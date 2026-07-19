from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from openlinker import registration

from .config import OpenLinkerHermesConfig
from .worker import (
    build_registration_request,
    load_stored_registration,
    run_worker,
)


def setup_cli(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="openlinker_command", required=True)

    register = sub.add_parser("register", help="Register or reuse the Hermes Agent")
    _add_common_openlinker_args(register)

    status = sub.add_parser("status", help="Show local OpenLinker configuration")
    _add_common_openlinker_args(status)

    worker = sub.add_parser("worker", help="Run the OpenLinker runtime worker")
    _add_common_openlinker_args(worker)
    worker.add_argument(
        "--backend",
        choices=["hermes_agent", "dispatch_tool", "hermes_cli", "command", "echo"],
        default=None,
    )


def run_cli(args: argparse.Namespace, ctx: Any = None) -> int:
    cfg = _cfg_from_args(args)
    return asyncio.run(_run_cli_async(args, cfg, ctx))


async def _run_cli_async(
    args: argparse.Namespace, cfg: OpenLinkerHermesConfig, ctx: Any
) -> int:
    command = args.openlinker_command
    if command == "register":
        registered = await registration.ensure_agent(build_registration_request(cfg))
        print(
            json.dumps(
                {
                    "agent_id": registered.agent_id,
                    "agent_slug": registered.agent_slug,
                    "agent_name": registered.agent_name,
                    "agent_token_saved": bool(registered.agent_token),
                    "token_prefix": registered.token_prefix,
                    "platform_url": registered.api_base,
                    "registration_env": cfg.env_path(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if command == "status":
        load_stored_registration(cfg)
        missing = cfg.runtime_missing()
        print(
            json.dumps(
                {
                    "registration_env": cfg.env_path(),
                    "agent_registered": bool(cfg.agent_id and cfg.agent_token),
                    "agent_id": cfg.agent_id,
                    "agent_token_present": bool(cfg.agent_token),
                    "platform_url": cfg.platform_url,
                    "runtime_url": cfg.runtime_url,
                    "node_id": cfg.node_id,
                    "transport": cfg.transport,
                    "runtime_ready": not missing and not cfg.migration_errors(),
                    "missing_runtime_config": missing,
                    "migration_errors": cfg.migration_errors(),
                    "note": "Local configuration only; no network validation was performed.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if command == "worker":
        await run_worker(ctx, cfg)
        return 0
    raise SystemExit(f"unknown openlinker command: {command}")


def _add_common_openlinker_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--url", dest="platform_url", default=None)
    parser.add_argument("--api-base", dest="platform_url", default=None)
    parser.add_argument("--runtime-url", default=None)
    parser.add_argument("--user-token", default=None)
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--agent-id", default=None)
    parser.add_argument("--agent-token", default=None)
    parser.add_argument("--transport", choices=["auto", "ws", "pull"], default=None)
    parser.add_argument("--mtls-cert-file", dest="runtime_mtls_cert_file", default=None)
    parser.add_argument("--mtls-key-file", dest="runtime_mtls_key_file", default=None)
    parser.add_argument("--mtls-ca-file", dest="runtime_mtls_ca_file", default=None)
    parser.add_argument("--data-dir", dest="runtime_data_dir", default=None)
    parser.add_argument("--agent-slug", default=None)
    parser.add_argument("--agent-name", default=None)
    parser.add_argument("--registration-env", default=None)
    parser.add_argument("--policy", default=None)


def _cfg_from_args(args: argparse.Namespace) -> OpenLinkerHermesConfig:
    cfg = OpenLinkerHermesConfig.from_env()
    for attr, target in [
        ("platform_url", "platform_url"),
        ("runtime_url", "runtime_url"),
        ("user_token", "user_token"),
        ("node_id", "node_id"),
        ("agent_id", "agent_id"),
        ("agent_token", "agent_token"),
        ("transport", "transport"),
        ("runtime_mtls_cert_file", "runtime_mtls_cert_file"),
        ("runtime_mtls_key_file", "runtime_mtls_key_file"),
        ("runtime_mtls_ca_file", "runtime_mtls_ca_file"),
        ("runtime_data_dir", "runtime_data_dir"),
        ("agent_slug", "agent_slug"),
        ("agent_name", "agent_name"),
        ("registration_env", "registration_env"),
        ("policy", "register_policy"),
        ("backend", "backend"),
    ]:
        if hasattr(args, attr):
            value = getattr(args, attr)
            if value is not None and value != "":
                setattr(cfg, target, value)
    return cfg
