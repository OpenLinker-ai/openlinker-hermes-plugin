from __future__ import annotations

import asyncio
import inspect
import json
import os
import shutil
from dataclasses import dataclass
import threading
from typing import Any

from openlinker import runtime

from .config import OpenLinkerHermesConfig


@dataclass
class HermesTurnResult:
    text: str
    raw: Any = None


_session_lock = threading.Lock()
_session_messages: dict[str, list[dict[str, Any]]] = {}


async def run_hermes_turn(
    ctx: Any,
    run: runtime.RuntimeContext,
    cfg: OpenLinkerHermesConfig,
) -> HermesTurnResult:
    text = _input_text(run.input) or "hello"
    backend = cfg.backend.strip().lower()
    if backend == "hermes_agent":
        return await _hermes_agent_turn(run, cfg, text)
    if backend == "dispatch_tool":
        return await _dispatch_tool_turn(ctx, run, cfg, text)
    if backend == "hermes_cli":
        return await _hermes_cli_turn(run, cfg, text)
    if backend == "command":
        return await _command_turn(run, cfg, text)
    if backend == "echo":
        return HermesTurnResult(
            text=f"{cfg.echo_backend_prefix}: {text}", raw={"backend": "echo"}
        )
    raise RuntimeError(
        "openlinker-hermes-plugin: unsupported OPENLINKER_HERMES_BACKEND "
        f"{cfg.backend!r}; use hermes_agent, dispatch_tool, hermes_cli, command, or echo"
    )


async def _hermes_agent_turn(
    run: runtime.RuntimeContext,
    cfg: OpenLinkerHermesConfig,
    text: str,
) -> HermesTurnResult:
    session_id = _session_id_from_run(run)

    def invoke() -> HermesTurnResult:
        from run_agent import AIAgent

        with _session_lock:
            history = [dict(item) for item in _session_messages.get(session_id, [])]

        agent_kwargs: dict[str, Any] = {
            "quiet_mode": True,
            "skip_memory": cfg.hermes_skip_memory,
            "load_soul_identity": cfg.hermes_load_soul_identity,
            "max_iterations": cfg.hermes_max_iterations,
        }
        if cfg.hermes_enabled_toolsets:
            agent_kwargs["enabled_toolsets"] = cfg.hermes_enabled_toolsets
        if cfg.hermes_disabled_toolsets:
            agent_kwargs["disabled_toolsets"] = cfg.hermes_disabled_toolsets

        signature = inspect.signature(AIAgent)
        if not any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in signature.parameters.values()
        ):
            agent_kwargs = {
                key: value
                for key, value in agent_kwargs.items()
                if key in signature.parameters
            }
        agent = AIAgent(**agent_kwargs)
        result = agent.run_conversation(
            user_message=text,
            conversation_history=history,
            system_message=cfg.hermes_system_message or None,
            task_id=session_id,
        )
        answer = _extract_text(result)
        messages = result.get("messages") if isinstance(result, dict) else None
        if isinstance(messages, list):
            with _session_lock:
                _session_messages[session_id] = [
                    dict(item) for item in messages if isinstance(item, dict)
                ]
        return HermesTurnResult(
            text=answer,
            raw={
                "backend": "hermes_agent",
                "session_id": session_id,
                "message_count": len(messages) if isinstance(messages, list) else 0,
            },
        )

    return await asyncio.to_thread(invoke)


async def _dispatch_tool_turn(
    ctx: Any,
    run: runtime.RuntimeContext,
    cfg: OpenLinkerHermesConfig,
    text: str,
) -> HermesTurnResult:
    if ctx is None or not hasattr(ctx, "dispatch_tool"):
        raise RuntimeError(
            "openlinker-hermes-plugin: dispatch_tool backend requires Hermes plugin ctx.dispatch_tool"
        )
    args: dict[str, Any] = {
        "goal": text,
        "input": text,
        "metadata": {
            "source": "openlinker",
            "run_id": run.run_id,
            "agent_id": run.agent_id,
            "assignment": _assignment_payload(run),
        },
    }
    if cfg.dispatch_toolsets:
        args["toolsets"] = cfg.dispatch_toolsets
    result = ctx.dispatch_tool(cfg.dispatch_tool, args)
    if hasattr(result, "__await__"):
        result = await result
    if cfg.dispatch_fallback_to_cli and _is_unknown_tool(result, cfg.dispatch_tool):
        return await _hermes_cli_turn(run, cfg, text)
    return HermesTurnResult(text=_extract_text(result), raw=result)


