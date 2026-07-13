from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path

_ENV_FILES_LOADED = False


def hermes_home() -> Path:
    return Path(os.getenv("HERMES_HOME", "~/.hermes")).expanduser()


def default_registration_env_path() -> str:
    return str(hermes_home() / "openlinker.env")


def _env_file_candidates() -> list[Path]:
    explicit = os.getenv("OPENLINKER_HERMES_ENV", "").strip()
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    registration_env = os.getenv("OPENLINKER_REGISTRATION_ENV", "").strip()
    if registration_env:
        candidates.append(Path(registration_env).expanduser())
    candidates.append(Path(default_registration_env_path()))
    return candidates


def _parse_env_value(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ""
    try:
        parsed = shlex.split(raw, comments=False, posix=True)
    except ValueError:
        return raw.strip("\"'")
    if len(parsed) == 1:
        return parsed[0]
    return raw.strip("\"'")


def _load_env_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[7:].strip()
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = _parse_env_value(value)


def load_config_env_files() -> None:
    global _ENV_FILES_LOADED
    if _ENV_FILES_LOADED:
        return
    _ENV_FILES_LOADED = True
    seen: set[Path] = set()
    for candidate in _env_file_candidates():
        resolved = candidate.expanduser()
        if resolved in seen:
            continue
        seen.add(resolved)
        _load_env_file(resolved)


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int = 0) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _list_env(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass
class OpenLinkerHermesConfig:
    api_base: str = ""
    user_token: str = ""
    runtime_token: str = ""
    connector: str = "runtime_pull"
    max_runs: int = 0
    pull_wait_seconds: float = 25.0
    runtime_enabled: bool = False
    auto_register: bool = True
    register_policy: str = "reuse_existing"
    registration_env: str = field(default_factory=default_registration_env_path)
    agent_slug: str = "hermes-agent-local"
    agent_name: str = "Hermes Agent"
    agent_description: str = "Hermes Agent runtime registered through openlinker-hermes-plugin."
    agent_visibility: str = "private"
    agent_tags: list[str] = field(default_factory=lambda: ["agent", "runtime", "hermes"])
    token_name: str = "hermes-agent runtime"
    token_scopes: list[str] = field(default_factory=lambda: ["agent:pull", "agent:call"])
    backend: str = "hermes_agent"
    hermes_system_message: str = ""
    hermes_max_iterations: int = 90
    hermes_skip_memory: bool = False
    hermes_load_soul_identity: bool = False
    hermes_enabled_toolsets: list[str] = field(default_factory=list)
    hermes_disabled_toolsets: list[str] = field(default_factory=list)
    dispatch_tool: str = "delegate_task"
    dispatch_toolsets: list[str] = field(default_factory=list)
    dispatch_fallback_to_cli: bool = True
    hermes_cli_command: str = ""
    hermes_cli_args: list[str] = field(default_factory=list)
    turn_command: str = ""
    command_cwd: str = ""
    echo_backend_prefix: str = "Hermes OpenLinker echo"

    @classmethod
    def from_env(cls) -> "OpenLinkerHermesConfig":
        load_config_env_files()
        return cls(
            api_base=os.getenv("OPENLINKER_API_BASE", "").strip(),
            user_token=os.getenv("OPENLINKER_USER_TOKEN", "").strip(),
            runtime_token=os.getenv("OPENLINKER_RUNTIME_TOKEN", "").strip(),
            connector=os.getenv("OPENLINKER_WORKER_CONNECTOR", "runtime_pull").strip() or "runtime_pull",
            max_runs=_int_env("OPENLINKER_WORKER_MAX_RUNS", 0),
            pull_wait_seconds=float(os.getenv("OPENLINKER_WORKER_PULL_WAIT_SECONDS", "25") or "25"),
            runtime_enabled=_bool_env("OPENLINKER_RUNTIME_ENABLED", False),
            auto_register=_bool_env("OPENLINKER_AUTO_REGISTER", True),
            register_policy=os.getenv("OPENLINKER_REGISTER_POLICY", "reuse_existing").strip()
            or "reuse_existing",
            registration_env=os.getenv(
                "OPENLINKER_REGISTRATION_ENV", default_registration_env_path()
            ).strip()
            or default_registration_env_path(),
            agent_slug=os.getenv("OPENLINKER_AGENT_SLUG", "hermes-agent-local").strip()
            or "hermes-agent-local",
            agent_name=os.getenv("OPENLINKER_AGENT_NAME", "Hermes Agent").strip() or "Hermes Agent",
            agent_description=os.getenv(
                "OPENLINKER_AGENT_DESCRIPTION",
                "Hermes Agent runtime registered through openlinker-hermes-plugin.",
            ).strip(),
            agent_visibility=os.getenv("OPENLINKER_AGENT_VISIBILITY", "private").strip() or "private",
            agent_tags=_list_env("OPENLINKER_AGENT_TAGS") or ["agent", "runtime", "hermes"],
            token_name=os.getenv("OPENLINKER_RUNTIME_TOKEN_NAME", "hermes-agent runtime").strip()
            or "hermes-agent runtime",
            token_scopes=_list_env("OPENLINKER_RUNTIME_TOKEN_SCOPES") or ["agent:pull", "agent:call"],
            backend=os.getenv("OPENLINKER_HERMES_BACKEND", "hermes_agent").strip()
            or "hermes_agent",
            hermes_system_message=os.getenv("OPENLINKER_HERMES_SYSTEM_MESSAGE", "").strip(),
            hermes_max_iterations=_int_env("OPENLINKER_HERMES_MAX_ITERATIONS", 90),
            hermes_skip_memory=_bool_env("OPENLINKER_HERMES_SKIP_MEMORY", False),
            hermes_load_soul_identity=_bool_env("OPENLINKER_HERMES_LOAD_SOUL_IDENTITY", False),
            hermes_enabled_toolsets=_list_env("OPENLINKER_HERMES_TOOLSETS"),
            hermes_disabled_toolsets=_list_env("OPENLINKER_HERMES_DISABLED_TOOLSETS"),
            dispatch_tool=os.getenv("OPENLINKER_HERMES_DISPATCH_TOOL", "delegate_task").strip()
            or "delegate_task",
            dispatch_toolsets=_list_env("OPENLINKER_HERMES_TOOLSETS"),
            dispatch_fallback_to_cli=_bool_env("OPENLINKER_HERMES_DISPATCH_FALLBACK_TO_CLI", True),
            hermes_cli_command=os.getenv("OPENLINKER_HERMES_CLI_COMMAND", "").strip(),
            hermes_cli_args=_list_env("OPENLINKER_HERMES_CLI_ARGS"),
            turn_command=os.getenv("OPENLINKER_HERMES_TURN_COMMAND", "").strip(),
            command_cwd=os.getenv("OPENLINKER_HERMES_COMMAND_CWD", "").strip(),
            echo_backend_prefix=os.getenv("OPENLINKER_HERMES_ECHO_PREFIX", "Hermes OpenLinker echo").strip()
            or "Hermes OpenLinker echo",
        )

    def env_path(self) -> str:
        path = self.registration_env.strip()
        if not path:
            return default_registration_env_path()
        return str(Path(path).expanduser())
