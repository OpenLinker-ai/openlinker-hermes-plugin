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
    return (
        "OpenLinker Hermes plugin\n"
        f"- runtime_enabled: {cfg.runtime_enabled}\n"
        f"- worker_running: {running}\n"
        f"- connector: {cfg.connector}\n"
        f"- agent_slug: {cfg.agent_slug}\n"
        f"- backend: {cfg.backend}\n"
    )


__all__ = ["register"]
