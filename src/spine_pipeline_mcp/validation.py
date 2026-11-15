"""Conservative static checks for Spine JSON; no runtime or visual guarantees."""
from __future__ import annotations

import math
from typing import Any


def _number(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_document(doc: dict) -> dict:
    """Return errors, warnings and mesh counts without mutating the input.

    Handles modern skin arrays and legacy skin objects. Linked meshes are
    counted separately: their resolved topology is not validated here.
    """
    errors: list[dict] = []
    warnings: list[dict] = []
    counts = {"bones": 0, "slots": 0, "attachments": 0, "meshes": 0,
              "weighted_meshes": 0, "linked_meshes": 0, "animations": 0}

    def error(path, message):
        errors.append({"path": path, "message": message})

    def warning(path, message):
        warnings.append({"path": path, "message": message})

    if not isinstance(doc, dict):
        error("$", "Expected a JSON object")
        return {"valid": False, "errors": errors, "warnings": warnings, "counts": counts,
                "scope": "static checks only; not full schema, runtime or visual validation"}
    if not isinstance(doc.get("skeleton"), dict):
        error("skeleton", "Expected a skeleton object")
    bones = doc.get("bones", [])
    if not isinstance(bones, list):
        error("bones", "Expected an array")
        bones = []
    counts["bones"] = len(bones)
    names = set()
    parents = {}
    for i, bone in enumerate(bones):
        path = f"bones[{i}]"
        if not isinstance(bone, dict) or not isinstance(bone.get("name"), str):
            error(path, "Bone must have a string name")
            continue
        name = bone["name"]
        if name in names:
            error(path + ".name", "Duplicate bone name")
        names.add(name)
        parent = bone.get("parent")
        if parent is not None and not isinstance(parent, str):
            error(path + ".parent", "Parent must be a string")
        else:
            parents[name] = parent
    for name, parent in parents.items():
        if parent is not None and parent not in names:
            error("bones." + name + ".parent", "Parent bone does not exist")
    # Iterative walk avoids recursion limits on long skeleton hierarchies.
    done = set()
    for name in parents:
        current = name
        trail = set()
        while current is not None and current in parents and current not in done:
            if current in trail:
                error("bones." + current, "Parent hierarchy contains a cycle")
                break
            trail.add(current)
            current = parents[current]
        done.update(trail)
    slots = doc.get("slots", [])
    if not isinstance(slots, list):
        error("slots", "Expected an array")
        slots = []
    counts["slots"] = len(slots)
    slot_names = set()
    for i, slot in enumerate(slots):
        if not isinstance(slot, dict):
            error(f"slots[{i}]", "Expected a slot object")
            continue
        if not isinstance(slot.get("name"), str):
            error(f"slots[{i}].name", "Expected a string")
        elif slot["name"] in slot_names:
            error(f"slots[{i}].name", "Duplicate slot name")
        else:
            slot_names.add(slot["name"])
        if not isinstance(slot.get("bone"), str) or slot["bone"] not in names:
            error(f"slots[{i}].bone", "Slot bone does not exist")

    skins = doc.get("skins", [])
    skin_items = []
    if isinstance(skins, dict):
        skin_items = list(skins.items())
    elif isinstance(skins, list):
        for i, skin in enumerate(skins):
            if not isinstance(skin, dict):
                error(f"skins[{i}]", "Expected a skin object")
            else:
                skin_items.append((str(skin.get("name", i)), skin.get("attachments", {})))
    else:
        error("skins", "Expected a skin array or legacy object")
    for skin_name, skin in skin_items:
        path = "skins." + skin_name
        if not isinstance(skin, dict):
            error(path, "Expected slot attachment mapping")
            continue
        for slot_name, attachments in skin.items():
            slot_path = path + "." + slot_name
            if slot_name not in slot_names:
                error(slot_path, "Attachment slot does not exist")
            if not isinstance(attachments, dict):
                error(slot_path, "Expected attachment mapping")
                continue
            for attachment_name, attachment in attachments.items():
                loc = slot_path + "." + attachment_name
                counts["attachments"] += 1
                if not isinstance(attachment, dict):
                    error(loc, "Expected attachment object")
                    continue
                kind = attachment.get("type", "region")
                if kind == "linkedmesh":
                    counts["linked_meshes"] += 1
                    warning(loc, "Linked mesh topology/reference resolution is not checked")
                    continue
                if kind != "mesh":
                    continue
                counts["meshes"] += 1
                uvs = attachment.get("uvs")
                vertices = attachment.get("vertices")
                triangles = attachment.get("triangles")
                if not isinstance(uvs, list) or len(uvs) % 2 or len(uvs) < 6 or not all(_number(v) for v in uvs):
                    error(loc + ".uvs", "UVs must be finite coordinate pairs for at least three vertices")
                    continue
                vertex_count = len(uvs) // 2
                if not isinstance(triangles, list) or not triangles or len(triangles) % 3:
                    error(loc + ".triangles", "Expected nonempty triangle index triples")
                elif any(not _integer(v) or not 0 <= v < vertex_count for v in triangles):
                    error(loc + ".triangles", "Triangle index is not an integer in vertex range")
                else:
                    for start in range(0, len(triangles), 3):
                        if len(set(triangles[start:start + 3])) < 3:
                            error(loc + f".triangles[{start}]", "Triangle repeats a vertex index")
                if not isinstance(vertices, list) or not all(_number(v) for v in vertices):
                    error(loc + ".vertices", "Vertices must be a finite numeric array")
                    continue
                if len(vertices) == len(uvs):
                    continue  # Unweighted x/y pairs.
                counts["weighted_meshes"] += 1
                cursor = 0
                for vertex in range(vertex_count):
                    vloc = loc + f".vertices[vertex={vertex}]"
                    if cursor >= len(vertices) or not _integer(vertices[cursor]) or vertices[cursor] < 1:
                        error(vloc, "Expected positive integer influence count")
                        break
                    influences = vertices[cursor]
                    cursor += 1
                    if cursor + influences * 4 > len(vertices):
                        error(vloc, "Truncated packed influence data")
                        break
                    total = 0.0
                    used = set()
                    for j in range(influences):
                        index, x, y, weight = vertices[cursor:cursor + 4]
                        cursor += 4
                        if not _integer(index) or not 0 <= index < len(bones):
                            error(vloc, "Influence bone index is outside the bones array")
                        elif index in used:
                            warning(vloc, "Repeated influence bone index")
                        else:
                            used.add(index)
                        if weight < 0 or weight > 1:
                            error(vloc, "Influence weight must be between zero and one")
                        total += weight
                    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-3):
                        error(vloc, "Influence weights must sum to one (tolerance 0.001)")
                else:
                    if cursor != len(vertices):
                        error(loc + ".vertices", "Extra packed influence data after final vertex")

    animations = doc.get("animations", {})
    if not isinstance(animations, dict):
        error("animations", "Expected an animation object")
        animations = {}
    counts["animations"] = len(animations)
    for name, animation in animations.items():
        loc = "animations." + name
        if not isinstance(animation, dict):
            error(loc, "Expected an animation object")
            continue
        animated_bones = animation.get("bones", {})
        if not isinstance(animated_bones, dict):
            error(loc + ".bones", "Expected bone timeline mapping")
        else:
            for bone_name in animated_bones:
                if bone_name not in names:
                    error(loc + ".bones." + bone_name, "Animated bone does not exist")
        # Animation leaf arrays of objects are keyframe sequences. Omitted time
        # means zero in Spine JSON. Curve/vertex numeric arrays are left alone.
        stack = [(loc, animation)]
        while stack:
            path, item = stack.pop()
            if isinstance(item, dict):
                stack.extend((path + "." + str(k), v) for k, v in item.items())
            elif isinstance(item, list):
                if item and all(isinstance(frame, dict) for frame in item):
                    previous = -1.0
                    for i, frame in enumerate(item):
                        time = frame.get("time", 0)
                        if not _number(time) or time < 0:
                            error(path + f"[{i}].time", "Key time must be finite and nonnegative")
                        elif time <= previous:
                            error(path + f"[{i}].time", "Key times must be strictly increasing")
                        else:
                            previous = time
                stack.extend((path + f"[{i}]", v) for i, v in enumerate(item) if isinstance(v, (dict, list)))
    if counts["meshes"] > 1:
        warning("skins", "Multiple mesh attachments; counts alone cannot prove whole-art mesh continuity")
    return {"valid": not errors, "errors": errors, "warnings": warnings, "counts": counts,
            "scope": "static checks only; not full schema, runtime or visual validation"}
