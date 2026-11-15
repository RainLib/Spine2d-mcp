"""Isolated native-runtime smoke checks, not visual-quality validation."""
import json
import os
import shutil
import subprocess
from pathlib import Path

from .core import no_symlinks
from .pipeline import MAX_ASSET_BYTES, safe_asset

TIMEOUT_SECONDS = 60
MAX_LOG_BYTES = 4 * 1024 * 1024

SCRIPT = '''extends SceneTree
func _init() -> void:
 call_deferred("run")
func finish(report: Dictionary, code: int) -> void:
 var file = FileAccess.open("res://report.json", FileAccess.WRITE)
 if file == null:
  printerr("Cannot write validation report")
  quit(2)
  return
 file.store_string(JSON.stringify(report, "  "))
 file.close()
 print("SPINE_MCP_GODOT ", JSON.stringify(report))
 quit(code)
func run() -> void:
 var report = {"engine_version": Engine.get_version_info().string, "native_class": ClassDB.class_exists("SpineSprite"), "loaded": false, "initialized": false, "animations": [], "errors": []}
 if not report.native_class:
  report.errors.append("Configured Godot has no native SpineSprite class")
  finish(report, 1)
  return
 var data = load("res://assets/skeleton_data.tres")
 if data == null:
  report.errors.append("SpineSkeletonDataResource failed to load")
  finish(report, 1)
  return
 report.loaded = true
 var source = JSON.parse_string(FileAccess.get_file_as_string("res://assets/skeleton.spine-json"))
 if not source is Dictionary:
  report.errors.append("Export JSON failed to parse")
  finish(report, 1)
  return
 var sprite = ClassDB.instantiate("SpineSprite")
 sprite.set_skeleton_data_res(data)
 sprite.set_update_mode(2)
 root.add_child(sprite)
 if sprite.get_skeleton() == null:
  report.errors.append("Spine skeleton initialization failed")
  finish(report, 1)
  return
 report.initialized = true
 var animation_map = source.get("animations", {})
 for clip in animation_map:
  var animation = data.find_animation(clip)
  if animation == null:
   report.errors.append("Animation missing in runtime: " + str(clip))
   continue
  sprite.get_animation_state().clear_tracks()
  sprite.get_skeleton().set_to_setup_pose()
  var track = sprite.get_animation_state().set_animation(clip, false, 0)
  if track == null:
   report.errors.append("Animation could not start: " + str(clip))
   continue
  track.set_mix_duration(0)
  sprite.update_skeleton(0.0)
  sprite.update_skeleton(minf(0.1, animation.get_duration()))
  report.animations.append({"name": str(clip), "duration": animation.get_duration()})
 sprite.free()
 finish(report, 0 if report.errors.is_empty() else 1)
'''


def _run(executable, project, args, log_path, env):
    with log_path.open("wb") as log:
        try:
            process = subprocess.run([str(executable), "--headless", "--path", str(project), *args],
                                     cwd=project, stdin=subprocess.DEVNULL, stdout=log,
                                     stderr=subprocess.STDOUT, timeout=TIMEOUT_SECONDS, env=env)
        except subprocess.TimeoutExpired:
            return {"ok": False, "reason": "timeout", "log_path": str(log_path)}
    if log_path.stat().st_size > MAX_LOG_BYTES:
        return {"ok": False, "reason": "oversized_log", "log_path": str(log_path)}
    lines = log_path.read_text(errors="replace").splitlines()
    errors = [line for line in lines if line.lstrip().startswith(("ERROR:", "SCRIPT ERROR:"))]
    return {"ok": process.returncode == 0 and not errors, "returncode": process.returncode,
            "errors": errors[:20], "log_path": str(log_path)}


