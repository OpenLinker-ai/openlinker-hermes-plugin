# OpenLinker Hermes Plugin Installation

This guide installs `openlinker-hermes-plugin` as a standard Hermes pip entry-point plugin.

For v0.1, the OpenLinker Python SDK is installed from a local checkout because it is not published
to PyPI yet.

## Requirements

- Hermes Agent installed and working.
- Python 3.10+ in the same environment used by Hermes.
- Local checkouts of:
  - `openlinker-python`
  - `openlinker-hermes-plugin`
- An OpenLinker creator token for the one-time registration step.

## Install

Use the Python interpreter that Hermes uses. For many Hermes installs this is just:

```bash
python -m pip install -e /path/to/openlinker-python
python -m pip install -e /path/to/openlinker-hermes-plugin
```

If you want to use the Aliyun PyPI mirror for third-party dependencies:

```bash
python -m pip install \
  -i https://mirrors.aliyun.com/pypi/simple/ \
  --trusted-host mirrors.aliyun.com \
  -e /path/to/openlinker-python

python -m pip install \
  -i https://mirrors.aliyun.com/pypi/simple/ \
  --trusted-host mirrors.aliyun.com \
  -e /path/to/openlinker-hermes-plugin
```

Confirm Hermes can discover the plugin:

```bash
hermes plugins list
```

## Enable

Enable the entry-point plugin:

```bash
hermes plugins enable openlinker
```

Equivalently, add `openlinker` to Hermes config:

```yaml
plugins:
  enabled:
    - openlinker
```

Hermes plugin docs note that pip entry-point plugins use the entry-point key as the enabled name.
For this package, that name is `openlinker`.

## Register

Register or reuse the OpenLinker runtime agent:

```bash
hermes openlinker register \
  --user-token "$OPENLINKER_USER_TOKEN" \
  --agent-slug hermes-agent-local \
  --agent-name "Hermes Agent"
```

If you use a non-default OpenLinker API host:

```bash
hermes openlinker register \
  --api-base "https://your-openlinker-api.example" \
  --user-token "$OPENLINKER_USER_TOKEN"
```

The command persists runtime registration state to:

```text
$HERMES_HOME/openlinker.env
```

If `HERMES_HOME` is not set, it uses:

```text
~/.hermes/openlinker.env
```

Use a custom state file if needed:

```bash
hermes openlinker register \
  --registration-env /secure/path/openlinker.env \
  --user-token "$OPENLINKER_USER_TOKEN"
```

## Validate

Check that the persisted runtime token works:

```bash
hermes openlinker status
```

If you used a custom registration env file:

```bash
hermes openlinker status --registration-env /secure/path/openlinker.env
```

## Run Worker

For a foreground worker:

```bash
hermes openlinker worker
```

To start the worker automatically when Hermes loads the plugin, set:

```bash
export OPENLINKER_RUNTIME_ENABLED=true
```

or persist it in the registration env file:

```env
OPENLINKER_RUNTIME_ENABLED=true
```

Then restart Hermes.

## Model Selection

The plugin does not choose or override Hermes' model/provider/base URL. Hermes uses its normal
model configuration.

If Hermes calls the wrong provider, inspect Hermes config with:

```bash
hermes config
hermes model
```

## Troubleshooting

If Hermes cannot import `openlinker`, install the local SDK into the same Python environment:

```bash
python -m pip install -e /path/to/openlinker-python
```

If `hermes plugins enable openlinker` says the plugin is not installed, verify it is installed in
the same environment as Hermes:

```bash
python -c "import importlib.metadata as m; print(m.entry_points(group='hermes_agent.plugins'))"
```

If `status` says a runtime token is missing, run `register` first. `OPENLINKER_USER_TOKEN` is for
registration; `OPENLINKER_RUNTIME_TOKEN` is for runtime `status` and `worker`.
