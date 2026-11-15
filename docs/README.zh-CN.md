# Spine Pipeline MCP

本项目是可复用的本地 Spine 管线 MCP **最小基础版**，并不是完整动画制作工具。

- 项目版本：**0.1.0**。
- 框架：Python 官方 MCP SDK **2.3.0**，不是 FastMCP 2.0，也不是“协议 2.0”。
- 传输：stdio，不监听网络端口。

## 已实现

1. `skeleton_inspect`：读取白名单目录内的 JSON，列出版本、骨骼、动画、SHA-256；检查基本结构，提示重名骨骼和缺失父骨骼。
2. `stage_json_copy`：将 JSON 原样复制到独立 UUID 暂存目录，不覆盖源文件；不复制纹理或 atlas。

**尚未实现**：Spine CLI 导入导出、编辑器实时控制、动作生成、网格/权重编辑、完整校验、GIF/Godot 预览及发布回游戏。结构检查通过不等于实际渲染正确。

## 使用

安装 Python 3.11+ 和 uv 后，执行仓库主 README 的 quick start。`uv sync --locked` 安装锁定依赖；`uv run --locked pytest -q` 运行合成样本测试。随后在 MCP 客户端配置 `uv --directory /path/to/spine-pipeline-mcp run --locked spine-pipeline-mcp`。

必须设置 `SPINE_MCP_SOURCE_ROOT` 和 `SPINE_MCP_STAGING_ROOT`，且两个根目录不能相互包含。首次建议读取仓库的 `examples/source` 并暂存到 `.staging`。两个工具均接受 `{"relative_path":"minimal.json"}`。

拒绝绝对路径、`..`、符号链接和特殊文件，单 JSON 最大 16 MiB。无任意命令、覆盖、删除或发布工具。它不是操作系统沙箱，不防御恶意本地进程并发替换目录。暂存不会自动清理，需自行控制磁盘占用。

## 为什么选择 Python

艺术资源管线通常已有 Python、Pillow、NumPy 和 JSON 处理逻辑，沿用更容易迭代。Go 的单二进制部署有优势，但现在用 Go 包一层 Python worker 只会增加进程和错误处理成本。

计划按“检查 → 暂存 → 变换 → 固定版本 CLI → 引擎预览 → 明确授权发布”分层扩展，游戏项目用 adapter 接入。不把任何项目专有资产和硬编码路径放进通用核心。

本项目代码及合成示例采用 MIT。Spine 是 Esoteric Software 的商业软件，不随本项目提供；未来使用 CLI 需要自行安装并遵守其许可。本项目非官方 Spine 产品。

完整架构和功能边界请见 [英文 README](../README.md) 与 [Architecture](architecture.md)。

## CI 状态

当前发布凭据没有 GitHub workflow 写入权限，所以只提供 `ci-workflow.yml.example` 模板，尚未启用或验证云端 CI。维护者可使用具有适当权限的身份将模板放到 `.github/workflows/ci.yml` 后运行。本地测试与构建已通过。
