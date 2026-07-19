from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from typing import Any

from openlinker import registration, runtime

from .adapter import run_hermes_turn
from .config import OpenLinkerHermesConfig


@dataclass
class WorkerHandle:
    thread: threading.Thread
    stop_event: threading.Event
    error: BaseException | None = None


_worker_handle: WorkerHandle | None = None


def build_registration_request(
    cfg: OpenLinkerHermesConfig,
) -> registration.EnsureAgentRequest:
    return registration.EnsureAgentRequest(
        slug=cfg.agent_slug,
        name=cfg.agent_name,
        description=cfg.agent_description,
        tags=cfg.agent_tags,
        visibility=cfg.agent_visibility,
        connection_mode="runtime",
        token_name=cfg.token_name,
        token_scopes=cfg.token_scopes,
        policy=cfg.register_policy,
        user_token=cfg.user_token,
        agent_token=cfg.agent_token,
        api_base=cfg.platform_url,
        store=registration.EnvRegistrationStore(cfg.env_path()),
    )


async def handle_openlinker_run(
    ctx: Any,
    cfg: OpenLinkerHermesConfig,
    run: runtime.RuntimeContext,
) -> runtime.RuntimeResult:
    await run.emit(
        "run.progress",
        {"stage": "received", "adapter": "openlinker-hermes-plugin"},
    )
    result = await run_hermes_turn(ctx, run, cfg)
    if not result.text:
        return runtime.RuntimeResult.failed(
            "HERMES_EMPTY_RESPONSE",
            "Hermes adapter returned an empty response.",
        )
    return runtime.RuntimeResult.success(
        {
            "text": result.text,
            "run_id": run.run_id,
            "agent_id": run.agent_id,
            "backend": cfg.backend,
            "raw": result.raw,
        },
        events=(
            runtime.RuntimeEvent(
                event_type="run.message.delta",
                payload={"text": result.text},
            ),
        ),
    )


async def run_worker(ctx: Any, cfg: OpenLinkerHermesConfig) -> None:
    migration_errors = cfg.migration_errors()
    if migration_errors:
        raise ValueError(" ".join(migration_errors))

    if cfg.auto_register:
        registered = await registration.ensure_agent(build_registration_request(cfg))
        _apply_registration(cfg, registered)
    else:
        load_stored_registration(cfg)

    missing = cfg.runtime_missing()
    if missing:
        raise ValueError(
            "OpenLinker Runtime worker configuration is incomplete. Missing: "
            + ", ".join(missing)
            + ". Agent registration does not create a Runtime Node or its mTLS files."
        )

    worker = build_runtime_worker(ctx, cfg)
    await worker.run()


def build_runtime_worker(
    ctx: Any,
    cfg: OpenLinkerHermesConfig,
) -> runtime.RuntimeWorker:
    async def handler(run: runtime.RuntimeContext) -> runtime.RuntimeResult:
        return await handle_openlinker_run(ctx, cfg, run)

    return runtime.RuntimeWorker(
        platform_url=cfg.platform_url,
        runtime_url=cfg.runtime_url,
        node_id=cfg.node_id,
        node_version="openlinker-hermes-plugin/runtime",
        agent_id=cfg.agent_id,
        agent_token=cfg.agent_token,
        mtls=runtime.RuntimeMTLS(
            cert_file=cfg.runtime_mtls_cert_file,
            key_file=cfg.runtime_mtls_key_file,
            ca_file=cfg.runtime_mtls_ca_file,
            server_name=cfg.runtime_mtls_server_name,
        ),
        data_dir=cfg.runtime_data_dir,
        transport=cfg.transport,
        capacity=cfg.capacity,
        claim_wait=cfg.claim_wait_seconds,
        handler=handler,
    )


def load_stored_registration(cfg: OpenLinkerHermesConfig) -> None:
    stored = registration.EnvRegistrationStore(cfg.env_path()).load_agent_registration()
    if stored is not None:
        _apply_registration(cfg, stored)


def _apply_registration(
    cfg: OpenLinkerHermesConfig,
    registered: registration.AgentRegistration,
) -> None:
    cfg.agent_id = cfg.agent_id or registered.agent_id
    cfg.agent_token = cfg.agent_token or registered.agent_token
    cfg.platform_url = cfg.platform_url or registered.api_base


def start_worker_background(ctx: Any, cfg: OpenLinkerHermesConfig) -> WorkerHandle:
    global _worker_handle
    if _worker_handle is not None and _worker_handle.thread.is_alive():
        return _worker_handle
    stop_event = threading.Event()

    handle = WorkerHandle(
        thread=threading.Thread(),
        stop_event=stop_event,
    )

    def target() -> None:
        try:
            asyncio.run(run_worker(ctx, cfg))
        except BaseException as exc:
            handle.error = exc
        finally:
            stop_event.set()

    thread = threading.Thread(
        target=target, name="openlinker-hermes-runtime", daemon=True
    )
    handle.thread = thread
    thread.start()
    _worker_handle = handle
    return _worker_handle


def current_worker() -> WorkerHandle | None:
    return _worker_handle
