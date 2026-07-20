# Install and operate the OpenLinker Hermes plugin

[简体中文](INSTALL.zh-CN.md)

## Requirements

- Hermes Agent already works on this machine.
- Python 3.10 or later in the environment used by Hermes.
- Local checkouts of `openlinker-python` and `openlinker-hermes-plugin`.
- A User Token if this is the first Agent registration.
- A Runtime Node ID and mTLS files supplied by an OpenLinker administrator.

The User Token creates or manages the Agent. The Agent Token runs the Agent. The Node ID and mTLS
files let this machine connect to the Runtime service. These values are not interchangeable.

## 1. Install

```bash
python -m pip install -e /path/to/openlinker-python
python -m pip install -e /path/to/openlinker-hermes-plugin
hermes plugins enable openlinker
```

Confirm Hermes can see it:

```bash
hermes plugins list
```

You may also enable it in Hermes configuration:

```yaml
plugins:
  enabled:
    - openlinker
```

## 2. Register the Agent

```bash
export OPENLINKER_URL="https://api.openlinker.ai"
export OPENLINKER_USER_TOKEN="ol_user_..."

hermes openlinker register \
  --agent-slug hermes-agent-local \
  --agent-name "Hermes Agent"
```

For another OpenLinker deployment, pass `--url` or set `OPENLINKER_URL`.
`--api-base` and `OPENLINKER_API_BASE` remain temporary compatibility aliases.

Registration is saved to `$HERMES_HOME/openlinker.env`, or
`~/.hermes/openlinker.env` when `HERMES_HOME` is unset. Choose another file with
`--registration-env`.

The command output tells you where the file was saved, but does not print the Agent Token.

## 3. Configure the Runtime Node

Ask an OpenLinker administrator for:

- `OPENLINKER_NODE_ID`
- the client certificate
- the client private key
- the CA certificate
- `OPENLINKER_RUNTIME_URL`, only when Runtime uses a separate address

Set them on the Hermes machine:

```bash
export OPENLINKER_NODE_ID="..."
export OPENLINKER_RUNTIME_MTLS_CERT_FILE="/secure/path/client.crt"
export OPENLINKER_RUNTIME_MTLS_KEY_FILE="/secure/path/client.key"
export OPENLINKER_RUNTIME_MTLS_CA_FILE="/secure/path/ca.crt"
export OPENLINKER_RUNTIME_DATA_DIR="$HERMES_HOME/openlinker-runtime"
```

Protect the registration file and private key so only the Hermes service account can read them.

## 4. Check and run

```bash
hermes openlinker status
hermes openlinker worker
```

`status` checks local files and environment variables only. A successful status means the
required settings are present; it does not prove that the server is reachable.

Use `OPENLINKER_RUNTIME_TRANSPORT=auto` unless an administrator tells you to force `ws` or
`pull`.

To start the worker whenever Hermes loads:

```bash
export OPENLINKER_RUNTIME_ENABLED=true
```

You can put the setting in the registration env file and then restart Hermes.

## Upgrade from the pre-0.1 Runtime Token setup

The old plugin used `OPENLINKER_RUNTIME_TOKEN`, `OPENLINKER_WORKER_CONNECTOR=runtime_pull`,
and the removed Python SDK Native API.

The current setup requires:

1. an Agent ID and Agent Token from `hermes openlinker register`;
2. a Runtime Node ID;
3. Runtime mTLS certificate, key, and CA files;
4. `OPENLINKER_RUNTIME_TRANSPORT=auto|ws|pull`.

Do not copy the old Runtime Token into `OPENLINKER_AGENT_TOKEN`. Register again. Legacy connector
values `runtime_pull` and `runtime_ws` are still mapped to `pull` and `ws` for one migration
period.

`OPENLINKER_WORKER_MAX_RUNS` is no longer supported because the reliable Runtime worker is a
long-running process. Stop it through normal process or service shutdown.

## Troubleshooting

**Hermes cannot import `openlinker`**

Install `openlinker-python` into the same Python environment that runs Hermes.

**Hermes cannot find the plugin**

```bash
python -c "import importlib.metadata as m; print(m.entry_points(group='hermes_agent.plugins'))"
```

**Status says Agent registration is missing**

Run `hermes openlinker register` with a User Token. If you use a custom registration file, pass
the same `--registration-env` to every command.

**Status says Runtime settings are missing**

Registration cannot create Runtime Node credentials. Ask an administrator for the Node ID and
mTLS files listed above.

**The worker reports that `OPENLINKER_RUNTIME_TOKEN` is obsolete**

Remove the old setting after registering again. Do not expose either the old token or the new
Agent Token in logs or support messages.

**Hermes uses the wrong model or provider**

The plugin does not choose a model. Check the normal Hermes configuration with:

```bash
hermes config
hermes model
```
