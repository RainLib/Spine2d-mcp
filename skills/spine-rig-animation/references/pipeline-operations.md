# MCP 能力与本地扩展

以下是本通用包实现的能力分类，执行时仍以**当前连接实际发现的 schema**为准。连接未刷新时不可直接调用尚未列出的工具。

| 能力 | 工具／接口 | 边界 |
| --- | --- | --- |
| 源检查 | `skeleton_inspect`、`skeleton_validate`、`mesh_inspect` | 读取配置根下的相对 JSON；mesh 检查也可读取 job |
| 暂存 | `stage_json_copy`、`stage_asset_bundle` | 前者仅 JSON，后者带引用图片；原生导出需要完整 bundle |
| 权重 | `mesh_weights_get`、`mesh_weights_set` | 分页读取；修改已有绑定，保留局部坐标，不能凭骨骼名称自动重绑 |
| 几何 | `mesh_replace` | 输入显式 UV、三角形、vertices、hull；不自动从图片生成网格 |
| 规则 | `job_validate`、`mesh_policy_validate` | 静态结构及声明式规则，不是完整 Spine schema／物理或视觉验收 |
| 动画 | `animation_copy`、`animation_retime`、`bone_keys_set` | 复制不覆盖目标；变速／设置 key 目前支持 linear／stepped，拒绝 Bezier |
| 原生管线 | `spine_export`、`godot_validate` | 配置本机合法可用的 Spine 与原生 Spine-enabled Godot；输出始终暂存 |

骨骼创建、IK／Transform／Path／Physics 约束编排、skin／slot 构造、自动布网、权重平滑与完整动态验收并没有对应的内置创建工具。写了技能不代表这些 MCP API 已存在。

当用户请求这些能力：先查是否有其他已验证的 Spine 编辑器桥接接口；否则读取已有本地生成器或使用通用包的 Python 扩展边界。核对目标版本的实际 schema／官方文档，生成副本，验证后再走原生导入。缺少运行时／编辑器时诚实说明未验证部分，不伪造工具调用或自动替换版本。

## 推荐链路

```text
inspect source → stage_asset_bundle → job A
mesh／animation edit → new job B
mesh_inspect + job_validate + project policy
spine_export → new job C
godot_validate → new check job D
local full-motion sampling / rendered review when needed
```

选择器为 `(skin, slot, attachment map key)`，不是贴图路径。编辑都返回新 job，下一步使用返回的 ID，不继续修改旧 job 或原图。导出的 atlas 全部纹理页需要一起交接。

编辑器版本必须与当前 `spine_export` 配置精确匹配。Spine 4.3 `bone_keys_set` 的 rotate 使用 `value`；不要把其他版本的 `angle` 示例直接套入。不同官方运行时、Godot 包装层和 4.2／4.3 的 API 名称可能不同，按安装版本和源码核实。

## 普通 Python 扩展

在使用方维护角色策略／生成器，显式注册可信回调：

```python
from pathlib import Path
from spine_pipeline_mcp.adapter import ProjectAdapter
from spine_pipeline_mcp.core import Workspace
from spine_pipeline_mcp.pipeline import Pipeline

pipeline = Pipeline(Workspace(Path(source_root), Path(staging_root)))
adapter = ProjectAdapter(pipeline, validators=[local_validator])
result = adapter.transform(parent_job_id, "custom_operation", local_transform, policy)
```

这里的变量来自本次任务的真实配置；不是可直接复制执行的项目配置。`local_transform(doc)` 返回候选 JSON；validator 接收副本并返回含布尔 `valid` 的对象。通用结构与本地检查通过后才创建新 job。直接调用 `Pipeline.transform` 不自动执行项目规则，需要规则时使用 `ProjectAdapter`。

回调是可信本地 Python，不是沙箱。先检查旧脚本的顶层副作用，避免为了复用一个函数触发全角色重建或源文件覆盖。MCP 工具参数不接受任意脚本路径。重复适用的能力可以后续纳入通用核心；本次技能创建本身不授权修改任何消费方游戏工程。
