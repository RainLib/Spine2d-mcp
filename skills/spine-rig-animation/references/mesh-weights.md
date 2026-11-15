# Mesh and Weight Operations

## Inspection

Identify the target from the actual skin/slot/attachment inventory. Inspect UVs, triangles, weighted vertices, and bone indices. Check edge connectivity, unused vertices, duplicate or degenerate triangles, nonmanifold edges/vertex fans, and winding. Two triangle fans touching only at a point do not form a continuous surface.

Total attachment counts include different skins and mutually exclusive states; multiple attachments do not prove that the body is fragmented. Continuity is a topological property and does not prove complete artwork coverage, deformation without folds, or correct occlusion. Derive mesh budgets from the task's display size and performance target, not another game's numbers.

## Edit existing bindings

`mesh_weights_get` returns at most 256 vertices per page, including UVs, bone names, bone-local bind coordinates, and weights.

```json
[{"vertex": 12, "weights": {"head": 1}}]
```

Updates passed to `mesh_weights_set` **replace** the vertex's influence set: omitted influences and zero weights are removed, and positive weights are normalized. Select only bones already bound to that vertex. New bindings require explicit local-coordinate calculations. Preserving bind x/y does not guarantee an unchanged current pose.

The package sorts **every vertex's influence list** in the edited attachment by bone index. Unselected vertices retain their weights and bind coordinates. Native import has failed when only edited rows were sorted and the remaining rows used inconsistent ordering, so local extensions must keep influence ordering consistent across the attachment. Do not directly reorder data with Deform dependencies.

## Replace geometry and rebind

`mesh_replace` requires `uvs`, `triangles`, `vertices`, and `hull`, with optional `edges`. It preserves the existing attachment's texture and other metadata. Hull vertices come first; triangles use vertex indices; this tool's nonessential edges use coordinate offsets of `2 * vertex_index`. Omitting edges clears the old edge metadata.

Replacement currently accepts one continuous surface with one boundary loop. Meshes with holes or multiple pieces require a local generation/validation workflow that explicitly supports them; do not silently fill holes or discard parts. The tool does not detect geometric self-intersection or automatically extract contours from PNGs.

Each weighted vertex encodes an influence count followed by bone index, bone-local x/y, and weight for each influence. `pack_vertices` can encode named influences. Compute new bind coordinates using the inverse of the actual bone world transform. Do not write image pixels, slot coordinates, or world coordinates directly as bone-local coordinates. See [Spine JSON attachments](https://esotericsoftware.com/spine-json-format#Attachments).

Mesh editing currently supports Spine 4.3.x only. It rejects documents containing linked meshes, image sequences, or Deform/FFD/attachments animation timelines. Ordinary attachment-switch timelines under `slots` remain supported. Do not delete rejected timelines merely to pass validation. Editing a dependent mesh requires an actual editor or implementation that supports dependency remapping, followed by validation. Otherwise preserve the original data and identify the missing capability.

### When local Deform migration is required

This is not a built-in feature, and registering a `ProjectAdapter` callback does not establish that migration is implemented. First inspect dependency handling in the target version's actual loader. [Spine Deform timelines](https://esotericsoftware.com/spine-json-format#Deform-timeline) provide conceptual guidance; confirm paths and fields against the target version.

- Inventory all skins, linked meshes, animations, and timelines referencing the mesh. Save complete inputs and hashes. Select vertices from an explicit region of the current topology instead of guessing which indices represent the face.
- Decode sparse frame `offset` values, omitted entries, and zero deltas according to that version. Distinguish unweighted coordinate pairs from the per-influence delta layout of weighted meshes. Do not truncate weighted Deform arrays using the UV vertex count.
- Map old vertices and bone influences to new records before migrating every affected frame. Handle reordered, removed, and added influences and topology changes explicitly. Removing influences while keeping old array offsets corrupts the mapping. When deformation must be preserved, also account for changed weights and local-coordinate transforms.
- Test sparse frames, zero frames, reordering, influence removal, and linked dependencies on synthetic samples, then compare native output frame by frame using the same playback history. Unselected vertices and unrelated animations must retain their effects without shifted records, missing frames, or disappearing content. The task defines acceptable changes to selected vertices.

Rebinding may prevent selected vertices from exactly reproducing their former multi-bone motion. Explain the tradeoff between making a binding rigid and preserving every previous pose. If the target is unattainable, preserve the source and report the specific limitation. A successful migrator or static check does not prove preserved animation without native import and animation regression checks.

## Region policies

`mesh_policy_validate` takes caller-defined rules such as `continuous`, `max_vertices`, `max_influences`, and explicit vertex regions with `rigid_bone`, `allowed_bones`, or `forbidden_ancestors`.

Facial rigidity, cape isolation from direct weights, and ancestor isolation express different requirements. A hem can still follow an arm when its bones descend from the arm, even with zero direct arm weights. Constraints and Deform can add further motion.

Region selections depend on the current topology. Rebuild selections after remeshing and bind them to the current JSON hash; do not reuse old vertex indices on a new mesh. After smoothing weights or reducing influences, recheck protected regions, boundaries, and extreme poses.
