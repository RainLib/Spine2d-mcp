# Architecture and roadmap

## Implemented boundaries

- `src/spine_pipeline_mcp/server.py`: stdio protocol registration with official MCP SDK 2.3.0. Exactly two tools.
- `src/spine_pipeline_mcp/core.py`: explicit source/staging configuration, path checks, 16 MiB bounded JSON read, minimal structure validation and UUID copies.
- `tests/test_core.py`: isolated fixtures plus actual MCP subprocess transport tests.
- `examples/source/minimal.json`: newly authored, synthetic schema-shaped fixture. Not a rendering compatibility test.

The service does not discover local projects or read the entire filesystem. It reads only a requested relative JSON path below a configured root. Tool return values include paths and names; an MCP client will see those values. Choose roots accordingly.

## Planned, not implemented

1. **Validation layer**: typed Spine data models, bone graph cycles, attachment/skin references, weight checks and explicit editor/runtime version profiles.
2. **Transformation layer**: pure functions for animation operations and mesh edits, immutable inputs, diff and provenance manifests.
3. **CLI adapter**: fixed executable and version, argument arrays rather than shell text, timeout, bounded logs, output checks, staging-only imports/exports. No generic command-execution tool.
4. **Preview adapter**: matching runtime/engine render tests for mesh continuity, deformation and transitions. Separate static checks from visual evidence.
5. **Publication step**: separate explicit operation with output diff, destination policy, backups and user authorization. Never an implicit side effect of preview or validation.

Game-specific adapters should describe roots, asset conventions, required versions and validators. They must not bake private project paths into the reusable core. A legacy export script that writes straight to production directories cannot be exposed as an MCP tool unchanged.

## Current limits

Validation checks skeleton/bones shape, animation container type, duplicate names and absent parents. It does not validate full format semantics, constraints, cycle-free hierarchy, mesh topology, weights, atlas references or version compatibility. `.spine` binaries are unsupported. Staging preserves only the selected JSON; it is not a complete movable asset bundle.

The path checks are a boundary for normal requests, not a race-proof defense against malicious local processes. Memory/CPU use from parsing is bounded indirectly by the byte limit, not a process quota. Disk quota/retention and cancellation/timeouts for future long-running jobs remain roadmap work.
