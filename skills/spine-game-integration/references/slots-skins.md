# Slot、Skin 与游戏接口

## 明确名称与职责

| 概念 | 作用与需要记录的契约 |
| --- | --- |
| bone | 变换与层级；挂点追踪读取对应变换 |
| slot | 绑定在骨骼上的绘制容器；同一时刻显示一个 attachment 或不显示 |
| attachment key／skin placeholder | 通过 skin 查找附件的稳定键；不一定等于实际附件名 |
| 实际 attachment | region／mesh／point／boundingbox 等具体资源及数据 |
| texture path | 纹理查找路径，不能代替 slot 或 attachment 选择器 |
| 游戏 socket | 游戏定义的接口，映射到 bone、point 或包装层实际支持的位置来源 |

slot 是绘制与附件管理概念，自身没有位置；绘制顺序不等同于骨骼层级。依据 [Spine Slots](https://esotericsoftware.com/spine-slots)。空 slot 可以作为约定保留，但挂点世界坐标仍需由真实骨骼／point 计算。

用小型映射表记录消费方需要的名字，例如“施法出口 → 某骨骼”“主手 → 某 slot／placeholder”；名称来自任务，不预设 `fx_cast` 或 `weapon` 必须存在。每个需要的 skin 都检查映射，骨骼前缀变化不能让游戏继续绑定旧骨。

## 换肤

读取实际 skin 清单与默认 skin 回退；不要把未找到新附件后显示旧附件误判为换肤成功。Spine skin 可以关联附件、专用骨骼及约束；已有或新组合的皮肤要保留这些依赖。参考 [Spine Skins](https://esotericsoftware.com/spine-skins)。

通常需要按这个语义顺序更新：选择目标／组合 skin → 恢复 slot 默认附件 → 重新应用当前动画 → 恢复游戏手动指定的附件。方法名因运行时及包装层版本变化而异；先查当前源码／官方接口，不将示例方法名作为跨版本保证。来源：[Runtime Skins](https://esotericsoftware.com/spine-runtime-skins)。

检查切换时机：动画时间是否应延续、过渡是否需要遮挡、切换当帧是否闪出默认姿态、物理是否重置、挂点是否重绑。只在切换需要时更新，避免每帧恢复 setup pose 抹掉动画或装备状态。

## 装备与互斥状态

先确认消费方表示装备的方式：单 slot 换附件、组合 skin、独立骨架或额外游戏节点。双持、双手、主副手、施法和空手等只在用户任务需要时实现，沿用已有冲突和隐藏规则。

同一个 slot 的嘴部／道具状态应互斥并可恢复默认。若动画关键帧会覆盖游戏设置的附件，明确由哪层最终决定，测试混合窗口与取消恢复。避免用另加一个同时可见 slot 掩盖错误的切换逻辑。

linked mesh 可共享几何和 Deform 依赖；不能为不同外形的装备随意复用。当前通用 mesh 编辑工具拒绝 linked mesh 文档，不可删除 parent／deform 字段绕过它。使用真正支持该依赖的工具或显式本地实现，并重新验证动画。

目前通用 MCP 没有 skin、slot 或 constraint 创建工具。已存在的数据可检查和交接；需要新增时发现可用编辑器桥接，或通过目标版本的本地 Python 生成器与 `ProjectAdapter` 完成，不能编造 `skin_create` 等已实现 API。
