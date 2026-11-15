# Slots, Skins, and Game Interfaces

## Distinguish names and responsibilities

| Concept | Role and contract to record |
| --- | --- |
| bone | Transform and hierarchy; socket tracking reads the relevant transform |
| slot | Drawing container attached to a bone; displays one attachment or none at a time |
| attachment key / skin placeholder | Stable key for skin lookup; may differ from the actual attachment name |
| actual attachment | A concrete region, mesh, point, bounding box, or other resource and its data |
| texture path | Texture lookup path; not a substitute for a slot or attachment selector |
| game socket | A game-defined interface mapped to a bone, point, or position source supported by the wrapper |

A slot manages drawing and attachments; it has no position of its own. Draw order is separate from bone hierarchy. See [Spine Slots](https://esotericsoftware.com/spine-slots). An empty slot may reserve a convention, but a socket's world position still needs a real bone/point transform.

Record consuming names in a small mapping, such as "cast origin -> selected bone" or "main hand -> selected slot/placeholder." Names come from the task; do not assume `fx_cast` or `weapon` must exist. Check mappings for every required skin. A changed bone prefix must not leave the game bound to an old bone.

## Change skins

Inspect the actual skin inventory and default-skin fallback. An old attachment remaining visible after a failed lookup is not a successful skin change. Spine skins can include attachments, dedicated bones, and constraints; preserve those dependencies in existing or newly composed skins. See [Spine Skins](https://esotericsoftware.com/spine-skins).

The usual semantic sequence is: select the target/composed skin, restore default slot attachments, reapply the current animation, then restore attachments manually selected by the game. Method names vary across runtime and wrapper versions. Inspect the current source or official API rather than treating example names as a compatibility guarantee. See [Runtime Skins](https://esotericsoftware.com/spine-runtime-skins).

Check switching behavior: whether animation time continues, transitions need occlusion, the setup pose flashes on the switching frame, physics resets, or sockets need rebinding. Update when a change requires it; restoring the setup pose every frame can erase animation or equipment state.

## Equipment and mutually exclusive states

Identify the consuming project's equipment representation: attachment changes in one slot, composed skins, separate skeletons, or additional game nodes. Implement dual wielding, two-handed use, main/off-hand, casting, or empty-hand states only when requested, following existing conflict and visibility rules.

Mouth/prop states within a slot should be mutually exclusive and restore the default correctly. If animation keys override game-selected attachments, establish which layer has final authority and test blend windows and cancellation recovery. Do not hide incorrect switching logic by adding another simultaneously visible slot.

Linked meshes may share geometry and Deform dependencies; they cannot be arbitrarily reused for equipment with different shapes. The generic mesh tools currently reject linked-mesh documents. Do not remove `parent` or deform fields to bypass this restriction. Use a tool or explicit local implementation that supports those dependencies, then revalidate the animation.

The generic MCP currently has no skin, slot, or constraint creation tools. Existing data can be inspected and handed off. For additions, discover a working editor bridge or use a local generator for the target version with `ProjectAdapter`. Do not invent implemented APIs such as `skin_create`.
