---
name: spine-game-integration
description: "Integrate Spine 2D characters into a user-specified game runtime, including slots, attachments, bone sockets, skins, equipment combinations, animation events, and asset validation. Use for Spine-to-game integration without assuming game directories, character names, or combat rules."
---

# Spine Game Integration and Skins

Integrate Spine according to the current task's game contract, delivering reproducible assets and runtime behavior. This skill provides generic methods. Creating or installing it does not connect to, scan, or modify a particular game. Inspect a consuming project's code and configuration only when the user specifies that integration target.

## Establish the integration contract

Confirm the target engine, Spine runtime/wrapper versions, resource entry points, animation-state mapping, time source, pause behavior, existing skin/equipment APIs, and ownership of game events. Do not generalize every engine's API from one example or copy another project's absolute paths, bone/slot names, or budgets.

Determine whether the task is an asset handoff, preview integration, or production replacement. Work within the existing authorization. The generic MCP creates staging jobs and has no automatic game-publication tool. For an asset-preparation task, deliver the package and contract without modifying the consuming project.

## Slots, sockets, skins, and equipment

Read [slot and skin contracts](references/slots-skins.md). Distinguish drawing slots, skin placeholders, actual attachments, texture paths, and bones/points used for position tracking. A slot has no transform of its own and cannot directly serve as a world-space socket.

Define stable sockets from the user's required effects, then map them to actual bones/points and names. Verify that origins remain aligned after scaling, mirroring, animation blending, phase changes, and skin changes. Check defaults, switching, and restoration for prop grips, mouth states, and other mutually exclusive attachments.

Skin changes must cover selecting the skin, restoring default slot attachments, reapplying the current animation, and restoring manually selected attachments, using the target version's API. Equipment composition must preserve dependent bones/constraints and resolve placeholder conflicts, not merely combine texture paths. Follow the game's existing behavior for missing resources. If a wrapper is a no-op, fix it or use a working entry point; a call returning without an error does not prove success.

## Animation and game effects

Map idle, movement, ability phases, hit reactions, cancellation, and exit behavior from the existing state machine instead of redefining combat timing. Identify event sources, trigger times, and duplicate handling. Keep presentation events separate from authoritative game resolution. If the game model applies damage, a Spine event must not apply it again; an explicitly event-driven design still needs one authoritative resolution source.

Character animation, separate effects, and collision/hit regions have distinct contracts. Use [runtime validation](references/runtime-validation.md) to check time advancement, events, sockets, and resources. If rigging or animation changes are needed, use `spine-rig-animation` when installed; otherwise perform the necessary work using available tools and runtime documentation.

## Complete the delivery

Package the actual exported JSON/binary, atlas, and every texture page, with consistent versions and relative paths. Include the native project and art handoff when editable sources are required, keeping authoring sources separate from runtime assets according to the consuming project's packaging rules.

Validate the actual resources from a clean import cache or an isolated directory. For the requested scope, check initial loading, state transitions, skins/equipment, pause/resume, object reuse, and required events. Retain source hashes and runtime reports. Distinguish static validation, native loading, and complete behavioral/visual acceptance. A preview screenshot does not establish combat correctness, device performance, or replay correctness.
