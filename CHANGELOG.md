# Changelog

## Unreleased

### Changed

- Updated the plugin to the current OpenLinker Python SDK Runtime Worker API.
- Replaced the removed Runtime Token flow with Agent Token plus Runtime Node mTLS.
- Added complete English and Simplified Chinese setup and migration guides.
- Kept `OPENLINKER_API_BASE`, `runtime_pull`, and `runtime_ws` as temporary migration aliases.

### Upgrade note

`OPENLINKER_RUNTIME_TOKEN` is no longer accepted. Do not reuse it as
`OPENLINKER_AGENT_TOKEN`. Register the Agent again, then configure the Runtime Node ID and mTLS
files supplied by an administrator.
