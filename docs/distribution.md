# Installation and marketplaces / 安装与分发

这个工程同时提供可执行的 MCP 服务和三个 `SKILL.md` 技能。推荐使用客户端插件一起安装；只需要其中一部分时，用 `skills` CLI 和 `uvx` 分别安装。无需接入任何特定游戏工程。

| 入口 | 用户获得什么 | 发布条件 |
| --- | --- | --- |
| 本地 checkout | 当前源码、MCP、三项技能、市场清单 | 当前工作副本即可使用 |
| `npx skills add RainLib/Spine2d-mcp` | 从 GitHub 安装技能到选定客户端 | `skills/` 必须已推送到所选 ref；无需先申请排行榜收录 |
| Codex / Claude 仓库市场 | 一个插件包含 MCP 和全部技能 | 对应市场清单及插件文件必须已推送到所选 ref |
| `uvx --from git+https://…` | 从 Git 构建并启动 MCP | 所选 ref 中已有 Python 包；无需 PyPI |
| 公共插件目录 / MCP Registry | 公开发现与客户端集成入口 | 各平台独立的提交、所有权验证或审核流程 |

**当前状态：**`main` 已提供 0.2.0、15 个 MCP 工具、三项技能和两种仓库市场清单，可按下面的命令从 GitHub 安装。本文不宣称已有 PyPI 包、公共插件目录条目或 MCP Registry 条目。实测范围见文末验证记录。

## Install the combined plugin

