"""Build a deterministic MCPB from an explicit list of public runtime files."""
import hashlib
import json
from pathlib import Path
import tomllib
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def build(root: Path) -> Path:
    manifest = json.loads((root / "manifest.json").read_text())
    project = tomllib.loads((root / "pyproject.toml").read_text())
    version = project["project"]["version"]
    if manifest["version"] != version:
        raise ValueError("Bundle and project versions must match")
    files = [
        Path(name) for name in (
            "manifest.json", "pyproject.toml", "uv.lock", "README.md",
            "LICENSE", "THIRD_PARTY_NOTICES.md", "mcpb/launch.py",
            "docs/assets/brand/icon.png",
        )
    ]
    files.extend(p.relative_to(root) for p in (root / "src/spine_pipeline_mcp").glob("*.py"))
    output = root / "dist" / f"spine-pipeline-mcp-{version}.mcpb"
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for relative in sorted(files):
            source = root / relative
            if source.is_symlink() or not source.is_file():
                raise ValueError(f"Expected a regular public bundle file: {relative}")
            info = ZipInfo(relative.as_posix(), date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())
    print(json.dumps({
        "path": str(output), "version": version, "files": len(files),
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }, indent=2))
    return output


if __name__ == "__main__":
    build(Path(__file__).resolve().parents[1])
