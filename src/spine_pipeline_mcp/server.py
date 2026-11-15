import os
from pathlib import Path
from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from .core import Workspace

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


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
