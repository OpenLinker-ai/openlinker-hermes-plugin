from __future__ import annotations

from typing import Any

from .config import OpenLinkerHermesConfig

try:
    from .cli import run_cli, setup_cli
    from .worker import current_worker, start_worker_background
except ModuleNotFoundError as exc:
    if exc.name == "openlinker":
        raise ModuleNotFoundError(
            "openlinker-hermes-plugin requires the local openlinker-python SDK. "
            "Install it into the same Python environment as Hermes first, for example: "
            "python -m pip install -e /path/to/openlinker-python"
        ) from exc
    raise


def register(ctx: Any) -> None:
    cfg = OpenLinkerHermesConfig.from_env()

    if hasattr(ctx, "register_cli_command"):
        ctx.register_cli_command(
            "openlinker",
            "Manage OpenLinker runtime integration",
            setup_cli,
            lambda args: run_cli(args, ctx),
        )

    if hasattr(ctx, "register_command"):
        ctx.register_command(
            "openlinker",
            lambda _argstr="": _slash_status(cfg),
            "Show OpenLinker Hermes plugin status",
        )

    if cfg.runtime_enabled:
        start_worker_background(ctx, cfg)


def _slash_status(cfg: OpenLinkerHermesConfig) -> str:
    worker = current_worker()
    running = bool(worker and worker.thread.is_alive())
    error = type(worker.error).__name__ if worker and worker.error else ""
    missing = cfg.runtime_missing()
    return (
        "OpenLinker Hermes plugin\n"
        f"- start worker with Hermes: {cfg.runtime_enabled}\n"
        f"- worker running: {running}\n"
        f"- connection: {cfg.transport}\n"
        f"- Agent: {cfg.agent_slug}\n"
        f"- Hermes backend: {cfg.backend}\n"
        f"- missing local settings: {', '.join(missing) if missing else 'none'}\n"
        f"- last worker error type: {error or 'none'}\n"
    )


__all__ = ["register"]
