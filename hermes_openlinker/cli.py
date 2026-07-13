from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from openlinker import client, runtime

from .config import OpenLinkerHermesConfig
from .worker import build_registration_request, run_worker


def setup_cli(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="openlinker_command", required=True)

    register = sub.add_parser("register", help="Register or validate the Hermes runtime agent")
    _add_common_openlinker_args(register)

    status = sub.add_parser("status", help="Validate the OpenLinker runtime token")
    _add_common_openlinker_args(status)

    worker = sub.add_parser("worker", help="Run the OpenLinker runtime worker")
    _add_common_openlinker_args(worker)
    worker.add_argument("--backend", choices=["dispatch_tool", "command", "echo"], default=None)
    worker.add_argument("--max-runs", type=int, default=None)


def run_cli(args: argparse.Namespace, ctx: Any = None) -> int:
    cfg = _cfg_from_args(args)
    return asyncio.run(_run_cli_async(args, cfg, ctx))


async def _run_cli_async(args: argparse.Namespace, cfg: OpenLinkerHermesConfig, ctx: Any) -> int:
    command = args.openlinker_command
    if command == "register":
        reg = await runtime.ensure_runtime_agent(build_registration_request(cfg))
        print(json.dumps(reg.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if command == "status":
        if not cfg.runtime_token:
            stored = await runtime.EnvRegistrationStore(cfg.env_path()).load_runtime_agent_registration()
            if stored is not None:
                cfg.runtime_token = stored.runtime_token or ""
                cfg.api_base = cfg.api_base or (stored.api_base or "")
        async with client.Client(
            cfg.api_base or "https://api.openlinker.ai",
            runtime_token=cfg.runtime_token,
            sdk_agent="openlinker-hermes-plugin/cli",
        ) as sdk:
            heartbeat = await sdk.validate_runtime_token()
            print(json.dumps(heartbeat.to_dict(), ensure_ascii=False, indent=2))
            return 0
    if command == "worker":
        await run_worker(ctx, cfg)
        return 0
    raise SystemExit(f"unknown openlinker command: {command}")


def _add_common_openlinker_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-base", default=None)
    parser.add_argument("--user-token", default=None)
    parser.add_argument("--runtime-token", default=None)
    parser.add_argument("--connector", default=None)
    parser.add_argument("--agent-slug", default=None)
    parser.add_argument("--agent-name", default=None)
    parser.add_argument("--registration-env", default=None)
    parser.add_argument("--policy", default=None)


def _cfg_from_args(args: argparse.Namespace) -> OpenLinkerHermesConfig:
    cfg = OpenLinkerHermesConfig.from_env()
    for attr, target in [
        ("api_base", "api_base"),
        ("user_token", "user_token"),
        ("runtime_token", "runtime_token"),
        ("connector", "connector"),
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
    if hasattr(args, "max_runs") and args.max_runs is not None:
        cfg.max_runs = args.max_runs
    return cfg
