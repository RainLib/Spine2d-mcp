"""Staging-only asset bundles and fixed, explicitly configured Spine CLI execution."""
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from .core import MAX_BYTES, Workspace, no_symlinks

MAX_IMAGES = 256
MAX_ASSET_BYTES = 128 * 1024 * 1024


def attachments(doc):
    skins = doc.get("skins", [])
    if isinstance(skins, dict):
        skins = [{"name": name, "attachments": value} for name, value in skins.items()]
    for skin in skins:
        for slot, values in skin.get("attachments", {}).items():
            for name, data in values.items():
                yield skin.get("name", "default"), slot, name, data


def safe_asset(root, relative):
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("Image paths must be relative and cannot traverse parents")
    path = no_symlinks(root / rel).resolve(strict=True)
    if root.resolve() not in path.parents or not path.is_file():
        raise ValueError("Image must be a regular file in its allowed root")
    return path


class Pipeline:
    def __init__(self, workspace: Workspace):
        self.ws = workspace

    def new_job(self):
        no_symlinks(self.ws.staging)
        self.ws.staging.mkdir(parents=True, exist_ok=True)
        job = self.ws.staging / uuid.uuid4().hex
        job.mkdir(mode=0o700)
        return job

    def job(self, job_id):
        if not re.fullmatch(r"[0-9a-f]{32}", job_id):
            raise ValueError("Invalid staging job ID")
        job = no_symlinks(self.ws.staging / job_id).resolve(strict=True)
        if job.parent != self.ws.staging or not job.is_dir():
            raise ValueError("Invalid job directory")
        return job

    def read_job(self, job_id):
        job = self.job(job_id)
        file = safe_asset(job, "skeleton.json")
        if file.stat().st_size > MAX_BYTES:
            raise ValueError("Staged JSON too large")
        doc = json.loads(file.read_text())
        if not isinstance(doc, dict) or not isinstance(doc.get("bones"), list):
            raise ValueError("Invalid staged skeleton")
        return job, doc

    def save(self, job, doc, metadata):
        data = json.dumps(doc, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
        if len(data) > MAX_BYTES:
            raise ValueError("Result exceeds JSON limit")
        with (job / "skeleton.json").open("xb") as f:
            f.write(data)
        manifest = {"job_id": job.name, "sha256": hashlib.sha256(data).hexdigest(), **metadata}
        (job / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return manifest

    def stage_bundle(self, relative_path):
        raw, doc = self.ws.read(relative_path)
        source = (self.ws.source / relative_path).resolve()
        image_setting = doc["skeleton"].get("images", "./")
        if not isinstance(image_setting, str) or Path(image_setting).is_absolute():
            raise ValueError("Source skeleton image root must be relative")
        images = no_symlinks(source.parent / image_setting).resolve(strict=True)
        if images != self.ws.source and self.ws.source not in images.parents:
            raise ValueError("Skeleton images root escapes configured source")
        assets = {}
        total = 0
        for _, _, name, data in attachments(doc):
            kind = data.get("type", "region")
            if kind not in {"region", "mesh", "linkedmesh"}:
                continue
            if data.get("sequence"):
                raise ValueError("Image sequences are not supported yet")
            image_name = data.get("path", name)
            rel = Path(image_name)
            if rel.is_absolute() or ".." in rel.parts or not image_name:
                raise ValueError("Unsafe attachment image path")
            candidates = [rel] if rel.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} else [Path(str(rel)+ext) for ext in (".png", ".jpg", ".jpeg", ".webp")]
            found = next((candidate for candidate in candidates if (images / candidate).exists()), None)
            if found is None:
                raise ValueError("Missing image for attachment: " + image_name)
            path = safe_asset(images, found)
            if str(found) not in assets:
                total += path.stat().st_size
                assets[str(found)] = path
            if len(assets) > MAX_IMAGES or total > MAX_ASSET_BYTES:
                raise ValueError("Asset bundle exceeds file or byte limit")
        job = self.new_job()
        (job / "images").mkdir()
        for rel, source_file in assets.items():
            target = job / "images" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_file, target)
        doc = copy.deepcopy(doc)
        # Never let the CLI follow original project image/audio paths.
        doc["skeleton"]["images"] = "images/"
        doc["skeleton"].pop("audio", None)
        if any(isinstance(event, dict) and event.get("audio") for event in doc.get("events", {}).values()):
            raise ValueError("Audio-linked events are not supported in isolated bundles")
        return self.save(job, doc, {"operation": "stage_bundle", "source_sha256": hashlib.sha256(raw).hexdigest(), "images": len(assets), "image_bytes": total})

    def transform(self, job_id, operation, transformer):
        parent, doc = self.read_job(job_id)
        updated = transformer(doc)
        job = self.new_job()
        images = no_symlinks(parent / "images")
        if images.exists():
            total = 0
            paths = list(images.rglob("*"))
            if len(paths) > MAX_IMAGES * 8:
                raise ValueError("Too many staged image entries")
            for file in paths:
                no_symlinks(file)
                if file.is_file():
                    total += file.stat().st_size
                    if total > MAX_ASSET_BYTES:
                        raise ValueError("Staged images exceed byte limit")
                    target = job / "images" / file.relative_to(images)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(file, target)
        return self.save(job, updated, {"operation": operation, "parent_job": job_id})

    def export(self, job_id):
        executable = os.environ.get("SPINE_MCP_CLI")
        version = os.environ.get("SPINE_MCP_CLI_VERSION")
        if not executable or not version:
            raise ValueError("Set SPINE_MCP_CLI and SPINE_MCP_CLI_VERSION to enable CLI export")
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            raise ValueError("Pin an exact Spine editor version")
        executable = Path(executable)
        if not executable.is_absolute() or not executable.is_file() or not os.access(executable, os.X_OK):
            raise ValueError("CLI executable must be an existing absolute executable path")
        job, doc = self.read_job(job_id)
        if doc.get("skeleton", {}).get("spine") != version:
            raise ValueError("Skeleton and configured Spine CLI version must match exactly")
        if doc.get("skeleton", {}).get("images") != "images/":
            raise ValueError("Export requires an isolated stage_bundle job")
        # Clone the bundle again: the CLI never touches the input job or source tree.
        result = self.transform(job_id, "spine_export", lambda d: d)
        output = self.job(result["job_id"])
        runtime = output / "runtime"
        runtime.mkdir()
        base = [str(executable), "--hide-license", "-u", version]
        commands = [base + ["-i", str(output/"skeleton.json"), "-o", str(output/"skeleton.spine"), "--to", "skeleton", "--replace", "-r"],
                    base + ["-i", str(output/"skeleton.spine"), "-o", str(runtime)+"/", "--set", "packAtlas.maxWidth=2048", "--set", "packAtlas.maxHeight=2048", "--set", "packAtlas.rotation=false", "--set", "nonessential=true", "-e", "json+pack"]]
        for name, args in zip(("import", "export"), commands):
            logfile = output / (name + ".log")
            with logfile.open("wb") as log:
                try:
                    process = subprocess.run(args, cwd=output, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, timeout=120, check=False)
                except subprocess.TimeoutExpired as error:
                    raise RuntimeError("Spine " + name + " timed out; inspect staging log") from error
            if logfile.stat().st_size > 8 * 1024 * 1024:
                raise RuntimeError("Spine log exceeds expected size; inspect staging log")
            text = logfile.read_text(errors="replace")
            if process.returncode or "Complete." not in text:
                raise RuntimeError("Spine " + name + " failed; inspect " + str(logfile))
        if not (output/"skeleton.spine").is_file() or not list(runtime.glob("*.json")) or not list(runtime.glob("*.atlas")) or not list(runtime.glob("*.png")):
            raise RuntimeError("CLI did not produce expected project/JSON/atlas/PNG outputs")
        result.update({"runtime_directory": str(runtime), "project": str(output/"skeleton.spine"), "spine_version": version, "files": sorted(p.name for p in runtime.iterdir() if p.is_file())})
        (output/"export-result.json").write_text(json.dumps(result, indent=2))
        return result
