# 安装和运行 OpenLinker Hermes 插件

[English](INSTALL.md)

## 准备条件

- 这台机器上的 Hermes Agent 已经可以正常使用。
- Hermes 使用的 Python 版本不低于 3.10。
- 本地有 `openlinker-python` 和 `openlinker-hermes-plugin` 仓库。
- 第一次注册 Agent 时需要 User Token。
- OpenLinker 管理员提供的 Runtime Node ID 和 mTLS 文件。

User Token 用来创建或管理 Agent，Agent Token 用来运行 Agent，Node ID 和 mTLS 文件让这台
机器连接 Runtime 服务。这几种信息不能互相替代。

## 1. 安装

```bash
python -m pip install -e /path/to/openlinker-python
python -m pip install -e /path/to/openlinker-hermes-plugin
hermes plugins enable openlinker
```

确认 Hermes 能找到插件：

```bash
hermes plugins list
```

也可以在 Hermes 配置里启用：

```yaml
plugins:
  enabled:
    - openlinker
```

## 2. 注册 Agent

```bash
export OPENLINKER_URL="https://api.openlinker.ai"
export OPENLINKER_USER_TOKEN="ol_user_..."

hermes openlinker register \
  --agent-slug hermes-agent-local \
  --agent-name "Hermes Agent"
```

使用其他 OpenLinker 部署时，传入 `--url` 或设置 `OPENLINKER_URL`。
`--api-base` 和 `OPENLINKER_API_BASE` 暂时作为旧名称继续兼容。

注册信息会保存到 `$HERMES_HOME/openlinker.env`；没有设置 `HERMES_HOME` 时保存到
`~/.hermes/openlinker.env`。可以用 `--registration-env` 选择其他文件。

命令会告诉你文件保存在哪里，但不会把 Agent Token 打印出来。

## 3. 配置 Runtime Node

向 OpenLinker 管理员索取：

- `OPENLINKER_NODE_ID`
- 客户端证书
- 客户端私钥
- CA 证书
- 只有 Runtime 使用独立地址时才需要的 `OPENLINKER_RUNTIME_URL`

在 Hermes 机器上设置：

```bash
export OPENLINKER_NODE_ID="..."
export OPENLINKER_RUNTIME_MTLS_CERT_FILE="/secure/path/client.crt"
export OPENLINKER_RUNTIME_MTLS_KEY_FILE="/secure/path/client.key"
export OPENLINKER_RUNTIME_MTLS_CA_FILE="/secure/path/ca.crt"
export OPENLINKER_RUNTIME_DATA_DIR="$HERMES_HOME/openlinker-runtime"
```

请限制注册文件和私钥的权限，只允许运行 Hermes 的系统账号读取。

## 4. 检查并启动

```bash
hermes openlinker status
hermes openlinker worker
```

`status` 只检查本机文件和环境变量。它显示配置齐全，不代表服务器一定能连通。

除非管理员明确要求固定连接方式，否则使用 `OPENLINKER_RUNTIME_TRANSPORT=auto`。
另外两个可选值是 `ws` 和 `pull`。

需要 Hermes 加载插件时自动启动 worker，可以设置：

```bash
export OPENLINKER_RUNTIME_ENABLED=true
```

也可以把这项写进注册信息文件，然后重启 Hermes。

## 从旧 Runtime Token 配置升级

旧插件使用 `OPENLINKER_RUNTIME_TOKEN`、
`OPENLINKER_WORKER_CONNECTOR=runtime_pull` 和已经删除的 Python SDK Native API。

当前配置需要：

1. 通过 `hermes openlinker register` 获得 Agent ID 和 Agent Token；
2. Runtime Node ID；
3. Runtime mTLS 客户端证书、私钥和 CA 文件；
4. `OPENLINKER_RUNTIME_TRANSPORT=auto|ws|pull`。

不要把旧 Runtime Token 复制成 `OPENLINKER_AGENT_TOKEN`，请重新注册。
`runtime_pull` 和 `runtime_ws` 会在一个迁移周期内继续兼容，分别转成 `pull` 和 `ws`。

`OPENLINKER_WORKER_MAX_RUNS` 不再支持。可靠 Runtime worker 是长期运行进程，请通过正常的
进程或服务停止流程关闭它。

## 常见问题

**Hermes 无法导入 `openlinker`**

请把 `openlinker-python` 安装到 Hermes 实际使用的 Python 环境。

**Hermes 找不到插件**

```bash
python -c "import importlib.metadata as m; print(m.entry_points(group='hermes_agent.plugins'))"
```

**status 显示 Agent 尚未注册**

带 User Token 运行 `hermes openlinker register`。如果用了自定义注册文件，每条命令都要
传入同一个 `--registration-env`。

**status 显示缺少 Runtime 设置**

注册 Agent 不能创建 Runtime Node 凭证。请向管理员索取上面列出的 Node ID 和 mTLS 文件。

**worker 提示 `OPENLINKER_RUNTIME_TOKEN` 已废弃**

重新注册后删除旧设置。不要把旧 Token 或新的 Agent Token 发到日志和支持消息里。

**Hermes 使用了错误的模型或服务商**

插件不负责选择模型，请检查 Hermes 自己的配置：

```bash
hermes config
hermes model
```
