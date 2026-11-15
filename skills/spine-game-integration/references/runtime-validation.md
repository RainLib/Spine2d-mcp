# Runtime Assets and Behavior Validation

## Complete the resource pipeline

Confirm compatibility between the exported JSON/binary version and the actual runtime. The current `spine_export` requires an exact match with the configured Spine editor version. Godot scenes require a build that actually includes native Spine classes; a stock Godot installation does not establish that capability.

Inventory the atlas and **every** texture page from the export results. Do not assume a single page or fixed filenames. Check relative paths, case sensitivity, skin/slot/animation names, and resource references. Refresh caches according to the engine's actual import rules, and verify that imported content hashes correspond to the current sources. Matching filenames alone do not prove an update.

`godot_validate` loads and briefly samples an isolated project without the consuming game's autoloads. It is a generic loading check, not validation of game states, complete physics, pixel coverage, mobile performance, hit detection, or network replay. Use the target project's existing tests or an isolated scene created for the task to verify those behaviors.

## Time, events, and sockets

Identify what advances skeleton time: automatic engine updates, a shared game clock, or a replay clock. Avoid enabling automatic and manual updates simultaneously. Check `delta=0`, playback speed, pause/resume, and object reactivation. Physics needs consistent state history and reset behavior.

Check the items relevant to the task:

- Correct default skins, attachments, and initial state.
- No stale tracks, attachments, or particles after state changes, blends, cancellation, or death.
- Anticipation, release/contact, and recovery timing agree with the existing authority; repeated playback/callbacks do not resolve the same action twice.
- Effect origins, handheld props, and contact points stay aligned through character transforms, mirroring, and skin changes.
- Mutually exclusive attachments show only the intended state; missing equipment follows the specified hide, fallback, or error behavior.
- Character reuse, scene exit, and resource disposal clear temporary state and subscriptions.

If collision is in scope, Spine bounding-box data can be an input, but actual detection and event consumption still follow the game contract. Do not automatically turn visible mesh triangles into a new damage authority.

## Evidence and delivery

Reports should identify the versions and resource hashes used, together with checks actually performed. Dynamic previews must come from the real Spine runtime. Use continuous sampling for physics and contact issues, not staged still images. A passing result covers the executed checks; one successful load does not establish correctness of every animation or skin.

Choose performance metrics according to the target device and task budget: visible vertices, influence counts, texture memory, draw calls, load time, or other relevant measures. Desktop previews do not replace mobile testing. Clearly mark required project/device checks that were not executed.

Keep source projects, runtime packages, previews, and reports traceably related. Perform production replacement only within the user's existing authorization and task scope. If replacement is not requested, deliver an inspectable handoff package without publishing or modifying runtime resources.
