from __future__ import annotations

from pathlib import Path

from hermes_openlinker.config import OpenLinkerHermesConfig
import hermes_openlinker.config as config_module


def test_from_env_loads_explicit_config_file(monkeypatch, tmp_path):
    env_path = tmp_path / "openlinker.env"
    env_path.write_text(
        "\n".join(
            [
                "OPENLINKER_RUNTIME_ENABLED=true",
                "OPENLINKER_AGENT_SLUG=hermes-from-file",
                'OPENLINKER_AGENT_NAME="Hermes From File"',
                "OPENLINKER_RUNTIME_TOKEN=file-token",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENLINKER_HERMES_ENV", str(env_path))
    monkeypatch.delenv("OPENLINKER_RUNTIME_ENABLED", raising=False)
    monkeypatch.delenv("OPENLINKER_AGENT_SLUG", raising=False)
    monkeypatch.delenv("OPENLINKER_AGENT_NAME", raising=False)
    monkeypatch.delenv("OPENLINKER_RUNTIME_TOKEN", raising=False)
    monkeypatch.setattr(config_module, "_ENV_FILES_LOADED", False)

    cfg = OpenLinkerHermesConfig.from_env()

    assert cfg.runtime_enabled is True
    assert cfg.agent_slug == "hermes-from-file"
    assert cfg.agent_name == "Hermes From File"
    assert cfg.legacy_runtime_token == "file-token"
    assert "cannot be used as an Agent Token" in cfg.migration_errors()[0]


def test_environment_overrides_config_file(monkeypatch, tmp_path):
    env_path = Path(tmp_path) / "openlinker.env"
    env_path.write_text("OPENLINKER_RUNTIME_ENABLED=false\n", encoding="utf-8")
    monkeypatch.setenv("OPENLINKER_HERMES_ENV", str(env_path))
    monkeypatch.setenv("OPENLINKER_RUNTIME_ENABLED", "true")
    monkeypatch.setattr(config_module, "_ENV_FILES_LOADED", False)

    assert OpenLinkerHermesConfig.from_env().runtime_enabled is True


def test_default_registration_env_uses_hermes_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes-home"))
    monkeypatch.delenv("OPENLINKER_REGISTRATION_ENV", raising=False)
    monkeypatch.delenv("OPENLINKER_HERMES_ENV", raising=False)
    monkeypatch.setattr(config_module, "_ENV_FILES_LOADED", False)

    cfg = OpenLinkerHermesConfig.from_env()

    assert cfg.registration_env == str(tmp_path / "hermes-home" / "openlinker.env")


def test_canonical_runtime_config_and_legacy_transport_alias(monkeypatch):
    monkeypatch.setenv("OPENLINKER_URL", "https://platform.example.test")
    monkeypatch.setenv("OPENLINKER_API_BASE", "https://old.example.test")
    monkeypatch.setenv("OPENLINKER_RUNTIME_TRANSPORT", "runtime_ws")
    monkeypatch.setenv("OPENLINKER_AGENT_TOKEN", "ol_agent_secret")
    monkeypatch.setenv("OPENLINKER_RUNTIME_TOKEN", "old-runtime-secret")
    monkeypatch.setattr(config_module, "_ENV_FILES_LOADED", False)

    cfg = OpenLinkerHermesConfig.from_env()

    assert cfg.platform_url == "https://platform.example.test"
    assert cfg.transport == "ws"
    assert cfg.agent_token == "ol_agent_secret"
    assert cfg.migration_errors() == []


def test_runtime_pull_alias_maps_to_current_sdk_transport(monkeypatch):
    monkeypatch.setenv("OPENLINKER_WORKER_CONNECTOR", "runtime_pull")
    monkeypatch.delenv("OPENLINKER_RUNTIME_TRANSPORT", raising=False)
    monkeypatch.setattr(config_module, "_ENV_FILES_LOADED", False)

    assert OpenLinkerHermesConfig.from_env().transport == "pull"
