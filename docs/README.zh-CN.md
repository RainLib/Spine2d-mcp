![Spine2d-mcp](assets/brand/banner.png)

# Spine2d-mcp

仓库/展示名称改为 **Spine2d-mcp**；Python包名和启动命令继续使用 `spine-pipeline-mcp`，不影响既有客户端。项目icon保持原样，仅横幅更新。横幅独立展示未修改的Spine官方标志，Codex与Claude Code使用普通文字，不表示官方背书。第三方标志不归本项目MIT许可，见[第三方声明](../THIRD_PARTY_NOTICES.md)。

项目 **0.1.0**，采用 Python 官方 MCP SDK **2.3.0**，通过 stdio 使用。它不是“协议 2.0”或 FastMCP 2.x。

## 已实现 10 个工具

- 读取/静态检查：`skeleton_inspect`、`skeleton_validate`、`job_validate`。
- 暂存：`stage_json_copy`、`stage_asset_bundle`（JSON + 引用图片）。
- 动画：`animation_copy`、`animation_retime`、`bone_keys_set`。
- 原生管线：`spine_export`、`godot_validate`。

变换都会创建新 job，不覆盖源文件或输入 job。动画变速和关键帧编辑暂只支持线性/stepped，遇到数字Bezier曲线明确拒绝。rotate 使用 Spine 4.3 的 `value` 字段。

本地真实副本验证已覆盖：weighted mesh素材 → 动画复制/变速/关键帧调整 → Spine **4.3.26** 导出 `.spine`、JSON、atlas、PNG → 原生 Spine-enabled Godot **4.7.1 custom build** 加载/初始化/短动画采样。不是全部版本兼容保证，也不是视觉质量验收；测试游戏素材和本地路径不公开。

## 整体 Mesh 的边界

可检查骨骼引用/循环、UV、三角索引、weighted vertices编码、权重和与时间线。不会自动重新绑骨、生成完整Mesh或改权重。连续身体、脸部刚性、披风隔离、脚不漂移仍需本地角色适配器和渲染验证，不能用“资源加载成功”替代。

## Codex / Claude 接入

完整步骤与模板见[接入指南](clients.md)。**Codex 使用 TOML 的 `mcp_servers`，Claude Code 使用 JSON 的 `mcpServers`，不能混用。** Codex 已实测真实只读工具调用；Claude目前只验证独立配置的Connected健康状态，未声称模型驱动调用已通过。使用独立 `CODEX_HOME` 的API模式不会自动继承默认配置。

## 使用

依赖安装与测试：`uv sync --locked`、`uv run --locked pytest -q`。
客户端 command 为 `uv`，args 为 `--directory /path/to/Spine2d-mcp run --locked spine-pipeline-mcp`（各项拆为数组）。

必须设置两个不重叠目录：`SPINE_MCP_SOURCE_ROOT`、`SPINE_MCP_STAGING_ROOT`。首次使用测试副本。
CLI额外需要 `SPINE_MCP_CLI`（已授权本机Spine绝对路径）、`SPINE_MCP_CLI_VERSION`（精确版本）；Godot检查需要 `SPINE_MCP_GODOT_EXECUTABLE`（含原生SpineSprite的版本，不能默认普通Godot）。

所有输出只写独立暂存，无发布到游戏的工具；无任意shell执行。Godot生成最小隔离项目，无游戏autoload。Spine输出隔离，但仍可能读写正常许可证/缓存/设置，不是OS沙箱。暂存不自动清理。

## 开源与本地分离

仓库仅通用代码、合成测试和文档，MIT许可。游戏专有资产、本地路径、角色策略、测试结果放在仓库外的本地适配器中。Spine商业软件不随项目分发。本项目非官方Spine产品。

CI仅提供 [模板](ci-workflow.yml.example)，当前发布凭据缺workflow权限，云端CI未启用。详细配置与架构见[主README](../README.md)。
