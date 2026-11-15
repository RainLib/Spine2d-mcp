import os
from pathlib import Path
from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from .core import Workspace
from .pipeline import Pipeline
from .validation import validate_document
from .animation import copy_animation, retime_animation, set_bone_keys
from .godot_check import validate_export

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
