from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from typing import Any

from openlinker import runtime

from .adapter import run_hermes_turn
from .config import OpenLinkerHermesConfig


@dataclass
class WorkerHandle:
    thread: threading.Thread
    stop_event: threading.Event


_worker_handle: WorkerHandle | None = None


def build_registration_request(cfg: OpenLinkerHermesConfig) -> runtime.EnsureRuntimeAgentRequest:
    return runtime.EnsureRuntimeAgentRequest(
        slug=cfg.agent_slug,
        name=cfg.agent_name,
        description=cfg.agent_description,
        tags=cfg.agent_tags,
        visibility=cfg.agent_visibility,
        connection_mode=cfg.connector,
        token_name=cfg.token_name,
        token_scopes=cfg.token_scopes,
        policy=cfg.register_policy,
        user_token=cfg.user_token,
        runtime_token=cfg.runtime_token,
        api_base=cfg.api_base,
        connector=cfg.connector,
        store=runtime.EnvRegistrationStore(cfg.env_path()),
    )


async def handle_openlinker_run(
    ctx: Any,
    cfg: OpenLinkerHermesConfig,
    run: runtime.NativeRun,
) -> runtime.NativeResult:
    await run.message_delta("Hermes received the OpenLinker request.")
    result = await run_hermes_turn(ctx, run, cfg)
    if not result.text:
        return runtime.NativeResult.failed(
            "HERMES_EMPTY_RESPONSE",
            "Hermes adapter returned an empty response.",
        )
    return runtime.NativeResult.success(
        {
            "text": result.text,
            "run_id": run.assignment.run_id,
            "agent_id": run.assignment.agent_id,
            "backend": cfg.backend,
            "raw": result.raw,
        },
        events=[
            runtime.AgentEvent(
                event_type=runtime.AGENT_EVENT_TYPE_RUN_MESSAGE_DELTA,
                payload={"text": result.text},
            )
        ],
    )


async def run_worker(ctx: Any, cfg: OpenLinkerHermesConfig) -> None:
    async def handler(run: runtime.NativeRun) -> runtime.NativeResult:
        return await handle_openlinker_run(ctx, cfg, run)

    runner = (
        runtime.Native(handler)
        .with_api_base(cfg.api_base)
        .with_runtime_token(cfg.runtime_token)
        .with_connector(cfg.connector)
        .with_pull_wait(cfg.pull_wait_seconds)
        .with_max_runs(cfg.max_runs)
        .with_sdk_agent("openlinker-hermes-plugin/runtime")
    )
    if cfg.auto_register:
        await runner.run_or_register(build_registration_request(cfg))
    else:
        await runner.run()


def start_worker_background(ctx: Any, cfg: OpenLinkerHermesConfig) -> WorkerHandle:
    global _worker_handle
    if _worker_handle is not None and _worker_handle.thread.is_alive():
        return _worker_handle
    stop_event = threading.Event()

    def target() -> None:
        asyncio.run(run_worker(ctx, cfg))
        stop_event.set()

    thread = threading.Thread(target=target, name="openlinker-hermes-runtime", daemon=True)
    thread.start()
    _worker_handle = WorkerHandle(thread=thread, stop_event=stop_event)
    return _worker_handle

def current_worker() -> WorkerHandle | None:
    return _worker_handle

