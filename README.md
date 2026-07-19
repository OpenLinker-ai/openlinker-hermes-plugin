# openlinker-hermes-plugin

[简体中文](README.zh-CN.md)

This plugin lets OpenLinker send work to Hermes Agent. It receives an OpenLinker Runtime
assignment, runs one Hermes turn, and returns the answer to OpenLinker.

The plugin supports five ways to run Hermes:

- `hermes_agent`: call Hermes `AIAgent` directly. This is the default.
- `dispatch_tool`: call a Hermes tool such as `delegate_task`.
- `hermes_cli`: run `hermes -z <prompt>`.
- `command`: run a command chosen by the operator.
- `echo`: return the input for local smoke tests.

## Before you start

You need two separate sets of credentials:

1. **Agent registration**: an Agent ID and Agent Token. The plugin can create or reuse these
   when you run `hermes openlinker register`.
2. **Runtime Node connection**: a Node ID and three mTLS files (client certificate, private key,
   and CA certificate). An OpenLinker administrator must create the Runtime Node and give these
   values to the machine running Hermes.

Registering an Agent does not create a Runtime Node or its mTLS files.

The OpenLinker Python SDK is not published to PyPI for v0.1. Install it from a local checkout
before installing this plugin.

## Quick start

Install the SDK and plugin into the Python environment used by Hermes:

```bash
python -m pip install -e /path/to/openlinker-python
python -m pip install -e /path/to/openlinker-hermes-plugin
hermes plugins enable openlinker
```

Register or reuse the Hermes Agent:

```bash
export OPENLINKER_URL="https://api.openlinker.ai"
export OPENLINKER_USER_TOKEN="ol_user_..."
hermes openlinker register
```

The command saves the Agent ID and Agent Token to:

```text
$HERMES_HOME/openlinker.env
```

If `HERMES_HOME` is not set, the file is `~/.hermes/openlinker.env`.

Next, add the Runtime Node values supplied by your administrator:

```bash
export OPENLINKER_NODE_ID="..."
export OPENLINKER_RUNTIME_MTLS_CERT_FILE="/secure/path/client.crt"
export OPENLINKER_RUNTIME_MTLS_KEY_FILE="/secure/path/client.key"
export OPENLINKER_RUNTIME_MTLS_CA_FILE="/secure/path/ca.crt"
export OPENLINKER_RUNTIME_DATA_DIR="$HERMES_HOME/openlinker-runtime"
```

Check the local configuration, then start the worker:

```bash
hermes openlinker status
hermes openlinker worker
```

`status` does not contact OpenLinker. It reports what is configured locally and which settings
are still missing.

See [INSTALL.md](INSTALL.md) for the full setup and migration guide.

## Main settings

| Name | Default | What it does |
| --- | --- | --- |
| `OPENLINKER_URL` | none | Public OpenLinker platform URL. |
| `OPENLINKER_RUNTIME_URL` | discovered from the platform | Optional dedicated Runtime URL. |
| `OPENLINKER_USER_TOKEN` | none | Used only to create, validate, or rotate Agent registration. |
| `OPENLINKER_AGENT_ID` | saved by `register` | Agent that receives the work. |
| `OPENLINKER_AGENT_TOKEN` | saved by `register` | Agent credential used by the worker. |
| `OPENLINKER_NODE_ID` | none | Runtime Node assigned to this machine. |
| `OPENLINKER_RUNTIME_MTLS_CERT_FILE` | none | Runtime client certificate. |
| `OPENLINKER_RUNTIME_MTLS_KEY_FILE` | none | Runtime client private key. |
| `OPENLINKER_RUNTIME_MTLS_CA_FILE` | none | CA used to verify the Runtime service. |
| `OPENLINKER_RUNTIME_DATA_DIR` | `$HERMES_HOME/openlinker-runtime` | Durable local state used to resume work safely. |
| `OPENLINKER_RUNTIME_TRANSPORT` | `auto` | `auto`, `ws`, or `pull`. |
| `OPENLINKER_RUNTIME_ENABLED` | `false` | Start the worker automatically when Hermes loads the plugin. |
| `OPENLINKER_AUTO_REGISTER` | `true` | Reuse or create Agent registration before starting the worker. |
| `OPENLINKER_REGISTRATION_ENV` | `$HERMES_HOME/openlinker.env` | File that stores Agent registration. |
| `OPENLINKER_HERMES_BACKEND` | `hermes_agent` | Select one of the five Hermes backends above. |

`OPENLINKER_API_BASE` remains accepted as an alias for `OPENLINKER_URL`.
`runtime_ws` and `runtime_pull` remain accepted as aliases for `ws` and `pull`.

## Commands

```bash
hermes openlinker register
hermes openlinker status
hermes openlinker worker
```

The `/openlinker` command inside Hermes shows whether the background worker is running and which
local settings are missing. It never prints the Agent Token or private key.

## Backend details

### `hermes_agent`

Calls Hermes `AIAgent.run_conversation()` directly. Conversation history is kept in memory and
grouped by the OpenLinker session metadata, falling back to the run ID.

### `dispatch_tool`

Calls Hermes `ctx.dispatch_tool()`. Set `OPENLINKER_HERMES_DISPATCH_TOOL` if the tool is not
`delegate_task`. If Hermes reports that the tool is unknown, the plugin can fall back to
`hermes_cli`.

### `hermes_cli`

Runs `hermes -z <prompt>`. Set `OPENLINKER_HERMES_CLI_COMMAND` or `HERMES_BIN` to choose a
different executable.

### `command`

Runs `OPENLINKER_HERMES_TURN_COMMAND`. The command receives JSON on stdin and in
`OPENLINKER_HERMES_RUN`. It may return plain text or JSON containing `text`, `answer`,
`output`, `content`, or `result`.

### `echo`

Returns the input without calling Hermes. Use it only for local connection tests.

## Upgrading from the old Runtime Token setup

The current Python SDK uses an Agent Token plus Runtime Node mTLS. It no longer accepts
`OPENLINKER_RUNTIME_TOKEN`.

Do not rename the old Runtime Token to `OPENLINKER_AGENT_TOKEN`; they are different credentials.
Run `hermes openlinker register` to create or reuse an Agent Token, then ask an administrator for
the Runtime Node and mTLS settings. The plugin reports a migration error when it finds only the
old token.

Hermes model and provider selection still come from the normal Hermes configuration. This plugin
does not override them.
