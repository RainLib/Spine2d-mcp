# 可选编辑器探测与操作

## 探测

使用当前工具目录按 PhotoCraft／Photoshop 的名称和描述发现接口，再读取实际 schema。可以使用 `functions.exec` 中的 `ALL_TOOLS`；其他宿主使用各自的工具发现能力。不要靠工具名猜参数或编造 Photoshop MCP 命令。

PhotoCraft 若暴露 `session_list`，调用它验证只读连通性。空文档列表表示连接正常；`command_list` 返回 `needsDocument=true`、`disabledReason="no document open"` 表示先要打开文档，不表示功能不存在。检查图层与状态能力可查询 `command_list(filter="layerComp")`，并查看实际暴露的 `doc_export_layers`、`doc_inspect` 和预览工具。

Photoshop 若暴露文档列表、应用状态或工具目录，选一项只读调用验证。没有 Photoshop 工具时，只报告“本会话未发现可用 Photoshop MCP”；不要推断用户没有安装 Photoshop。只有连接配置仍不等于实际调用成功。

记录这次使用的应用、接口类型、探测结果和输入／输出作用域。每次任务都重新判断可用性；不要把某台机器的安装状态写成通用默认值。无需为可选编辑器增加强制 `dependencies.tools`。

## PhotoCraft 路径

工具前缀可能随宿主变化，以下为能力名，调用前以实际 schema 为准：

| 工作 | 优先接口及注意点 |
| --- | --- |
| 识别现有文档 | `session_list`；关注文档 ID/index、尺寸与 dirty，不关闭用户未保存的文档 |
| 打开／创建 | `doc_open` 或 `doc_new`；保留返回 index，后续操作显式指定目标 |
| 查看图层 | `doc_inspect`；确认图层 ID、层级、可见性和从上到下的顺序 |
| 图层／遮罩操作 | 先 `command_list` 查命令与参数，再 `command_run`；批量命令不是原子事务，失败时已完成步骤可能仍生效 |
| 放置原图 | 若 `doc_place` 可用，作为可回溯内容放入工作副本；不要猜 Smart Object 能力 |
| 状态组合 | 实际存在时使用 `layerComp.new/list/apply`；核对缺失图层及默认状态 |
| 状态预览 | `doc_render_preview` 或 `render_preview`；图像模式与 bridge 模式的参数不同 |
| 保存 | `doc_save` 指定新路径保存 `.pcraft`；PSD 导出记录兼容警告，合成预览需要实际 composite |
| 分层导出 | `doc_export_layers` 导出顶层图层，组会合并；检查 `files` 和 `skipped` |

文件操作受 MCP 的读写根目录约束。不要将项目相对路径擅自解释为服务器根路径；从返回状态、已知启动配置或一次明确的路径错误确认映射。不要自动扩大访问范围。

默认 `visible_only=true` 会跳过隐藏状态。导出互斥状态时，按已确认的图层组合逐次导出，或在隔离导出副本中明确选择图层，避免把参考层一并输出。不要以为一次默认导出已经包括闭口和张口两种状态。

导出后根据需要重新打开新文件，核对坐标、合成结果、透明边缘与状态。这会改变活动文档，后续必须使用明确的目标 ID；检查结束不要关闭或覆盖用户原先打开的文档。

## Photoshop 路径和无 MCP 回退

复用同一套“检查文档 → 保留可编辑源 → 图层／状态 → 透明素材 → 读回”的结果要求，但从发现的 Photoshop MCP 文档获取命令。不能把 PhotoCraft 的命令 ID 直接发给 Photoshop。

现有工程若有已维护的 Photoshop 导出脚本或官方桥接流程，检查其版本、输出坐标与副作用后使用；不要把未知下载脚本直接作用于当前工程。没有已验证桥接时，继续准备文件、图层计划和 Spine 所需坐标，明确尚未完成的编辑器步骤。仅当缺少原始素材等必要输入时才请求补充，而不是因为可选 MCP 不存在而反复请求确认。
