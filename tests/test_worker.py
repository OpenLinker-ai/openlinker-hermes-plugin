from __future__ import annotations

from openlinker import runtime

from hermes_openlinker.config import OpenLinkerHermesConfig
from hermes_openlinker.worker import build_registration_request


def test_build_registration_request_uses_runtime_sdk_types(tmp_path):
    cfg = OpenLinkerHermesConfig(
        api_base="https://api.example.test",
        user_token="user-token",
        runtime_token="runtime-token",
        connector="runtime_pull",
        registration_env=str(tmp_path / "runtime.env"),
        agent_slug="hermes-local",
        agent_name="Hermes Local",
    )
    req = build_registration_request(cfg)
    assert isinstance(req, runtime.EnsureRuntimeAgentRequest)
    assert req.slug == "hermes-local"
    assert req.name == "Hermes Local"
    assert isinstance(req.store, runtime.EnvRegistrationStore)

