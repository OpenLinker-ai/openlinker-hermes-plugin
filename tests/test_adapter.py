from __future__ import annotations

import pytest

from hermes_openlinker.adapter import run_hermes_turn
from hermes_openlinker.config import OpenLinkerHermesConfig


class FakeCtx:
    def __init__(self):
        self.calls = []

    def dispatch_tool(self, name, args):
        self.calls.append((name, args))
        return {"text": f"delegated: {args['goal']}"}


class FakeRun:
    def __init__(self, text: str = "hello", metadata=None):
        self.run_id = "run-1"
        self.agent_id = "agent-1"
        self.input = {"text": text}
        self.metadata = metadata or {}
        self.events = []

    async def emit(self, event_type, payload):
        self.events.append((event_type, payload))


def runtime_context(text: str = "hello", metadata=None) -> FakeRun:
    return FakeRun(text, metadata)


@pytest.mark.asyncio
async def test_echo_backend_returns_text():
    cfg = OpenLinkerHermesConfig(backend="echo", echo_backend_prefix="echo")
    result = await run_hermes_turn(None, runtime_context("ping"), cfg)
    assert result.text == "echo: ping"


@pytest.mark.asyncio
async def test_dispatch_tool_backend_uses_delegate_task_shape():
    ctx = FakeCtx()
    cfg = OpenLinkerHermesConfig(backend="dispatch_tool", dispatch_tool="delegate_task")
    result = await run_hermes_turn(ctx, runtime_context("write a haiku"), cfg)
    assert result.text == "delegated: write a haiku"
    assert ctx.calls[0][0] == "delegate_task"
    assert ctx.calls[0][1]["goal"] == "write a haiku"
    assert ctx.calls[0][1]["metadata"]["run_id"] == "run-1"


@pytest.mark.asyncio
async def test_session_metadata_is_forwarded_to_dispatch_tool():
    ctx = FakeCtx()
    cfg = OpenLinkerHermesConfig(backend="dispatch_tool")
    run = runtime_context(
        "continue",
        {"conversation": {"session_key": "conversation-7"}},
    )

    await run_hermes_turn(ctx, run, cfg)

    assignment = ctx.calls[0][1]["metadata"]["assignment"]
    assert assignment["metadata"]["conversation"]["session_key"] == "conversation-7"