async def _hermes_cli_turn(
    run: runtime.RuntimeContext,
    cfg: OpenLinkerHermesConfig,
    text: str,
) -> HermesTurnResult:
    command = cfg.hermes_cli_command or _default_hermes_command()
    args = cfg.hermes_cli_args or ["-z"]
    proc = await asyncio.create_subprocess_exec(
        command,
        *args,
        text,
        cwd=cfg.command_cwd or None,
        env=dict(os.environ),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(
            "openlinker-hermes-plugin: hermes cli backend failed "
            f"with code {proc.returncode}: {stderr.decode(errors='replace').strip()}"
        )
    return HermesTurnResult(
        text=stdout.decode(errors="replace").strip(),
        raw={"backend": "hermes_cli", "command": command, "args": args},
    )


async def _command_turn(
    run: runtime.RuntimeContext,
    cfg: OpenLinkerHermesConfig,
    text: str,
) -> HermesTurnResult:
    if not cfg.turn_command:
        raise RuntimeError(
            "openlinker-hermes-plugin: command backend requires OPENLINKER_HERMES_TURN_COMMAND"
        )
    payload = {
        "text": text,
        "assignment": _assignment_payload(run),
    }
    env = dict(os.environ)
    env["OPENLINKER_HERMES_RUN"] = json.dumps(payload, ensure_ascii=False)
    proc = await asyncio.create_subprocess_shell(
        cfg.turn_command,
        cwd=cfg.command_cwd or None,
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(
        json.dumps(payload, ensure_ascii=False).encode()
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "openlinker-hermes-plugin: turn command failed "
            f"with code {proc.returncode}: {stderr.decode(errors='replace').strip()}"
        )
    raw_text = stdout.decode(errors="replace").strip()
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return HermesTurnResult(text=raw_text, raw=raw_text)
    return HermesTurnResult(text=_extract_text(parsed), raw=parsed)


def _default_hermes_command() -> str:
    return os.getenv("HERMES_BIN", "").strip() or shutil.which("hermes") or "hermes"


def _is_unknown_tool(value: Any, tool_name: str) -> bool:
    needle = f"unknown tool: {tool_name}".lower()
    if isinstance(value, str):
        return needle in value.lower()
    if isinstance(value, dict):
        error = value.get("error")
        if isinstance(error, str) and needle in error.lower():
            return True
    return False


def _session_id_from_run(run: runtime.RuntimeContext) -> str:
    for container_name in ("conversation", "a2a"):
        container = run.metadata.get(container_name)
        if not isinstance(container, dict):
            continue
        for key in (
            "session_key",
            "protocol_context_id",
            "root_context_id",
            "parent_context_id",
            "trace_id",
            "id",
        ):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in (
        "session_key",
        "protocol_context_id",
        "root_context_id",
        "parent_context_id",
        "trace_id",
    ):
        value = run.metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if run.run_id:
        return f"run-{run.run_id}"
    return "runtime-unknown"


def _input_text(value: dict[str, Any]) -> str:
    for key in ("text", "query", "task", "prompt"):
        item = value.get(key)
        if isinstance(item, str) and item.strip():
            return item.strip()
    return ""


def _assignment_payload(run: runtime.RuntimeContext) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "agent_id": run.agent_id,
        "input": dict(run.input),
        "metadata": dict(run.metadata),
    }


def _extract_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("final_response", "text", "answer", "output", "content", "result"):
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return item.strip()
            if isinstance(item, dict):
                nested = _extract_text(item)
                if nested:
                    return nested
        return json.dumps(value, ensure_ascii=False)
    text = str(value).strip()
    return text
