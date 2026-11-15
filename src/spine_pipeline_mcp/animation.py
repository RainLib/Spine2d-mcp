"""Pure, copy-on-write animation operations for Spine JSON.

Rotation uses the Spine 4.3 `value` field (degrees), not legacy `angle`.
Retime changes `time` keys, including events/deform. Only implicit linear and
explicit stepped interpolation are supported; numeric/Bezier curves are rejected.
"""
from copy import deepcopy
import math
import re


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{label} must be a finite number")
    return value


def _name(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f"{label} must be a nonempty name of at most 256 characters")
    return value


def _animations(doc):
    if not isinstance(doc, dict):
        raise ValueError("Document must be an object")
    animations = doc.get("animations", {})
    if not isinstance(animations, dict):
        raise ValueError("Animations must be an object")
    return animations


def copy_animation(doc: dict, source: str, target: str) -> dict:
    """Copy a named animation to a new name; existing targets are never replaced."""
    _name(source, "source")
    _name(target, "target")
    animations = _animations(doc)
    if source not in animations or not isinstance(animations[source], dict):
        raise ValueError("Source animation does not exist or is not an object")
    if target in animations:
        raise ValueError("Target animation already exists")
    result = deepcopy(doc)
    result["animations"][target] = deepcopy(animations[source])
    return result


def retime_animation(doc: dict, name: str, speed: float) -> dict:
    """Scale all animation time keys by 1/speed; speed=2 makes it twice as fast.

    Numeric/Bezier curve data is rejected rather than silently distorted.
    No source data is mutated.
    """
    _name(name, "animation")
    speed = _number(speed, "speed")
    if speed <= 0:
        raise ValueError("Speed must be greater than zero")
    animations = _animations(doc)
    if name not in animations or not isinstance(animations[name], dict):
        raise ValueError("Animation does not exist or is not an object")
    result = deepcopy(doc)

    def visit(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "time":
                    old = _number(value, "time")
                    if old < 0:
                        raise ValueError("Time must be nonnegative")
                    scaled = old / speed
                    _number(scaled, "scaled time")
                    node[key] = scaled
                elif key == "curve":
                    if value != "stepped":
                        raise ValueError("Retime supports only implicit linear or stepped curves; Bezier data is unsupported")
                elif key.startswith("curve"):
                    raise ValueError("Unsupported curve metadata")
                else:
                    visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(result["animations"][name])
    return result


def set_bone_keys(doc: dict, animation: str, bone: str, timeline: str, keys: list) -> dict:
    """Set one bone timeline on a copied document, creating the animation if absent.

    Allowed timelines: rotate (`value` degrees), translate (`x`, `y`), scale
    (`x`, `y`). Keys require explicit nonnegative strictly increasing `time`.
    Optional curve must be `stepped`; omission means linear interpolation.
    Unknown fields, legacy rotate `angle`, invalid values and unknown bones fail.
    """
    version = doc.get("skeleton", {}).get("spine") if isinstance(doc, dict) and isinstance(doc.get("skeleton"), dict) else None
    if not isinstance(version, str) or not re.fullmatch(r"4\.3\.[0-9]+", version):
        raise ValueError("Bone key editing currently requires a Spine 4.3.x document")
    _name(animation, "animation")
    _name(bone, "bone")
    animations = _animations(doc)
    bones = doc.get("bones", [])
    if not isinstance(bones, list) or not any(isinstance(b, dict) and b.get("name") == bone for b in bones):
        raise ValueError("Bone does not exist")
    allowed = {"rotate": {"value"}, "translate": {"x", "y"}, "scale": {"x", "y"}}
    if timeline not in allowed:
        raise ValueError("Timeline must be rotate, translate or scale")
    if not isinstance(keys, list) or not keys or len(keys) > 10000:
        raise ValueError("Keys must be a nonempty list of at most 10000 keys")
    previous = -1
    for key in keys:
        if not isinstance(key, dict) or set(key) - (allowed[timeline] | {"time", "curve"}):
            raise ValueError("Invalid key object or unsupported field")
        if "time" not in key or not (set(key) & allowed[timeline]):
            raise ValueError("Each key needs time and at least one timeline value")
        time = _number(key["time"], "time")
        if time < 0 or time <= previous:
            raise ValueError("Key times must be nonnegative and strictly increasing")
        previous = time
        for field in allowed[timeline] & set(key):
            _number(key[field], field)
        if "curve" in key and key["curve"] != "stepped":
            raise ValueError("Curve must be omitted (linear) or stepped; numeric/Bezier curves are unsupported")
    if animation in animations and not isinstance(animations[animation], dict):
        raise ValueError("Animation must be an object")
    result = deepcopy(doc)
    anim = result.setdefault("animations", {}).setdefault(animation, {})
    timelines = anim.setdefault("bones", {})
    if not isinstance(timelines, dict):
        raise ValueError("Animation bones must be an object")
    bone_timelines = timelines.setdefault(bone, {})
    if not isinstance(bone_timelines, dict):
        raise ValueError("Bone timelines must be an object")
    bone_timelines[timeline] = deepcopy(keys)
    return result
