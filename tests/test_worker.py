from __future__ import annotations

import pytest
from openlinker import registration, runtime

from hermes_openlinker.config import OpenLinkerHermesConfig
from hermes_openlinker.worker import (
    build_registration_request,
    build_runtime_worker,
    handle_openlinker_run,
)


class FakeRuntimeContext:
    run_id = "run-1"
    agent_id = "agent-1"
    input = {"text": "hello"}
    metadata = {}

    def __init__(self):
        self.emitted = []

    async def emit(self, event_type, payload):
        self.emitted.append((event_type, payload))


def test_build_registration_request_uses_runtime_sdk_types(tmp_path):
    cfg = OpenLinkerHermesConfig(
        platform_url="https://api.example.test",
        user_token="user-token",
        agent_token="ol_agent_test",
        transport="pull",
        registration_env=str(tmp_path / "runtime.env"),
        agent_slug="hermes-local",
        agent_name="Hermes Local",
    )
    req = build_registration_request(cfg)
    assert isinstance(req, registration.EnsureAgentRequest)
    assert req.slug == "hermes-local"
    assert req.name == "Hermes Local"
    assert req.connection_mode == "runtime"
    assert req.agent_token == "ol_agent_test"
    assert isinstance(req.store, registration.EnvRegistrationStore)


def test_build_runtime_worker_uses_current_sdk(tmp_path):
    cfg = OpenLinkerHermesConfig(
        platform_url="https://platform.example.test",
        node_id="11111111-1111-4111-8111-111111111111",
        agent_id="22222222-2222-4222-8222-222222222222",
        agent_token="ol_agent_test",
        runtime_mtls_cert_file="client.crt",
        runtime_mtls_key_file="client.key",
        runtime_mtls_ca_file="ca.crt",
        runtime_data_dir=str(tmp_path / "runtime"),
        transport="pull",
    )

    worker = build_runtime_worker(None, cfg)

    assert isinstance(worker, runtime.RuntimeWorker)
    assert worker.node_id == cfg.node_id
    assert worker.agent_id == cfg.agent_id
    assert worker.transport_mode == "pull"


@pytest.mark.asyncio
async def test_handler_returns_supported_message_event():
    context = FakeRuntimeContext()
    cfg = OpenLinkerHermesConfig(backend="echo", echo_backend_prefix="Hermes")

    result = await handle_openlinker_run(None, cfg, context)

    assert result.status == "success"
    assert result.output["text"] == "Hermes: hello"
    assert result.events[0].event_type == "run.message.delta"
    assert context.emitted[0][0] == "run.progress"