需要 Git、Python 3.11+、[uv](https://docs.astral.sh/uv/getting-started/installation/) 和支持插件的客户端。`uv` 必须在客户端进程的 PATH 内。首次启动会按随包的 `uv.lock` 安装依赖；无需手动创建 venv。没有 `codex plugin` 或 Claude `userConfig` 支持的旧客户端，请使用下面的独立安装方式。

Codex：

```sh
codex plugin marketplace add RainLib/Spine2d-mcp
codex plugin add spine-pipeline@rainlib-spine
```

Claude Code：

```sh
claude plugin marketplace add RainLib/Spine2d-mcp
claude plugin install spine-pipeline@rainlib-spine
```

市场名为 `rainlib-spine`，插件名为 `spine-pipeline`，展示名为 **Spine2d-mcp**。这是本仓库维护的市场，不代表客户端官方推荐或公共目录审核通过。

### Configure the plugin

**Codex：**插件只转发下面列明的 Spine 配置。先替换为本机绝对路径，再从同一个终端启动 Codex：

```sh
export SPINE_MCP_SOURCE_ROOT=/absolute/path/to/test-assets
export SPINE_MCP_STAGING_ROOT=/absolute/path/to/separate-staging
codex
```

源目录必须已经存在，两个目录不能相同，也不能互为父子目录；使用不含符号链接的真实路径（macOS 的 `/tmp`、`/var` 等别名需要换成实际路径）。插件配置提供 120 秒启动和 300 秒工具超时。桌面客户端需要它自身的启动环境包含这些变量；从系统 Dock 打开的应用不保证继承终端的 `export`。需要固定的桌面配置时，使用独立 MCP 安装方式，将两个目录写入该 MCP 的客户端配置。

**Claude Code：**启用插件时根据提示填写 `Source assets directory` 和 `Staging output directory`。也可以用 CLI 保存两个选项，无需改插件文件：

```sh
claude plugin configure spine-pipeline@rainlib-spine --values-stdin <<'JSON'
{
  "source_root": "/absolute/path/to/test-assets",
  "staging_root": "/absolute/path/to/separate-staging"
}
JSON
claude plugin configure spine-pipeline@rainlib-spine
```

启动新会话，或按客户端支持方式重新加载插件。先对实际文件执行 `skeleton_inspect`；成功发现插件不等于 MCP 已成功调用。

原生步骤是可选的。在启动客户端的环境中增加 `SPINE_MCP_CLI`、精确匹配素材的 `SPINE_MCP_CLI_VERSION`、`SPINE_MCP_GODOT_EXECUTABLE`。Spine 商业程序和带原生 Spine 支持的 Godot 不包含在插件内，详见[客户端指南](clients.md#4-enable-the-local-spine--godot-steps)。PhotoCraft／Photoshop MCP 也由用户独立连接，技能会按当前可用接口探测。

### Local checkout

本地目录应是通用仓库的绝对路径。Codex：

```sh
codex plugin marketplace add /absolute/path/to/Spine2d-mcp
codex plugin add spine-pipeline@rainlib-spine
```

Claude Code：

```sh
claude plugin marketplace add /absolute/path/to/Spine2d-mcp
claude plugin install spine-pipeline@rainlib-spine
```

同名市场只添加一个来源；不要同时添加本地和 Git 来源。配置目录仍按上一节进行。需要开发版 Skills、但不安装插件时，在目标工作目录运行：

```sh
npx skills add /absolute/path/to/Spine2d-mcp \
  --skill spine-asset-prep spine-rig-animation spine-game-integration \
  --agent codex claude-code
```

这会向当前工作目录安装技能；增加 `--global` 才会安装为用户级技能。若已经有同名本地扩展，先比较或备份，不要覆盖。链接方式见[技能指南](skills.md#本地开发与不使用-nodejs-的安装)。

## Install Skills separately

使用 [Vercel Labs 的 skills CLI](https://github.com/vercel-labs/skills)，需要 Node.js 22.20+。先列出远程技能，再安装：

```sh
npx skills add RainLib/Spine2d-mcp --list
npx skills add RainLib/Spine2d-mcp \
  --skill spine-asset-prep spine-rig-animation spine-game-integration \
  --agent codex --global
```

`--agent claude-code` 为 Claude 安装；`--agent codex claude-code` 同时为二者安装。`--skill` 后可只保留需要的技能。省略 `--global` 是项目级安装。安装保留技能目录内的 `agents/`、`references/`，不需要逐个复制文件；**它不会安装或配置 MCP**。

[skills.sh FAQ](https://skills.sh/docs/faq) 说明排行榜依据安装统计自动发现技能；仓库直接安装不以排行榜展示为前提。可以使用 CLI 的 `DISABLE_TELEMETRY=1` 关闭统计。这里不制造安装量，也不把 CLI 兼容视为平台认证。

## Install MCP separately

无需手动克隆或发布到 PyPI。`uvx` 使用 Git 包来源，并在自己的工具环境中运行服务。

**Codex：**

```sh
codex mcp add spine-pipeline \
  --env SPINE_MCP_SOURCE_ROOT=/absolute/path/to/test-assets \
  --env SPINE_MCP_STAGING_ROOT=/absolute/path/to/separate-staging \
  -- uvx --from git+https://github.com/RainLib/Spine2d-mcp.git@main spine-pipeline-mcp
codex mcp get spine-pipeline --json
```

首次 Git 下载和 Python 构建可能超过客户端默认启动时间。可先预热包环境（此命令不启动 MCP，也不读取素材）：

```sh
uvx --from git+https://github.com/RainLib/Spine2d-mcp.git@main \
  python -c 'import spine_pipeline_mcp'
```

再合并下面两个超时值到已有命名表中，不要重复创建同名 TOML 表或覆盖其他配置：

```toml
[mcp_servers.spine-pipeline]
# Keep the existing command, args and env configuration.
startup_timeout_sec = 120
tool_timeout_sec = 300
```

**Claude Code：**在需要使用的工作目录执行，`local` 范围保留为个人配置：

```sh
claude mcp add --transport stdio --scope local spine-pipeline \
  --env SPINE_MCP_SOURCE_ROOT=/absolute/path/to/test-assets SPINE_MCP_STAGING_ROOT=/absolute/path/to/separate-staging \
  -- uvx --from git+https://github.com/RainLib/Spine2d-mcp.git@main spine-pipeline-mcp
claude mcp get spine-pipeline
```

替换路径后启动新会话，要求调用 `skeleton_inspect(relative_path="你的素材.json")`。不需要 cloud API key；模型客户端仍使用自身登录。Spine 原生导出和 Godot 检查的环境配置见[客户端指南](clients.md)。

本地开发改用 `uv --directory /absolute/path/to/Spine2d-mcp run --locked spine-pipeline-mcp`。Git 安装按选定 ref 的 `pyproject.toml` 解析依赖；插件和本地 `uv run --locked` 路线使用仓库锁文件。需要固定行为时选择发布的 tag 或完整 commit，不能把 `@main` 当成固定版本。

## Updates and removal

技能和插件选一种安装方式，避免同一客户端重复加载。修改过的技能先保存本地扩展；升级会换成上游版本。

```sh
# Standalone skills: choose global or project scope as appropriate.
npx skills update spine-asset-prep spine-rig-animation spine-game-integration --global
npx skills remove spine-asset-prep spine-rig-animation spine-game-integration --agent codex --global

# Codex repository plugin: refresh the source, then install the selected version.
codex plugin marketplace upgrade rainlib-spine
codex plugin add spine-pipeline@rainlib-spine
codex plugin remove spine-pipeline@rainlib-spine

# Claude repository plugin.
claude plugin marketplace update rainlib-spine
claude plugin update spine-pipeline@rainlib-spine
claude plugin uninstall spine-pipeline@rainlib-spine

# Standalone MCP registration, in the same client/scope used during installation.
codex mcp remove spine-pipeline
claude mcp remove --scope local spine-pipeline
```

上面的删除命令用于需要卸载时，不是安装步骤。插件发布时要提高两个 `plugin.json` 的版本号，避免客户端复用旧缓存。使用 Git MCP 的用户可以更新固定 ref；对于持续跟随 `main` 的配置，先用 `uvx --refresh --from git+https://github.com/RainLib/Spine2d-mcp.git@main python -c 'import spine_pipeline_mcp'` 刷新，再重启 MCP。卸载客户端条目不等于删除暂存素材。

## Public directories and MCP Registry

仓库市场已经能承载“添加来源 → 安装插件”的流程，无需先被公共商城收录。进一步公开分发是不同步骤：

- **skills.sh：**公开 `skills/`，验证远程 `--list` 和安装，按平台安装统计与发现规则展示。[官方说明](https://skills.sh/docs/faq)
- **Codex / ChatGPT 公共插件目录：**需要独立提交和审核；本服务是本机 stdio，不能冒充云端 HTTP MCP。按平台的 desktop-only 插件要求处理。[插件打包](https://developers.openai.com/plugins/build/plugins)、[发布入口](https://developers.openai.com/plugins/deploy/submission)
- **Claude 公共插件目录：**自建仓库市场可直接由用户添加；公共目录审核与自建市场是两件事。[官方市场指南](https://code.claude.com/docs/en/plugin-marketplaces)
- **MCP Registry：**登记服务元数据，不托管 Python 包，也不提供通用于所有客户端的安装命令。本项目若采用 PyPI 分发，需要先发布真实包版本、加入 `mcp-name` 所有权标记，再准备 `server.json`、登录验证 `io.github.RainLib/…` 命名空间并用 `mcp-publisher` 校验／发布。不要在实际发布前给用户 `uvx spine-pipeline-mcp` 作为已经可用的命令。[Registry quickstart](https://modelcontextprotocol.io/registry/quickstart)、[包类型与验证](https://modelcontextprotocol.io/registry/package-types)

目前不需要为安装引入 npm 包装器、远程托管、API key 或游戏工程依赖。

## Maintainer checks

2026-11-15 从公开 GitHub 提交 `1669c57d3f5389b5aed2f8cf4f79a7cfc4ce1cf4` 验证 0.2.0，使用干净的 Linux ARM64 容器，不挂载开发 checkout 或用户客户端配置。工具版本：Codex CLI 0.169.0、Claude Code 2.1.325、skills CLI 1.8.1、uv 0.13.8、Python 3.12.16。

| 安装路径 | 已实测结果 |
| --- | --- |
| `npx skills add RainLib/Spine2d-mcp` | 远程发现三项；Codex／Claude 的用户级和项目级安装成功，用户级副本逐文件比对一致；更新与卸载成功 |
| 独立 `uvx` MCP | Git 下载／构建、Codex 与 Claude 注册／读取配置／移除成功；15 个工具可用 |
| Codex 仓库插件 | 添加远程市场、安装、刷新／重装及卸载成功；Codex app-server 实际发现该插件的 15 个工具和全部三项带命名空间的技能，无工具发现错误 |
| Claude 仓库插件 | 添加远程市场、安装、两项目录配置、更新及卸载成功；`claude mcp list` 返回该插件 **Connected** |
| Git clone 本地开发路径 | `uv sync --locked`、154 项 pytest、wheel/sdist 构建通过 |

官方 MCP SDK 对独立配置、两种已安装插件及克隆目录的启动命令分别验证了工具发现、`skeleton_inspect`、`mesh_inspect`、JSON 暂存、权重读取／修改和 `job_validate`；均为 15 个工具，编辑产生新 job，源文件哈希保持不变。自动化安装使用 `--yes` 回答 Skills 的交互选择；用户可保留交互安装。

这是安装、客户端加载和真实 MCP 调用验证，不声称本次测试包含模型驱动操作、Spine 商业软件导出、视觉效果验收或公共商城审核。原生步骤的既有验证范围见[客户端指南](clients.md#verification-record-and-limits)。

发布前至少检查：

```sh
claude plugin validate --strict .claude-plugin/plugin.json
claude plugin validate --strict .claude-plugin/marketplace.json
codex plugin list --marketplace rainlib-spine --available --json
npx skills add . --list
uv run --locked pytest -q
uv build
```

Codex 的列表检查应从这个本地仓库运行；若客户端尚未发现本地市场，先按上面的本地市场步骤添加。后续发布也应从干净环境重新执行远程安装和目录配置，核对实际工具／技能数量并执行真实 MCP 调用。仅清单校验通过不能替代这些检查。
