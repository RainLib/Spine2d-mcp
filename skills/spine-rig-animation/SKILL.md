---
name: spine-rig-animation
description: "Create or adjust Spine 2D skeletons, meshes, weights, animation, and secondary motion. Reuse spine-pipeline-mcp staging, editing, and validation tools, with explicit local extensions for missing operations. Use for character rigging, deformation, and motion-quality tasks."
---

# Spine Rigging and Animation

Turn confirmed artwork and motion requirements into editable Spine projects and validated runtime assets. Derive skeleton structure, part counts, animation names, and budgets from the current task rather than importing another game's character rules.

## Establish capabilities and inputs

Inspect the existing Spine JSON/project version, asset handoff record, and target runtime. Discover the current session's MCP tools and read their schemas; source code existing on disk does not mean the connection has refreshed. Choose supported operations using [MCP capabilities and local extensions](references/pipeline-operations.md).

When more layering or alignment work is needed, use `spine-asset-prep` if installed. Otherwise inspect the existing project and handoff record directly. An animation-only adjustment does not require regenerating or splitting the artwork.

Separate source files from staging. Stage the JSON and every referenced image before native export. Complete reversible edits and validation within the user's existing authorization; do not add a new approval step for every operation.

## Skeletons, meshes, and weights

Define the roles of the root, character displacement, body controls, limb chains, appendages, and sockets. Parenting must meet motion-isolation requirements, and constraint targets, order, and skin dependencies must resolve. Adding or reordering bones also requires updating index references; editing only the `bones` array is insufficient.

Choose a continuous body and any necessary separate surfaces according to appearance and motion range, preserving correct occlusion. Mesh density should support joint bending and silhouettes. Avoid unused transparent triangles and thin triangles prone to inversion. Measure cost using actual vertices, influences, and simultaneously visible attachments, not total attachment count.

Constrain influences where faces, shells, or props need rigidity, while retaining limited transitions at flexible joints. For isolated regions such as capes, inspect direct weights, ancestors, constraints, and Deform together. Weights Lock does not provide animation isolation or bind compensation.

See [mesh and weight operations](references/mesh-weights.md) for checks and editing limits. Implement and verify missing algorithms through explicit local extensions. Do not hard-code character names in the core or bypass rejection rules in ways that silently corrupt Deform or linked meshes.

## Animation and physics requirements

Extract observable criteria from the user's description and game contract: readable motion, aligned contact points, credible support, preserved silhouettes, usable transitions, and recovery after cancellation. Create only the requested idle, movement, anticipation, release, recovery, hit, exit, or phase animations, using existing naming interfaces.

Animation must drive the actual skeleton and attachments. Use real Spine playback for dynamic previews. Camera pans, zooms, and static images do not establish rigging, physics, or loop quality. Sample complete animations, critical contacts, and transitions; inspect mesh inversion, foot sliding, facial distortion, socket drift, and loop discontinuities.

For hair, cloth, tails, or other secondary motion, read [motion and physics validation](references/motion-physics.md). Choose runtime physics or authored deterministic motion according to the target. Do not describe a sine-wave oscillation or ordinary keyframes as implemented Spine Physics.

## Deliverables and validation levels

Preserve an editable `.spine` project when native import/save is available, plus JSON, every atlas page, textures, and motion previews. Bind reports to the actual output hashes and editor/runtime versions.

Distinguish structural checks, native import, runtime loading, complete motion sampling, and visual review. `godot_validate` only loads and briefly samples an isolated project; it does not automatically validate motion quality or game behavior. Without native tools, complete the executable portions and identify unverified results. Valid JSON alone does not establish a finished production asset.

For subsequent sockets, skins, or equipment integration, use `spine-game-integration` if available and hand off the actual animation, skin, slot, and attachment contracts.
