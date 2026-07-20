from __future__ import annotations

import argparse

import hermes_openlinker
import pytest
from hermes_openlinker.cli import _run_cli_async
from hermes_openlinker.config import OpenLinkerHermesConfig


class FakeCtx:
    def __init__(self):
        self.cli_commands = {}
        self.commands = {}

    def register_cli_command(
        self, name, help, setup_fn, handler_fn=None, description=""
    ):
        self.cli_commands[name] = {
            "help": help,
            "setup_fn": setup_fn,
            "handler_fn": handler_fn,
            "description": description,
        }

    def register_command(self, name, handler, description="", args_hint=""):
        self.commands[name] = {
            "handler": handler,
            "description": description,
            "args_hint": args_hint,
        }


def test_register_adds_cli_and_slash_command_without_autostart(monkeypatch):
    monkeypatch.setenv("OPENLINKER_RUNTIME_ENABLED", "false")
    ctx = FakeCtx()
    hermes_openlinker.register(ctx)
    assert "openlinker" in ctx.cli_commands
    assert "openlinker" in ctx.commands
    status = ctx.commands["openlinker"]["handler"]("")
    assert "worker running: False" in status
    assert "Agent Token" not in status


def test_cli_setup_has_expected_subcommands():
    ctx = FakeCtx()
    hermes_openlinker.register(ctx)
    parser = argparse.ArgumentParser()
    ctx.cli_commands["openlinker"]["setup_fn"](parser)
    parsed = parser.parse_args(["status"])
    assert parsed.openlinker_command == "status"


def test_cli_setup_accepts_all_existing_backends():
    ctx = FakeCtx()
    hermes_openlinker.register(ctx)
    parser = argparse.ArgumentParser()
    ctx.cli_commands["openlinker"]["setup_fn"](parser)

    for backend in ("hermes_agent", "dispatch_tool", "hermes_cli", "command", "echo"):
        parsed = parser.parse_args(["worker", "--backend", backend])
        assert parsed.backend == backend


@pytest.mark.asyncio
async def test_status_reports_local_config_without_secrets(tmp_path, capsys):
    cfg = OpenLinkerHermesConfig(
        platform_url="https://platform.example.test",
        node_id="node-1",
        agent_id="agent-1",
        agent_token="ol_agent_do_not_print",
        runtime_mtls_cert_file="client.crt",
        runtime_mtls_key_file="private.key",
        runtime_mtls_ca_file="ca.crt",
        runtime_data_dir=str(tmp_path / "runtime"),
        registration_env=str(tmp_path / "missing.env"),
    )

    result = await _run_cli_async(
        argparse.Namespace(openlinker_command="status"),
        cfg,
        None,
    )

    output = capsys.readouterr().out
    assert result == 0
    assert '"runtime_ready": true' in output
    assert "ol_agent_do_not_print" not in output
    assert "private.key" not in output
    assert "no network validation was performed" in output
