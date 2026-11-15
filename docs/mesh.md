# Mesh operations and local extensions

The public package provides geometry/weight operations, declarative checks and staging. Project adapters own character layouts, art policies, generators and integration paths. Both MCP clients and ordinary Python scripts use the same functions. No project script is imported automatically.

## MCP workflow

```text
mesh_inspect(relative_path="weighted-mesh.json")
stage_json_copy(relative_path="weighted-mesh.json") -> A
mesh_weights_get(job_id=A, skin="default", slot="art", attachment="body", limit=10)
mesh_weights_set(job_id=A, skin="default", slot="art", attachment="body",
  updates=[{"vertex":0,"weights":{"head":1}}]) -> B
mesh_inspect(job_id=B)
mesh_policy_validate(job_id=B, policy=...)
```

Use `stage_asset_bundle` instead of `stage_json_copy` when the next step is native export: it copies the referenced images into the job. Native export cannot recover images from a JSON-only job. All edits make a new job and preserve the source and parent job. Inspect accepts exactly one `relative_path` or `job_id`.

The [synthetic fixture](../examples/source/weighted-mesh.json) works for JSON-only operations. It has no texture file and is not a native rendering fixture.

## Selectors, geometry and weights

All selectors are exact `(skin, slot, attachment)` map keys, including for legacy skin objects. Attachment texture paths and display names are not selectors. Inventory includes inactive skins and alternate attachments; total mesh count is not simultaneous visible mesh count.

`mesh_weights_get` returns at most 256 vertices per call (`offset` starts at zero), including UVs, named bones, bone-local bind x/y and weights. Unweighted vertices are reported as one influence from their slot bone. `mesh_weights_set` accepts a nonempty update array:

```json
[{"vertex": 0, "weights": {"head": 8, "root": 2}}]
```

This **replaces** that vertex's weights: omitted or zero influences are removed; positive weights are normalized. Every row in the selected mesh is sorted by skeleton bone index for native importer consistency. Unselected vertices retain their weights and bind coordinates, although their packed influence order can change; other attachments are unchanged. The named bones must already bind that vertex. Their bind x/y is retained, so this is not bind-pose compensation. A face can become rigid by retaining only its existing head influence; a garment can exclude an existing arm influence. Motion may still reach it through parents or constraints.

`mesh_replace` accepts a `geometry` object containing `uvs`, `triangles`, `vertices`, `hull`, and optionally `edges`. It retains image path, dimensions and other attachment metadata. UVs and vertices must have matching counts; triangles use vertex indices; hull vertices must come first in boundary order. Optional nonessential edges use even coordinate offsets (`2 * vertex index`). Omitted edges remove old edge metadata. Replacement requires one continuous indexed surface, exactly one boundary loop and a declared hull on that boundary. Geometry with holes is currently rejected for replacement. It does not check geometric overlap/self-intersection or reconstruct image contours.

Weighted `vertices` encode, per vertex, influence count followed by bone index, bone-local bind x, bind y, weight for each influence. This follows the [Spine JSON mesh format](https://esotericsoftware.com/spine-json-format#Attachments). `pack_vertices(rows, bones)` lets a local generator supply named `{bone,x,y,weight}` influences and performs normalization/ordering. No engine transform solver is included; the local generator supplies correct bind coordinates for new bones.

Editing requires Spine 4.3.x. Documents with linked meshes, sequences, or deform/FFD/attachment animation timelines are rejected conservatively, even if a dependency is on another mesh. Ordinary slot attachment-switch timelines remain supported. Changing influence order/count without remapping deform offsets would invalidate animation data. Inspection can still report these documents; linked topology is explicitly unresolved.

## Declarative policies

```json
{
  "rules": [{
    "skin": "default", "slot": "art", "attachment": "body",
    "continuous": true, "max_vertices": 480, "max_influences": 4,
    "regions": [
      {"name": "face", "vertices": [0], "rigid_bone": "head"},
      {"name": "cape", "vertices": [2, 3],
       "allowed_bones": ["root", "head"], "forbidden_ancestors": ["arm"]}
    ]
  }]
}
```

Vertex selections are explicit and belong to that topology/version; regenerate them after remeshing. Missing selectors, unknown bones and invalid regions fail instead of silently skipping checks. Any positive forbidden weight is a violation. An ancestor exclusion includes the named bone itself, detecting a cloth bone parented under an arm even when direct arm weights are zero. Budgets are per selected attachment, not a simultaneous visibility estimate.

`continuous` checks triangle edge connectivity, unused vertices, degenerate/duplicate triangles, vertex fans, manifold edges and shared-edge winding in UV space. Point-only connections fail. A surface with a hole can still be continuous; boundary loops and hull consistency are separate diagnostics. Static passing does not prove preserved artwork, rigid-looking faces, stable feet, correct constraints, no animated folds or suitable mobile performance.

## Local Python extension

```python
from pathlib import Path
from spine_pipeline_mcp.adapter import ProjectAdapter
from spine_pipeline_mcp.core import Workspace
from spine_pipeline_mcp.pipeline import Pipeline
from spine_pipeline_mcp.mesh import replace_mesh

def project_check(doc):
    missing = sorted({"idle"} - doc.get("animations", {}).keys())
    return {"valid": not missing, "missing_animations": missing}

pipeline = Pipeline(Workspace(Path("/path/to/source"), Path("/path/to/separate-staging")))
adapter = ProjectAdapter(pipeline, validators=[project_check])

# geometry comes from the project's existing contour/grid/rig generator.
result = adapter.transform(job_id, "local_contour_rebuild",
    lambda doc: replace_mesh(doc, "default", "art", "body", geometry),
    policy={"rules": [{"skin": "default", "slot": "art", "attachment": "body", "continuous": True}]})
```

Callbacks are explicitly registered trusted Python with normal process privileges. They receive document copies; a validator returns an object with a boolean `valid`. Invalid output, exceptions and rejected project checks prevent a new job. Successful results return both the standard parent/job/hash manifest and check reports. Persist the returned reports with your private evidence if needed. The MCP server has no tool to load arbitrary Python files or shell commands.

Install this repository as an editable dependency in your local environment for development, or pin a released package/commit for reproducibility. Keep local scripts in the game repository. Generic improvements can then be contributed upstream independently of project-specific assets and rules.

Existing alpha-island/contour extraction, constrained triangulation, automatic bone placement, weight smoothing, full motion sampling and rendered previews can stay local and feed this interface. They have **not** become built-in tools in this change. Native export and Godot load/sample remain independent subsequent jobs; publishing into the game is a separate project action.
