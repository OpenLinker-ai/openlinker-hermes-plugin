from __future__ import annotations

import argparse

import hermes_openlinker


class FakeCtx:
    def __init__(self):
        self.cli_commands = {}
        self.commands = {}

    def register_cli_command(self, name, help, setup_fn, handler_fn=None, description=""):
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
    assert "worker_running: False" in ctx.commands["openlinker"]["handler"]("")


def test_cli_setup_has_expected_subcommands():
    ctx = FakeCtx()
    hermes_openlinker.register(ctx)
    parser = argparse.ArgumentParser()
    ctx.cli_commands["openlinker"]["setup_fn"](parser)
    parsed = parser.parse_args(["status"])
    assert parsed.openlinker_command == "status"

