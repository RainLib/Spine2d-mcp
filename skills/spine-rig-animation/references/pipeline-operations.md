# MCP Capabilities and Local Extensions

These categories describe implemented capabilities. Always use the **schemas actually discovered on the current connection**. Do not call an unlisted tool merely because its source exists in an updated checkout.

| Capability | Tools or interface | Boundaries |
| --- | --- | --- |
| Source inspection | `skeleton_inspect`, `skeleton_validate`, `mesh_inspect` | Relative JSON paths under the configured root; mesh inspection can also read a job |
| Staging | `stage_json_copy`, `stage_asset_bundle` | JSON only versus JSON plus referenced images; native export requires a complete bundle |
| Weights | `mesh_weights_get`, `mesh_weights_set` | Paged reads and edits of existing bindings; preserve local coordinates; bone names alone cannot define new bindings |
| Geometry | `mesh_replace` | Explicit UVs, triangles, vertices, and hull; no automatic image-to-mesh generation |
| Policies | `job_validate`, `mesh_policy_validate` | Static structure and declarative rules, not complete Spine schema, physics, or visual acceptance |
| Animation | `animation_copy`, `animation_retime`, `bone_keys_set` | Copy does not overwrite a target; retiming/key edits currently support linear/stepped and reject Bezier |
| Native pipeline | `spine_export`, `godot_validate` | Explicitly configured, licensed local Spine and native Spine-enabled Godot; all output remains in staging |

There are no built-in creation tools for bones, IK/Transform/Path/Physics constraint orchestration, skins/slots, automatic meshing, weight smoothing, or complete dynamic validation. A skill description does not create these MCP APIs.

For such requests, first look for a verified Spine editor bridge. Otherwise inspect an existing local generator or use the package's Python extension interface. Verify the target version's schema or official documentation, generate a copy, validate it, and then use native import. Without the required runtime/editor, report the unverified portions; do not fabricate tool calls or silently substitute versions.

## Suggested pipeline

```text
inspect source -> stage_asset_bundle -> job A
mesh/animation edit -> new job B
mesh_inspect + job_validate + project policy
spine_export -> new job C
godot_validate -> new check job D
local full-motion sampling / rendered review when needed
```

Selectors are `(skin, slot, attachment map key)`, not texture paths. Every edit returns a new job. Use the returned ID for subsequent steps instead of modifying the old job or source art. Hand off every texture page referenced by the exported atlas.

The editor version must exactly match the current `spine_export` configuration and asset version. In Spine 4.3, `bone_keys_set` rotate keys use `value`; do not copy another version's `angle` examples. API names may differ across official runtimes, Godot wrappers, and Spine 4.2/4.3. Verify the installed version and source.

## Ordinary Python extensions

Keep character policies and generators in the consuming project, and explicitly register trusted callbacks:

```python
from pathlib import Path
from spine_pipeline_mcp.adapter import ProjectAdapter
from spine_pipeline_mcp.core import Workspace
from spine_pipeline_mcp.pipeline import Pipeline

pipeline = Pipeline(Workspace(Path(source_root), Path(staging_root)))
adapter = ProjectAdapter(pipeline, validators=[local_validator])
result = adapter.transform(parent_job_id, "custom_operation", local_transform, policy)
```

These variables must come from the current task's actual configuration; the example is not a ready-to-run project setup. `local_transform(doc)` returns candidate JSON. A validator receives a copy and returns an object containing a boolean `valid`. A new job is created only after generic structural checks and local checks pass. Calling `Pipeline.transform` directly does not automatically apply project policies; use `ProjectAdapter` when those policies are required.

Callbacks are trusted local Python, not a sandbox. Inspect old scripts for top-level side effects before importing functions, so reuse does not trigger a full character rebuild or overwrite sources. MCP tool arguments do not accept arbitrary script paths. Reusable capabilities may later move into the generic core. Creating this skill alone does not authorize changes to any consuming game project.
