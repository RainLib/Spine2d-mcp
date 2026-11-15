"""Exercise the bundle's actual UV launcher against synthetic asset copies."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from zipfile import ZipFile

from mcp import Client
from mcp.client.stdio import StdioServerParameters


TOOLS = {
    "skeleton_inspect", "skeleton_validate", "stage_json_copy", "stage_asset_bundle",
    "job_validate", "animation_copy", "animation_retime", "bone_keys_set",
    "spine_export", "godot_validate", "mesh_inspect", "mesh_weights_get",
    "mesh_weights_set", "mesh_replace", "mesh_policy_validate",
}


def payload(result):
    if result.is_error:
        raise AssertionError(result)
    return result.structured_content or json.loads(result.content[0].text)


async def verify(archive_path: Path, expected_sha256: str | None):
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if expected_sha256 and digest != expected_sha256:
        raise ValueError("Downloaded bundle SHA-256 differs from Registry metadata")
    with tempfile.TemporaryDirectory(prefix="spine-mcpb-") as temporary:
        root = Path(temporary).resolve()
        bundle, source, staging = root / "bundle", root / "source", root / "staging"
        with ZipFile(archive_path) as archive:
            for member in archive.infolist():
                path = PurePosixPath(member.filename)
                if path.is_absolute() or ".." in path.parts or "\\" in member.filename:
                    raise ValueError("Unsafe archive path")
                if (member.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError("Archive symlinks are not supported")
            archive.extractall(bundle)
        manifest = json.loads((bundle / "manifest.json").read_text())
        shutil.copytree(Path(__file__).resolve().parents[1] / "examples/source", source)
        original = (source / "weighted-mesh.json").read_bytes()
        substitutions = {"${__dirname}": str(bundle)}
        for key, field in manifest["user_config"].items():
            substitutions[f"${{user_config.{key}}}"] = field.get("default", "")
        substitutions["${user_config.source_root}"] = str(source)
        substitutions["${user_config.staging_root}"] = str(staging)

        def expand(value):
            for key, replacement in substitutions.items():
                value = value.replace(key, replacement)
            if "${" in value:
                raise ValueError(f"Unresolved manifest variable: {value}")
            return value

        config = manifest["server"]["mcp_config"]
        params = StdioServerParameters(
            command=expand(config["command"]),
            args=[expand(arg) for arg in config["args"]],
            env={**os.environ, **{key: expand(value) for key, value in config["env"].items()}},
            cwd=str(root),
        )
        async with Client(params) as client:
            listing = await client.list_tools()
            assert {tool.name for tool in listing.tools} == TOOLS
            payload(await client.call_tool("skeleton_inspect", {"relative_path": "weighted-mesh.json"}))
            meshes = payload(await client.call_tool("mesh_inspect", {"relative_path": "weighted-mesh.json"}))
            assert meshes["meshes"][0]["topology"]["continuous_surface"]
            job = payload(await client.call_tool("stage_json_copy", {"relative_path": "weighted-mesh.json"}))
            selector = {"skin": "default", "slot": "art", "attachment": "body"}
            payload(await client.call_tool("mesh_weights_get", {"job_id": job["job_id"], **selector}))
            edited = payload(await client.call_tool("mesh_weights_set", {
                "job_id": job["job_id"], **selector,
                "updates": [{"vertex": 0, "weights": {"head": 1}}],
            }))
            assert edited["job_id"] != job["job_id"]
            checked = payload(await client.call_tool("job_validate", {"job_id": edited["job_id"]}))
            assert checked["valid"], checked
        assert (source / "weighted-mesh.json").read_bytes() == original
        print(json.dumps({
            "version": manifest["version"], "sha256": digest, "tools": len(TOOLS),
            "mesh_edit": "passed", "source_unchanged": True,
        }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--sha256", help="Expected SHA-256 from Registry metadata")
    args = parser.parse_args()
    asyncio.run(verify(args.bundle.resolve(), args.sha256))
