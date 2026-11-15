# Animation and Secondary Motion

## Define motion through observable outcomes

Extract relevant checkpoints from the task instead of applying a fixed animation list. Examples include mouth/effect-origin alignment on release, limited sliding of the supporting foot, attacks that do not pull unrelated cloth, recovery that transitions into idle, and continuous loop velocity and silhouette. Existing attack timing, states, and events follow the consuming game's contract.

Distinguish global character displacement, motion within the skeleton, and camera movement. Check isolated playback, blended transitions, hit reactions/cancellation, death overrides, skin changes, and playback speed changes. Avoid two tracks applying the same global displacement. Inspect velocity discontinuities and accumulated drift in addition to comparing loop endpoints.

Native sampling should cover the start, contact/release, motion extremes, end, and important blend windows. Advance long animations and continuous physics sequentially. Choose sampling density according to speed and deformation risk rather than treating one game's frame count as universal. Compare triangle areas/winding with the bind pose to detect inversion and severe degeneration, and visually inspect facial proportions, occlusion, and foot positions.

## Choose the appropriate physics behavior

Determine whether the user needs native physics constraints, authored animation, or game physics. Spine Physics supplies secondary bone motion; it does not establish game collision, damage, or network synchronization. Confirm that the actual Spine version, licensed features, and runtime API support the required constraints. The generic MCP currently has no dedicated physics-creation or tuning tool.

When physics is needed, configure constraints through a verified editor interface or a generator for the target version. Check affected bones, constraint order, permitted transforms, strength, damping, inertia, mass, gravity/wind, mix, and reference scale. Available fields depend on the version. See [Spine Physics constraints](https://esotericsoftware.com/spine-physics-constraints) and [constraint evaluation order](https://esotericsoftware.com/spine-constraints).

An exported `physics` field does not prove correct motion, and a preset oscillation curve is not a passed physics test. Label ordinary keyframes as authored secondary motion. When native physics is explicitly required, ordinary oscillation must not silently replace the acceptance criterion.

Do not assume the editor offers a one-click command to bake Physics into keyframes. For reproducible sampling or custom reconstruction, first verify actual tool support and the required result. Record the method, time step, and error. Do not describe custom sampling as use of a native baking feature.

## Validate using the same simulation history

Physics depends on prior state. Advance frame by frame from consistent initialization/reset conditions before comparing preview and runtime. A single frame reached by an arbitrary seek is not a substitute for continuous simulation. Establish the behaviors relevant to the target project:

- How spawning/reuse, teleporting, turning, scaling, and phase changes reset or preserve secondary motion.
- Whether `delta=0`, resume, speed changes, and frame-rate changes cause jumps, unstable oscillation, or accumulated drift.
- Whether hit/cancel/death blends and constraint mix recover, and repeated loops remain stable.
- Whether wind, gravity, collision appearance, and bone chains behave as intended after mirroring or equipment changes.
- Whether replay or determinism requirements use matching inputs, time steps, and reset history rather than one similar-looking frame.

These are behaviors to verify when relevant, not features every project must enable. Do not promise inherently identical physics across machines, versions, or time steps.

`godot_validate` currently loads and briefly samples animation. It does not cover the Physics behaviors above, complete deformation, or visual review. Use a controlled preview/sampler in the actual native runtime when full validation is needed, and bind reports to exported JSON, atlas, and image hashes. State the separate coverage of screenshots, motion videos, and numerical checks.
