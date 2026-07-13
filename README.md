# openlinker-hermes-plugin

Hermes Agent plugin for registering Hermes as an OpenLinker native runtime agent.

This plugin lets OpenLinker call a running Hermes Agent through OpenLinker's native runtime
protocol. Each OpenLinker runtime assignment is translated into one Hermes agent turn and the
Hermes response is returned as the OpenLinker run result.

The OpenLinker Python SDK is not published to PyPI for v0.1, so install it from the local
`openlinker-python` checkout before installing this plugin.

## Quick Start

Install the local SDK and plugin into the same Python environment used by Hermes:

```bash
python -m pip install -e /path/to/openlinker-python
python -m pip install -e /path/to/openlinker-hermes-plugin
```

Enable the pip entry-point plugin in Hermes:

```bash
hermes plugins enable openlinker
```

Register Hermes as an OpenLinker runtime agent:

```bash
hermes openlinker register --user-token "$OPENLINKER_USER_TOKEN"
```

Validate the persisted runtime token:

```bash
hermes openlinker status
```

See [INSTALL.md](INSTALL.md) for the full installation and operations guide.

## Configuration

By default, registration state is stored in:

```text
$HERMES_HOME/openlinker.env
```

If `HERMES_HOME` is not set, the plugin uses:

```text
~/.hermes/openlinker.env
```

Useful environment variables:

| Name | Default | Description |
| --- | --- | --- |
| `OPENLINKER_API_BASE` | `https://api.openlinker.ai` via SDK default | OpenLinker API base URL. |
| `OPENLINKER_RUNTIME_ENABLED` | `false` | Start the OpenLinker worker when Hermes loads the plugin. |
| `OPENLINKER_AUTO_REGISTER` | `true` | Register/reuse the runtime agent before worker start. |
| `OPENLINKER_USER_TOKEN` |  | Creator token used only for registration/token rotation. |
| `OPENLINKER_RUNTIME_TOKEN` |  | Runtime token used by worker/status. Usually persisted by `register`. |
| `OPENLINKER_REGISTRATION_ENV` | `$HERMES_HOME/openlinker.env` | Env file used for persisted registration state. |
| `OPENLINKER_WORKER_CONNECTOR` | `runtime_pull` | `runtime_pull` or `runtime_ws`. |
| `OPENLINKER_AGENT_SLUG` | `hermes-agent-local` | Agent slug for first registration. |
| `OPENLINKER_AGENT_NAME` | `Hermes Agent` | Agent display name for first registration. |
| `OPENLINKER_HERMES_BACKEND` | `hermes_agent` | `hermes_agent`, `dispatch_tool`, `hermes_cli`, `command`, or `echo`. |
| `OPENLINKER_HERMES_TOOLSETS` |  | Optional comma-separated Hermes toolsets enabled for the agent turn. |
| `OPENLINKER_HERMES_DISABLED_TOOLSETS` |  | Optional comma-separated Hermes toolsets disabled for the agent turn. |
| `OPENLINKER_HERMES_SYSTEM_MESSAGE` |  | Optional system message passed to the Hermes turn. |

The plugin does not override Hermes model/provider/base URL by default. Hermes model selection
comes from the normal Hermes configuration.

## Commands

The plugin registers:

```bash
hermes openlinker register
hermes openlinker status
hermes openlinker worker
```

The slash command `/openlinker` reports plugin status inside Hermes.

## Backend Modes

`hermes_agent` is the default route. It mirrors openlinker-agent-layout's runtime adapter:
each OpenLinker runtime assignment becomes one Hermes `AIAgent.run_conversation()` turn.
The plugin keeps in-memory message history by OpenLinker conversation/session id, then returns
the Hermes `final_response` as the OpenLinker native runtime result.

`dispatch_tool` uses Hermes' public `ctx.dispatch_tool()` API. It is kept for environments that
explicitly expose a compatible Hermes tool.

`hermes_cli` shells out to `hermes -z <prompt>`. It is a fallback when embedding `AIAgent`
directly is not available.

`command` shells out to `OPENLINKER_HERMES_TURN_COMMAND`. The command receives the request JSON on
stdin and in `OPENLINKER_HERMES_RUN`, then may return either plain text or JSON with a `text`,
`answer`, `output`, `content`, or `result` field.

`echo` is for local smoke tests only.
