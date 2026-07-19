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


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _list_env(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return default


def _runtime_transport() -> str:
    raw = _first_env(
        "OPENLINKER_RUNTIME_TRANSPORT",
        "OPENLINKER_WORKER_CONNECTOR",
        default="auto",
    ).lower()
    aliases = {
        "runtime_pull": "pull",
        "http": "pull",
        "runtime_ws": "ws",
        "websocket": "ws",
    }
    return aliases.get(raw, raw)


@dataclass
class OpenLinkerHermesConfig:
    platform_url: str = ""
    runtime_url: str = ""
    node_id: str = ""
    agent_id: str = ""
    agent_token: str = ""
    user_token: str = ""
    legacy_runtime_token: str = ""
    transport: str = "auto"
    runtime_mtls_cert_file: str = ""
    runtime_mtls_key_file: str = ""
    runtime_mtls_ca_file: str = ""
    runtime_mtls_server_name: str = ""
    runtime_data_dir: str = ""
    capacity: int = 1
    claim_wait_seconds: float = 25.0
    runtime_enabled: bool = False
    auto_register: bool = True
    register_policy: str = "reuse_existing"
    registration_env: str = field(default_factory=default_registration_env_path)
    agent_slug: str = "hermes-agent-local"
    agent_name: str = "Hermes Agent"
    agent_description: str = (
        "Hermes Agent runtime registered through openlinker-hermes-plugin."
    )
    agent_visibility: str = "private"
    agent_tags: list[str] = field(
        default_factory=lambda: ["agent", "runtime", "hermes"]
    )
    token_name: str = "Hermes Agent runtime"
    token_scopes: list[str] = field(
        default_factory=lambda: ["agent:pull", "agent:call"]
    )
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
            platform_url=_first_env("OPENLINKER_URL", "OPENLINKER_API_BASE"),
            runtime_url=os.getenv("OPENLINKER_RUNTIME_URL", "").strip(),
            node_id=os.getenv("OPENLINKER_NODE_ID", "").strip(),
            agent_id=os.getenv("OPENLINKER_AGENT_ID", "").strip(),
            agent_token=os.getenv("OPENLINKER_AGENT_TOKEN", "").strip(),
            user_token=os.getenv("OPENLINKER_USER_TOKEN", "").strip(),
            legacy_runtime_token=os.getenv("OPENLINKER_RUNTIME_TOKEN", "").strip(),
            transport=_runtime_transport(),
            runtime_mtls_cert_file=os.getenv(
                "OPENLINKER_RUNTIME_MTLS_CERT_FILE", ""
            ).strip(),
            runtime_mtls_key_file=os.getenv(
                "OPENLINKER_RUNTIME_MTLS_KEY_FILE", ""
            ).strip(),
            runtime_mtls_ca_file=os.getenv(
                "OPENLINKER_RUNTIME_MTLS_CA_FILE", ""
            ).strip(),
            runtime_mtls_server_name=os.getenv(
                "OPENLINKER_RUNTIME_MTLS_SERVER_NAME", ""
            ).strip(),
            runtime_data_dir=os.getenv(
                "OPENLINKER_RUNTIME_DATA_DIR",
                str(hermes_home() / "openlinker-runtime"),
            ).strip()
            or str(hermes_home() / "openlinker-runtime"),
            capacity=_int_env("OPENLINKER_RUNTIME_CAPACITY", 1),
            claim_wait_seconds=_float_env(
                "OPENLINKER_RUNTIME_CLAIM_WAIT_SECONDS", 25.0
            ),
            runtime_enabled=_bool_env("OPENLINKER_RUNTIME_ENABLED", False),
            auto_register=_bool_env("OPENLINKER_AUTO_REGISTER", True),
            register_policy=os.getenv(
                "OPENLINKER_REGISTER_POLICY", "reuse_existing"
            ).strip()
            or "reuse_existing",
            registration_env=os.getenv(
                "OPENLINKER_REGISTRATION_ENV", default_registration_env_path()
            ).strip()
            or default_registration_env_path(),
            agent_slug=os.getenv("OPENLINKER_AGENT_SLUG", "hermes-agent-local").strip()
            or "hermes-agent-local",
            agent_name=os.getenv("OPENLINKER_AGENT_NAME", "Hermes Agent").strip()
            or "Hermes Agent",
            agent_description=os.getenv(
                "OPENLINKER_AGENT_DESCRIPTION",
                "Hermes Agent runtime registered through openlinker-hermes-plugin.",
            ).strip(),
            agent_visibility=os.getenv("OPENLINKER_AGENT_VISIBILITY", "private").strip()
            or "private",
            agent_tags=_list_env("OPENLINKER_AGENT_TAGS")
            or ["agent", "runtime", "hermes"],
            token_name=_first_env(
                "OPENLINKER_AGENT_TOKEN_NAME",
                "OPENLINKER_RUNTIME_TOKEN_NAME",
                default="Hermes Agent runtime",
            ),
            token_scopes=(
                _list_env("OPENLINKER_AGENT_TOKEN_SCOPES")
                or _list_env("OPENLINKER_RUNTIME_TOKEN_SCOPES")
                or ["agent:pull", "agent:call"]
            ),
            backend=os.getenv("OPENLINKER_HERMES_BACKEND", "hermes_agent").strip()
            or "hermes_agent",
            hermes_system_message=os.getenv(
                "OPENLINKER_HERMES_SYSTEM_MESSAGE", ""
            ).strip(),
            hermes_max_iterations=_int_env("OPENLINKER_HERMES_MAX_ITERATIONS", 90),
            hermes_skip_memory=_bool_env("OPENLINKER_HERMES_SKIP_MEMORY", False),
            hermes_load_soul_identity=_bool_env(
                "OPENLINKER_HERMES_LOAD_SOUL_IDENTITY", False
            ),
            hermes_enabled_toolsets=_list_env("OPENLINKER_HERMES_TOOLSETS"),
            hermes_disabled_toolsets=_list_env("OPENLINKER_HERMES_DISABLED_TOOLSETS"),
            dispatch_tool=os.getenv(
                "OPENLINKER_HERMES_DISPATCH_TOOL", "delegate_task"
            ).strip()
            or "delegate_task",
            dispatch_toolsets=_list_env("OPENLINKER_HERMES_TOOLSETS"),
            dispatch_fallback_to_cli=_bool_env(
                "OPENLINKER_HERMES_DISPATCH_FALLBACK_TO_CLI", True
            ),
            hermes_cli_command=os.getenv("OPENLINKER_HERMES_CLI_COMMAND", "").strip(),
            hermes_cli_args=_list_env("OPENLINKER_HERMES_CLI_ARGS"),
            turn_command=os.getenv("OPENLINKER_HERMES_TURN_COMMAND", "").strip(),
            command_cwd=os.getenv("OPENLINKER_HERMES_COMMAND_CWD", "").strip(),
            echo_backend_prefix=os.getenv(
                "OPENLINKER_HERMES_ECHO_PREFIX", "Hermes OpenLinker echo"
            ).strip()
            or "Hermes OpenLinker echo",
        )

    def env_path(self) -> str:
        path = self.registration_env.strip()
        if not path:
            return default_registration_env_path()
        return str(Path(path).expanduser())

    def runtime_missing(self) -> list[str]:
        required = {
            "OPENLINKER_URL": self.platform_url,
            "OPENLINKER_NODE_ID": self.node_id,
            "OPENLINKER_AGENT_ID": self.agent_id,
            "OPENLINKER_AGENT_TOKEN": self.agent_token,
            "OPENLINKER_RUNTIME_MTLS_CERT_FILE": self.runtime_mtls_cert_file,
            "OPENLINKER_RUNTIME_MTLS_KEY_FILE": self.runtime_mtls_key_file,
            "OPENLINKER_RUNTIME_MTLS_CA_FILE": self.runtime_mtls_ca_file,
            "OPENLINKER_RUNTIME_DATA_DIR": self.runtime_data_dir,
        }
        return [name for name, value in required.items() if not value]

    def migration_errors(self) -> list[str]:
        errors: list[str] = []
        if self.legacy_runtime_token and not self.agent_token:
            errors.append(
                "OPENLINKER_RUNTIME_TOKEN is obsolete and cannot be used as an Agent Token. "
                "Register the Agent again to obtain OPENLINKER_AGENT_TOKEN."
            )
        if self.transport not in {"auto", "ws", "pull"}:
            errors.append(
                "OPENLINKER_RUNTIME_TRANSPORT must be auto, ws, or pull "
                "(runtime_ws and runtime_pull remain accepted aliases)."
            )
        return errors
