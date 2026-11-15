"""Bounded JSON inspection; no shell execution, publication or source writes."""
import hashlib
import json
import os
import stat
import uuid
from pathlib import Path

MAX_BYTES = 16 * 1024 * 1024


def no_symlinks(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("Symlink paths are not allowed")
    return path


class Workspace:
    def __init__(self, source: Path, staging: Path):
        self.source = no_symlinks(source).resolve(strict=True)
        self.staging = no_symlinks(staging).resolve()
        if not self.source.is_dir():
            raise ValueError("Source must be a directory")
        if self.source == self.staging or self.source in self.staging.parents or self.staging in self.source.parents:
            raise ValueError("Source and staging must be separate, non-overlapping directories")

    def read(self, relative_path: str):
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Only relative paths without parent traversal are allowed")
        path = no_symlinks(self.source / relative).resolve(strict=True)
        if self.source not in path.parents or path.suffix not in {".json", ".spine-json"}:
            raise ValueError("Only JSON files inside the configured source are allowed")
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError("Only regular files are allowed")
        with path.open("rb") as f:
            raw = f.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("JSON exceeds 16 MiB limit")
        doc = json.loads(raw)
        if not isinstance(doc, dict) or not isinstance(doc.get("skeleton"), dict) or not isinstance(doc.get("bones"), list):
            raise ValueError("Expected Spine JSON with skeleton object and bones array")
        if not all(isinstance(b, dict) and isinstance(b.get("name"), str) for b in doc["bones"]):
            raise ValueError("Invalid bones array")
        if not isinstance(doc.get("animations", {}), dict):
            raise ValueError("Animations must be an object")
        return raw, doc

    def inspect(self, relative_path: str):
        raw, doc = self.read(relative_path)
        names = [b["name"] for b in doc["bones"]]
        warnings = []
        if len(set(names)) != len(names):
            warnings.append("Duplicate bone names")
        for b in doc["bones"]:
            if b.get("parent") and b["parent"] not in names:
                warnings.append("Missing parent for bone: " + b["name"])
        return {"path": relative_path, "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw), "spine_version": doc["skeleton"].get("spine"),
                "bones": names, "animations": list(doc.get("animations", {})),
                "warnings": warnings, "validation_scope": "basic structure only; not runtime/mesh validation"}

    def stage(self, relative_path: str):
        raw, _ = self.read(relative_path)
        no_symlinks(self.staging)
        self.staging.mkdir(parents=True, exist_ok=True)
        job_id = uuid.uuid4().hex
        job = self.staging / job_id
        job.mkdir(mode=0o700)
        target = job / "skeleton.json"
        with target.open("xb") as f:
            f.write(raw)
        return {"job_id": job_id, "staged_path": str(target),
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                "note": "JSON copy only; textures/atlas not copied, source unchanged"}
