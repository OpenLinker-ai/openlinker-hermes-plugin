from __future__ import annotations

import pytest

from openlinker import runtime

from hermes_openlinker.adapter import run_hermes_turn
from hermes_openlinker.config import OpenLinkerHermesConfig


class FakeCtx:
    def __init__(self):
        self.calls = []

    def dispatch_tool(self, name, args):
        self.calls.append((name, args))
        return {"text": f"delegated: {args['goal']}"}


def native_run(text: str = "hello") -> runtime.NativeRun:
    assignment = runtime.RuntimeAssignment(
        run_id="run-1",
        agent_id="agent-1",
        input={"text": text},
    )
    return runtime.NativeRun(
        assignment=assignment,
        reporter=runtime.NativeReporter(connector=None, run_id="run-1"),
    )


@pytest.mark.asyncio
async def test_echo_backend_returns_text():
    cfg = OpenLinkerHermesConfig(backend="echo", echo_backend_prefix="echo")
    result = await run_hermes_turn(None, native_run("ping"), cfg)
    assert result.text == "echo: ping"


@pytest.mark.asyncio
async def test_dispatch_tool_backend_uses_delegate_task_shape():
    ctx = FakeCtx()
    cfg = OpenLinkerHermesConfig(backend="dispatch_tool", dispatch_tool="delegate_task")
    result = await run_hermes_turn(ctx, native_run("write a haiku"), cfg)
    assert result.text == "delegated: write a haiku"
    assert ctx.calls[0][0] == "delegate_task"
    assert ctx.calls[0][1]["goal"] == "write a haiku"
    assert ctx.calls[0][1]["metadata"]["run_id"] == "run-1"

