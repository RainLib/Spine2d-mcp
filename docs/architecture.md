# Architecture

## Implemented layers

- `server.py`: 15 stdio tools using official MCP SDK 2.3.0.
- `core.py`: bounded source reads and JSON-only staging copies.
- `validation.py`: pure static bone/slot/mesh/weights/time checks, with explicit unsupported-semantic warnings.
- `animation.py`: pure deep-copy animation copy, linear/stepped retime and bone timeline keys. Numeric Bezier curves rejected for retime/key edits.
- `mesh.py`: indexed connectivity/fan/boundary inspection, named weighted-vertex codec, paged reads, immutable weight and explicit geometry edits.
- `mesh_policy.py`: declarative budgets, continuous surfaces, rigid regions, direct-weight and ancestor exclusions.
- `adapter.py`: explicit local Python callbacks plus generic validation/staging. No dynamic discovery/import from assets or MCP tool arguments.
- `pipeline.py`: isolated referenced-image bundles, immutable transformations, configured exact-version CLI import/export on another copy.
- `godot_check.py`: standalone generated project, PNG-first import, native resource load and brief sampling. No game autoloads.

The source root and staging root must not overlap. Jobs have UUID identifiers; arbitrary paths cannot be supplied for native outputs. A tool cannot publish to a game or execute an arbitrary shell command.

## Local adapter boundary

Keep actual project roots, licensed executables, native Godot builds, character policies and smoke-test evidence outside this public repository. An adapter should set `SPINE_MCP_SOURCE_ROOT`, `SPINE_MCP_STAGING_ROOT`, `SPINE_MCP_CLI`, `SPINE_MCP_CLI_VERSION` and `SPINE_MCP_GODOT_EXECUTABLE`. The generic core must not import production build scripts with side effects.

Character-specific requirements such as a continuous body mesh, rigid face/props, cloth isolation, foot stability and loop quality need dedicated checks and visual evidence. Static mesh counts and a successful runtime load do not establish those properties.

`ProjectAdapter` now provides the extension boundary: a local script imports the installed package, registers its own pure document transforms/validators, and calls `transform` to create a new job only after checks pass. Validators receive copies so they cannot mutate the candidate accidentally. Callbacks are trusted local Python with normal process privileges, not a sandbox. Generic tools never load callback paths from asset metadata. [Mesh guide](mesh.md) contains an example. No runtime project assets are imported into this package.

## Planned

- Automatic alpha-contour meshing, weight smoothing, bind-pose compensation and deform remapping.
- Complete Spine schema/version profiles and linked-mesh/sequence/audio handling.
- Full animation deformation sampling, rendered previews and per-game validators.
- Live native-process resource quotas, cleanup policies and cancellation.
- Separately authorized publication with diffs/backups; never implicit in preview.

Native commands currently have timeouts and post-run log-size checks, not a hardened process sandbox or strict live disk quota. Godot's isolated HOME avoids the game's user-data path; Spine uses its normal licensed editor state. No claim of zero editor cache/settings changes is made.
