from copy import deepcopy
import pytest
from spine_pipeline_mcp.animation import copy_animation, retime_animation, set_bone_keys


@pytest.fixture
def doc():
    animation = {
        "bones": {"root": {"rotate": [
            {"time": 0, "value": 0, "curve": "stepped"},
            {"time": 2, "value": 10},
        ]}},
        "events": [{"time": 1, "name": "step"}],
        "attachments": {"default": {"body": {"body": {
            "deform": [{"time": 2, "vertices": [0, 1]}]
        }}}},
    }
    return {"skeleton": {"spine": "4.3.26"}, "bones": [{"name": "root"}],
            "animations": {"idle": animation}}


def test_copy_is_deep_and_source_unchanged(doc):
    before = deepcopy(doc)
    copied = copy_animation(doc, "idle", "walk")
    copied["animations"]["walk"]["events"][0]["name"] = "changed"
    assert copied["animations"]["idle"]["events"][0]["name"] == "step"
    assert doc == before


@pytest.mark.parametrize("source,target", [("missing", "new"), ("idle", "idle"), ("", "new")])
def test_copy_rejects(doc, source, target):
    with pytest.raises(ValueError): copy_animation(doc, source, target)


def test_retime_all_times_with_stepped_curves(doc):
    before = deepcopy(doc)
    result = retime_animation(doc, "idle", 2)
    animation = result["animations"]["idle"]
    assert animation["bones"]["root"]["rotate"][1]["time"] == 1
    assert animation["events"][0]["time"] == .5
    assert animation["attachments"]["default"]["body"]["body"]["deform"][0]["time"] == 1
    assert animation["bones"]["root"]["rotate"][0]["curve"] == "stepped"
    assert doc == before


@pytest.mark.parametrize("speed", [0, -1, float("inf"), float("nan"), True, "2"])
def test_bad_speed(doc, speed):
    with pytest.raises(ValueError): retime_animation(doc, "idle", speed)


def test_set_keys_preserves_other_timelines(doc):
    before = deepcopy(doc)
    keys = [{"time": 0, "x": 0, "y": 0}, {"time": 1, "x": 10, "curve": "stepped"}]
    result = set_bone_keys(doc, "idle", "root", "translate", keys)
    keys[0]["x"] = 999
    assert result["animations"]["idle"]["bones"]["root"]["translate"][0]["x"] == 0
    assert result["animations"]["idle"]["bones"]["root"]["rotate"] == before["animations"]["idle"]["bones"]["root"]["rotate"]
    assert doc == before


def test_set_new_animation(doc):
    result = set_bone_keys(doc, "attack", "root", "rotate", [{"time": 0, "value": 10}])
    assert result["animations"]["attack"]["bones"]["root"]["rotate"][0]["value"] == 10
    assert "attack" not in doc["animations"]


@pytest.mark.parametrize("keys", [[], [{"time": -1, "value": 0}], [{"time": 0, "angle": 1}], [{"value": 1}], [{"time": 0, "value": float("nan")}], [{"time": True, "value": 1}], [{"time": 0, "value": 1}, {"time": 0, "value": 2}], [{"time": 1, "value": 1}, {"time": 0, "value": 2}], [{"time": 0, "value": 1, "curve": [1,2]}], [{"time": 0, "value": 1, "surprise": 1}]])
def test_invalid_keys(doc, keys):
    with pytest.raises(ValueError): set_bone_keys(doc, "idle", "root", "rotate", keys)


def test_unknown_bone_and_timeline(doc):
    with pytest.raises(ValueError): set_bone_keys(doc, "idle", "missing", "rotate", [{"time": 0, "value": 0}])
    with pytest.raises(ValueError): set_bone_keys(doc, "idle", "root", "shear", [{"time": 0, "x": 0}])


def test_bad_existing_time(doc):
    doc["animations"]["idle"]["events"][0]["time"] = -1
    with pytest.raises(ValueError): retime_animation(doc, "idle", 2)


@pytest.mark.parametrize("curve", [[0.1, 0, 0.9, 1], 0.1, {"time": 0.1}, "bezier", None])
def test_retime_rejects_unsupported_curves(doc, curve):
    doc["animations"]["idle"]["bones"]["root"]["rotate"][0]["curve"] = curve
    before = deepcopy(doc)
    with pytest.raises(ValueError): retime_animation(doc, "idle", 2)
    assert doc == before


def test_retime_rejects_curve_metadata(doc):
    doc["animations"]["idle"]["bones"]["root"]["rotate"][0]["curve2"] = 0.2
    with pytest.raises(ValueError): retime_animation(doc, "idle", 2)


def test_retime_implicit_linear(doc):
    del doc["animations"]["idle"]["bones"]["root"]["rotate"][0]["curve"]
    result = retime_animation(doc, "idle", 2)
    assert result["animations"]["idle"]["bones"]["root"]["rotate"][1]["time"] == 1


@pytest.mark.parametrize("curve", [[0.1, 0, 0.9, 1], 0.1, "linear", None])
def test_set_rejects_unsupported_curves(doc, curve):
    with pytest.raises(ValueError):
        set_bone_keys(doc, "idle", "root", "rotate", [{"time": 0, "value": 10, "curve": curve}])


@pytest.mark.parametrize("version", ["4.2.0", "3.8.75", "4.4.0", None])
def test_key_edit_requires_supported_schema(doc, version):
    doc["skeleton"]["spine"] = version
    with pytest.raises(ValueError, match="4.3"):
        set_bone_keys(doc, "idle", "root", "rotate", [{"time":0,"value":1}])