def validate_export(pipeline, export_job_id):
    """Import and sample an export in a new staging-only Godot project."""
    executable = Path(os.environ.get("SPINE_MCP_GODOT_EXECUTABLE", ""))
    if not executable.is_absolute() or not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError("Set SPINE_MCP_GODOT_EXECUTABLE to an existing absolute executable")
    parent = pipeline.job(export_job_id)
    manifest_file = safe_asset(parent, "export-result.json")
    if manifest_file.stat().st_size > 1024 * 1024:
        raise ValueError("Export manifest too large")
    manifest = json.loads(manifest_file.read_text())
    runtime = no_symlinks(parent / "runtime").resolve(strict=True)
    if runtime.parent != parent or str(runtime) != manifest.get("runtime_directory"):
        raise ValueError("Export runtime must be inside its staging job")
    entries = list(runtime.iterdir())
    if len(entries) > 260:
        raise ValueError("Too many runtime files")
    sources = [safe_asset(runtime, p.name) for p in entries]
    if any(p.suffix.lower() not in {".json", ".atlas", ".png"} for p in sources):
        raise ValueError("Runtime must contain only JSON, atlas and PNG files")
    if sum(p.stat().st_size for p in sources) > MAX_ASSET_BYTES:
        raise ValueError("Runtime exceeds byte limit")
    json_files = [p for p in sources if p.suffix == ".json"]
    atlas_files = [p for p in sources if p.suffix == ".atlas"]
    if len(json_files) != 1 or len(atlas_files) != 1:
        raise ValueError("Exactly one skeleton JSON and one atlas required")
    # Atlas page names must resolve to bundled PNGs, never outside the project.
    png_names = {p.name for p in sources if p.suffix == ".png"}
    if not png_names:
        raise ValueError("Atlas needs bundled PNG pages")
    atlas_text = atlas_files[0].read_text()
    for block in atlas_text.strip().split("\n\n"):
        page = block.splitlines()[0].strip()
        if page not in png_names:
            raise ValueError("Atlas page is not a bundled PNG basename")
    job = pipeline.new_job()
    project = job / "godot-project"
    assets = project / "assets"
    assets.mkdir(parents=True)
    shutil.copyfile(json_files[0], assets / "skeleton.spine-json")
    shutil.copyfile(atlas_files[0], assets / "skeleton.atlas")
    for file in sources:
        if file.suffix == ".png":
            shutil.copyfile(file, assets / file.name)
    (assets / "skeleton_data.tres").write_text('''[gd_resource type="SpineSkeletonDataResource" load_steps=3 format=3]
[ext_resource type="SpineAtlasResource" path="res://assets/skeleton.atlas" id="1"]
[ext_resource type="SpineSkeletonFileResource" path="res://assets/skeleton.spine-json" id="2"]
[resource]
atlas_res = ExtResource("1")
skeleton_file_res = ExtResource("2")
''')
    (project / "project.godot").write_text('''config_version=5
[application]
config/name="Spine MCP isolated validation"
[rendering]
renderer/rendering_method="gl_compatibility"
''')
    (project / "verify.gd").write_text(SCRIPT)
    home = job / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home), XDG_DATA_HOME=str(home / "data"),
               XDG_CONFIG_HOME=str(home / "config"), XDG_CACHE_HOME=str(home / "cache"))
    result = {"job_id": job.name, "parent_job": export_job_id, "ok": False,
              "scope": "native resource load and brief animation sampling only; not visual, mesh-deformation or game validation"}
    # Import texture pages before atlas: native Spine importer may otherwise
    # race PNG import and emit a missing-texture error on a pristine project.
    atlas = assets / "skeleton.atlas"
    tres = assets / "skeleton_data.tres"
    atlas.rename(assets / "atlas.pending")
    tres.rename(assets / "resource.pending")
    result["texture_import"] = _run(executable, project, ["--editor", "--import", "--quit"], job / "godot-textures.log", env)
    (assets / "atlas.pending").rename(atlas)
    (assets / "resource.pending").rename(tres)
    if not result["texture_import"]["ok"]:
        (job / "godot-result.json").write_text(json.dumps(result, indent=2))
        return result
    result["import"] = _run(executable, project, ["--editor", "--import", "--quit"], job / "godot-import.log", env)
    if result["import"]["ok"]:
        result["check"] = _run(executable, project, ["--script", "res://verify.gd"], job / "godot-check.log", env)
        report = project / "report.json"
        if report.is_file() and report.stat().st_size <= 1024 * 1024:
            result["report"] = json.loads(report.read_text())
            result["ok"] = bool(result["check"]["ok"] and result["report"].get("initialized") and not result["report"].get("errors"))
        else:
            result["error"] = "Godot did not produce a bounded report"
    (job / "godot-result.json").write_text(json.dumps(result, indent=2))
    return result
