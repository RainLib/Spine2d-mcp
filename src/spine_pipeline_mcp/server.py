import os
from pathlib import Path
from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from .core import Workspace
from .pipeline import Pipeline
from .validation import validate_document
from .animation import copy_animation, retime_animation, set_bone_keys
from .godot_check import validate_export
from .mesh import inspect_meshes, get_weights, set_weights, replace_mesh
from .mesh_policy import validate_mesh_policy

mcp = MCPServer("Spine Pipeline MCP")


def workspace():
    source = os.environ.get("SPINE_MCP_SOURCE_ROOT")
    staging = os.environ.get("SPINE_MCP_STAGING_ROOT")
    if not source or not staging:
        raise ValueError("Set SPINE_MCP_SOURCE_ROOT and SPINE_MCP_STAGING_ROOT explicitly")
    return Workspace(Path(source), Path(staging))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
def skeleton_inspect(relative_path: str) -> dict:
    """Inspect a Spine JSON in the configured read-only root; basic checks, not full validation."""
    return workspace().inspect(relative_path)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def stage_json_copy(relative_path: str) -> dict:
    """Copy one Spine JSON into a new isolated staging job. Never changes the source."""
    return workspace().stage(relative_path)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
def skeleton_validate(relative_path: str) -> dict:
    """Statically check bone references, mesh topology/weights and timeline times. Not a visual guarantee."""
    _, doc = workspace().read(relative_path)
    return validate_document(doc)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def stage_asset_bundle(relative_path: str) -> dict:
    """Create an isolated JSON + referenced image bundle. No source writes. No audio/sequences."""
    return Pipeline(workspace()).stage_bundle(relative_path)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
def job_validate(job_id: str) -> dict:
    """Run static structural checks against a staged job, without changing it."""
    _, doc = Pipeline(workspace()).read_job(job_id)
    return validate_document(doc)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
def mesh_inspect(relative_path: str = "", job_id: str = "") -> dict:
    """Inventory skins/meshes, topology, continuity and weights. Supply exactly one source path or job ID. Static only."""
    if bool(relative_path) == bool(job_id):
        raise ValueError("Supply exactly one relative_path or job_id")
    if job_id:
        _, doc = Pipeline(workspace()).read_job(job_id)
    else:
        _, doc = workspace().read(relative_path)
    return inspect_meshes(doc)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
def mesh_weights_get(job_id: str, skin: str, slot: str, attachment: str, offset: int = 0, limit: int = 100) -> dict:
    """Read up to 256 vertices with named bones, bone-local bind coordinates and weights from a staged mesh."""
    _, doc = Pipeline(workspace()).read_job(job_id)
    return get_weights(doc, skin, slot, attachment, offset, limit)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def mesh_weights_set(job_id: str, skin: str, slot: str, attachment: str, updates: list[dict]) -> dict:
    """NEW job: updates=[{vertex:0,weights:{bone:1}}]. Replace existing bindings' weights, normalize/sort; retain bind x/y. Spine 4.3 only; no deform/linked meshes. Does not preserve pose."""
    return Pipeline(workspace()).transform(job_id, "mesh_weights_set",
        lambda doc: set_weights(doc, skin, slot, attachment, updates))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def mesh_replace(job_id: str, skin: str, slot: str, attachment: str, geometry: dict) -> dict:
    """NEW job: replace uvs/triangles/vertices/hull (optional edges), preserving texture. Continuous geometry only; Spine 4.3; no deform/linked meshes. Weighted vertices need explicit bind coordinates."""
    return Pipeline(workspace()).transform(job_id, "mesh_replace",
        lambda doc: replace_mesh(doc, skin, slot, attachment, geometry))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
def mesh_policy_validate(job_id: str, policy: dict) -> dict:
    """Check {rules:[{skin,slot,attachment,continuous?,max_vertices?,max_influences?,regions?}]}. Regions use vertices plus allowed_bones/rigid_bone/forbidden_ancestors. Static only."""
    _, doc = Pipeline(workspace()).read_job(job_id)
    return validate_mesh_policy(doc, policy)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def animation_copy(job_id: str, source: str, target: str) -> dict:
    """Copy an existing animation to a new name in a NEW staging job; refuses name collisions."""
    return Pipeline(workspace()).transform(job_id, "animation_copy", lambda doc: copy_animation(doc, source, target))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def animation_retime(job_id: str, animation: str, speed: float) -> dict:
    """Return a new job with animation times divided by positive speed. Only linear/stepped; rejects Bezier."""
    return Pipeline(workspace()).transform(job_id, "animation_retime", lambda doc: retime_animation(doc, animation, speed))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def bone_keys_set(job_id: str, animation: str, bone: str, timeline: str, keys: list[dict]) -> dict:
    """Replace one rotate/translate/scale timeline in a NEW job. Spine 4.3 rotate uses value. Linear/stepped only."""
    return Pipeline(workspace()).transform(job_id, "bone_keys_set", lambda doc: set_bone_keys(doc, animation, bone, timeline, keys))


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def spine_export(job_id: str) -> dict:
    """Run explicitly configured licensed Spine CLI on another copy; produce project/JSON/atlas/PNG. Staging only."""
    return Pipeline(workspace()).export(job_id)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
def godot_validate(job_id: str) -> dict:
    """Use configured native Spine-enabled Godot in an isolated project. Runtime load/sample, not visual approval."""
    return validate_export(Pipeline(workspace()), job_id)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
