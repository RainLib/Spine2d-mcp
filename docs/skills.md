# 通用游戏制作 Skills

这三项技能随通用工程提供，用于后续不同游戏的素材、Spine 制作和运行时接入。它们不包含特定游戏路径、角色结构、骨骼名单、性能预算或消费方代码。技能是代理的工作指导，不会让尚未实现的 MCP 接口自动出现。

| 技能 | 使用场景 | 入口 |
| --- | --- | --- |
| `spine-asset-prep` | 可选探测 PhotoCraft／Photoshop MCP；优先管理可编辑图层、状态预览及 Spine 素材交接 | [SKILL.md](../skills/spine-asset-prep/SKILL.md) |
| `spine-rig-animation` | 骨架、Mesh、权重、动画效果和物理次级运动；暂存、原生验证与本地扩展 | [SKILL.md](../skills/spine-rig-animation/SKILL.md) |
| `spine-game-integration` | Slot、附件、挂点、换肤、装备、技能事件与运行资源验证 | [SKILL.md](../skills/spine-game-integration/SKILL.md) |

## 可选 photo 编辑器

技能要求通过实际工具发现及只读调用区分“应用已安装”“MCP 已配置”和“MCP 已连通”。有可用 PhotoCraft／Photoshop MCP 时优先用它管理 AI 素材与图层；若都没有，则继续文件交接及可执行的 Spine 工作。不会为了使用本包强制安装 photo 应用或连接插件。

PhotoCraft 与 Photoshop 使用各自发现的接口；不互相套用命令。既有手工图层优先保留，支持明确的原生工程、互斥状态、透明导出和读回校验。图层拆分方式取决于素材和动作，不强制每个角色采用同一种 mesh 数量。

## 能力边界

通用包目前提供 15 个 MCP 工具。技能说明了这些工具的适用范围，以及怎样使用普通 Python `ProjectAdapter` 承接缺少的操作。物理约束、骨架／skin／slot 的创建、自动轮廓布网与完整动画质量验收仍需要实际可用的编辑器接口或显式扩展；技能不把这些描述为现成 MCP 工具。

Physics 的连续历史、暂停和重置，换肤后的附件恢复，表现事件与游戏权威判定，以及真实动态预览均有独立指导。检查报告区分静态验证、原生加载、完整行为和视觉验收。

## 推荐安装

推荐通过仓库插件市场将 MCP 和三项技能一起安装，或者用 `skills.sh` CLI 单独拉取技能；详细步骤、远程发布状态和 MCP 连接方式见[安装与分发](distribution.md)。从公开仓库安装：

```sh
npx skills add RainLib/Spine2d-mcp \
  --skill spine-asset-prep spine-rig-animation spine-game-integration \
  --agent codex --global
```

需要 Node.js 22.20+。Claude 使用 `--agent claude-code`，两者一起使用 `--agent codex claude-code`；去掉 `--global` 为当前项目安装。仅选一项时缩短 `--skill` 列表。本地开发时把仓库来源换成 checkout 的绝对路径。CLI 方式只安装技能，不连接 MCP；插件方式已经同时携带两者，不要重复安装同名技能。

## 本地开发与不使用 Node.js 的安装

Codex 可以将需要的技能目录安装到 `${CODEX_HOME:-$HOME/.codex}/skills/`，保留 `SKILL.md`、`agents/`、`references/` 的相对结构。可复制目录；本地开发也可链接到本仓库的对应目录。存在同名技能时先比较内容，避免覆盖用户已有扩展。

例如，目标不存在时可以从仓库根目录执行：

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s "$PWD/skills/spine-asset-prep" "${CODEX_HOME:-$HOME/.codex}/skills/spine-asset-prep"
ln -s "$PWD/skills/spine-rig-animation" "${CODEX_HOME:-$HOME/.codex}/skills/spine-rig-animation"
ln -s "$PWD/skills/spine-game-integration" "${CODEX_HOME:-$HOME/.codex}/skills/spine-game-integration"
```

链接依赖本地 checkout 的位置，移动仓库时需更新链接。其他支持 `SKILL.md` 的客户端按各自发现目录安装；MCP 连接配置和技能安装是独立步骤。单独安装 Python wheel 不会自动注册技能到客户端。

## 调用

安装后在支持刷新技能的客户端重新加载，或开启新会话。先验证 MCP 的 `skeleton_inspect` 实际成功，再在独立安装 Skills 的 Codex 中使用：

```text
使用 $spine-asset-prep 整理这些素材，优先使用可用的 photo MCP 管理图层与状态。
使用 $spine-rig-animation 调整角色绑定与动作，验证面部稳定和物理次级运动。
使用 $spine-game-integration 接入我指定的目标项目，处理挂点、换肤和事件契约。
```

三项技能允许按任务自动选择，也可以单独明确调用。只有用户后续指定了游戏制作／接入任务与目标，才在授权范围内读取或修改消费方工程。

Codex 插件安装使用 `$spine-pipeline:spine-asset-prep`、`$spine-pipeline:spine-rig-animation`、`$spine-pipeline:spine-game-integration`。Claude 的独立技能可用 `/spine-asset-prep`、`/spine-rig-animation`、`/spine-game-integration`；通过插件安装后使用 `/spine-pipeline:spine-asset-prep` 等带插件命名空间的入口。升级会替换安装副本，自己的角色策略和扩展脚本继续放在仓库之外。
