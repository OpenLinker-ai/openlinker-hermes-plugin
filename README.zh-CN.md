# openlinker-hermes-plugin

[English](README.md)

这个插件让 OpenLinker 可以把任务交给 Hermes Agent。它收到 OpenLinker Runtime 的任务后，
执行一轮 Hermes 对话，再把答案返回给 OpenLinker。

插件保留五种执行方式：

- `hermes_agent`：直接调用 Hermes `AIAgent`，默认使用这个方式。
- `dispatch_tool`：调用 Hermes 工具，例如 `delegate_task`。
- `hermes_cli`：执行 `hermes -z <问题>`。
- `command`：执行管理员指定的命令。
- `echo`：原样返回输入，只用于本地连通性测试。

## 开始前要准备什么

你需要两套不同的身份信息：

1. **Agent 注册信息**：Agent ID 和 Agent Token。运行 `hermes openlinker register` 时，
   插件可以创建或复用它们。
2. **Runtime Node 连接信息**：Node ID 和三份 mTLS 文件（客户端证书、私钥、CA 证书）。
   OpenLinker 管理员需要先创建 Runtime Node，再把这些内容交给运行 Hermes 的机器。

注册 Agent 不会自动创建 Runtime Node，也不会生成 mTLS 文件。

OpenLinker Python SDK 在 v0.1 阶段还没有发布到 PyPI。请先从本地仓库安装 SDK，再安装插件。

## 快速开始

在 Hermes 使用的 Python 环境里安装 SDK 和插件：

```bash
python -m pip install -e /path/to/openlinker-python
python -m pip install -e /path/to/openlinker-hermes-plugin
hermes plugins enable openlinker
```

注册或复用 Hermes Agent：

```bash
export OPENLINKER_URL="https://api.openlinker.ai"
export OPENLINKER_USER_TOKEN="ol_user_..."
hermes openlinker register
```

命令会把 Agent ID 和 Agent Token 保存到：

```text
$HERMES_HOME/openlinker.env
```

没有设置 `HERMES_HOME` 时，文件位置是 `~/.hermes/openlinker.env`。

然后填写管理员提供的 Runtime Node 信息：

```bash
export OPENLINKER_NODE_ID="..."
export OPENLINKER_RUNTIME_MTLS_CERT_FILE="/secure/path/client.crt"
export OPENLINKER_RUNTIME_MTLS_KEY_FILE="/secure/path/client.key"
export OPENLINKER_RUNTIME_MTLS_CA_FILE="/secure/path/ca.crt"
export OPENLINKER_RUNTIME_DATA_DIR="$HERMES_HOME/openlinker-runtime"
```

检查本机配置，再启动 worker：

```bash
hermes openlinker status
hermes openlinker worker
```

`status` 不会连接 OpenLinker，只会告诉你本机已经配置了什么、还缺什么。

完整安装和迁移说明见 [INSTALL.zh-CN.md](INSTALL.zh-CN.md)。

## 常用设置

| 名称 | 默认值 | 用途 |
| --- | --- | --- |
| `OPENLINKER_URL` | 无 | OpenLinker 对外平台地址。 |
| `OPENLINKER_RUNTIME_URL` | 从平台自动发现 | 可选的独立 Runtime 地址。 |
| `OPENLINKER_USER_TOKEN` | 无 | 只在创建、核对或轮换 Agent 注册信息时使用。 |
| `OPENLINKER_AGENT_ID` | 由 `register` 保存 | 接收任务的 Agent。 |
| `OPENLINKER_AGENT_TOKEN` | 由 `register` 保存 | worker 使用的 Agent 凭证。 |
| `OPENLINKER_NODE_ID` | 无 | 分配给这台机器的 Runtime Node。 |
| `OPENLINKER_RUNTIME_MTLS_CERT_FILE` | 无 | Runtime 客户端证书。 |
| `OPENLINKER_RUNTIME_MTLS_KEY_FILE` | 无 | Runtime 客户端私钥。 |
| `OPENLINKER_RUNTIME_MTLS_CA_FILE` | 无 | 用来核验 Runtime 服务的 CA 证书。 |
| `OPENLINKER_RUNTIME_DATA_DIR` | `$HERMES_HOME/openlinker-runtime` | 保存任务进度，重启后可以安全续跑。 |
| `OPENLINKER_RUNTIME_TRANSPORT` | `auto` | 可选 `auto`、`ws` 或 `pull`。 |
| `OPENLINKER_RUNTIME_ENABLED` | `false` | Hermes 加载插件时是否自动启动 worker。 |
| `OPENLINKER_AUTO_REGISTER` | `true` | worker 启动前是否创建或复用 Agent 注册信息。 |
| `OPENLINKER_REGISTRATION_ENV` | `$HERMES_HOME/openlinker.env` | 保存 Agent 注册信息的文件。 |
| `OPENLINKER_HERMES_BACKEND` | `hermes_agent` | 选择上面的五种 Hermes 执行方式之一。 |

`OPENLINKER_API_BASE` 暂时仍可作为 `OPENLINKER_URL` 的旧名称使用。
`runtime_ws` 和 `runtime_pull` 也暂时分别兼容为 `ws` 和 `pull`。

## 命令

```bash
hermes openlinker register
hermes openlinker status
hermes openlinker worker
```

Hermes 里的 `/openlinker` 命令会显示后台 worker 是否在运行、还缺哪些本机设置。
它不会显示 Agent Token 或私钥。

## 五种执行方式

### `hermes_agent`

直接调用 Hermes `AIAgent.run_conversation()`。插件按 OpenLinker 的会话信息在内存中保存
对话历史；没有会话信息时使用运行 ID。

### `dispatch_tool`

调用 Hermes `ctx.dispatch_tool()`。工具名不是 `delegate_task` 时，设置
`OPENLINKER_HERMES_DISPATCH_TOOL`。Hermes 返回“工具不存在”时，插件可以改用
`hermes_cli`。

### `hermes_cli`

执行 `hermes -z <问题>`。可以用 `OPENLINKER_HERMES_CLI_COMMAND` 或 `HERMES_BIN`
指定其他可执行文件。

### `command`

执行 `OPENLINKER_HERMES_TURN_COMMAND`。命令会从标准输入和
`OPENLINKER_HERMES_RUN` 收到 JSON，可以返回普通文字，也可以返回包含 `text`、
`answer`、`output`、`content` 或 `result` 的 JSON。

### `echo`

不调用 Hermes，直接返回输入。只用于本地连接测试。

## 从旧 Runtime Token 配置升级

当前 Python SDK 使用 Agent Token 加 Runtime Node mTLS，不再接受
`OPENLINKER_RUNTIME_TOKEN`。

不要把旧 Runtime Token 改名成 `OPENLINKER_AGENT_TOKEN`，它们不是同一种凭证。
请重新运行 `hermes openlinker register` 创建或复用 Agent Token，再向管理员索取
Runtime Node 和 mTLS 配置。插件发现只有旧 Token 时会明确提示迁移，不会偷偷混用。

Hermes 的模型和服务商仍由 Hermes 自己的配置决定，本插件不会覆盖。
