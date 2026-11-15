from copy import deepcopy
import asyncio
import json
import os
import sys

import pytest

from spine_pipeline_mcp.core import Workspace
from spine_pipeline_mcp.mesh import (get_weights, inspect_meshes, pack_vertices,
                                     replace_mesh, set_weights, topology, unpack_vertices)
from spine_pipeline_mcp.mesh_policy import validate_mesh_policy
from spine_pipeline_mcp.pipeline import Pipeline


def rig():
    bones = [{"name": "root"}, {"name": "arm", "parent": "root"},
             {"name": "head", "parent": "root"}, {"name": "cloth", "parent": "arm"}]
    vertices = []
    for x, y in ((0, 0), (10, 0), (10, 10), (0, 10)):
        # Deliberately unordered; head has a different bone-local bind offset.
        vertices.extend([2, 2, x - 3, y - 5, .25, 0, x, y, .75])
    return {"skeleton": {"spine": "4.3.26"}, "bones": bones,
        "slots": [{"name": "art", "bone": "root"}], "skins": [{"name": "default", "attachments": {
        "art": {"body": {"type": "mesh", "path": "painting", "width": 10, "height": 10,
        "uvs": [0, 0, 1, 0, 1, 1, 0, 1], "vertices": vertices,
        "triangles": [0, 1, 2, 2, 3, 0], "hull": 4, "edges": [0, 2, 2, 4, 4, 6, 6, 0]}}}}],
        "animations": {"idle": {"slots": {"art": {"attachment": [{"name": "body"}]}}}}}


def mesh(doc):
    return doc["skins"][0]["attachments"]["art"]["body"]


def selection():
    return ("default", "art", "body")


def policy(**fields):
    return {"rules": [{"skin": "default", "slot": "art", "attachment": "body", **fields}]}


def test_inventory_and_paged_weights():
    doc = rig()
    before = deepcopy(doc)
    report = inspect_meshes(doc)["meshes"][0]
    assert report["topology"]["continuous_surface"]
    assert report["topology"]["boundary_loops"] == 1
    assert report["topology"]["hull_edges_on_boundary"]
    assert report["unsorted_weight_vertices"] == [0, 1, 2, 3]
    weights = get_weights(doc, *selection(), offset=1, limit=1)
    assert weights["total_vertices"] == 4
    assert weights["vertices"] == [{"vertex": 1, "uv": [1, 0], "influences": [
        {"bone": "head", "x": 7, "y": -5, "weight": .25},
        {"bone": "root", "x": 10, "y": 0, "weight": .75}]}]
    assert doc == before


@pytest.mark.parametrize("offset,limit", [(-1, 1), (0, 0), (0, 257), (True, 1), (4, 1)])
def test_page_bounds(offset, limit):
    with pytest.raises(ValueError):
        get_weights(rig(), *selection(), offset, limit)


def test_weight_edit_normalizes_sorts_preserves_other_vertices_and_metadata():
    doc = rig()
    before = deepcopy(doc)
    result = set_weights(doc, *selection(), [{"vertex": 1, "weights": {"head": 8, "root": 2}}])
    values = get_weights(result, *selection(), 1, 1)["vertices"][0]["influences"]
    assert values == [{"bone": "root", "x": 10, "y": 0, "weight": .2},
                      {"bone": "head", "x": 7, "y": -5, "weight": .8}]
    original_rows = unpack_vertices(mesh(doc), doc["bones"])
    updated_rows = unpack_vertices(mesh(result), doc["bones"])
    for index in (0, 2, 3):
        assert {v["bone"]: v for v in updated_rows[index]} == {v["bone"]: v for v in original_rows[index]}
    assert inspect_meshes(result)["meshes"][0]["unsorted_weight_vertices"] == []
    assert {k: v for k, v in mesh(result).items() if k != "vertices"} == {k: v for k, v in mesh(doc).items() if k != "vertices"}
    assert doc == before


def test_rigid_patch_removes_zero_and_keeps_bind_coordinates():
    doc = set_weights(rig(), *selection(), [{"vertex": 0, "weights": {"root": 0, "head": 1}}])
    assert get_weights(doc, *selection(), 0, 1)["vertices"][0]["influences"] == [
        {"bone": "head", "x": -3, "y": -5, "weight": 1}]


@pytest.mark.parametrize("weights", [{}, {"head": 0}, {"head": -1}, {"head": True},
    {"head": float("nan")}, {"head": float("inf")}, {"absent": 1}, {"arm": 1}])
def test_invalid_weight_patch(weights):
    with pytest.raises(ValueError):
        set_weights(rig(), *selection(), [{"vertex": 0, "weights": weights}])


@pytest.mark.parametrize("updates", [[], [{"vertex": -1, "weights": {"head": 1}}],
    [{"vertex": True, "weights": {"head": 1}}], [{"vertex": 4, "weights": {"head": 1}}],
    [{"vertex": 0, "weights": {"head": 1}}] * 2,
    [{"vertex": 0, "weights": {"head": 1}, "extra": 1}]])
def test_invalid_patch_selection(updates):
    with pytest.raises(ValueError):
        set_weights(rig(), *selection(), updates)


@pytest.mark.parametrize("kind", ["deform", "ffd", "attachments", "linkedmesh", "sequence", "version"])
def test_unsupported_edits_fail_without_mutation(kind):
    doc = rig()
    if kind in {"deform", "ffd", "attachments"}:
        doc["animations"]["idle"][kind] = {"default": {}}
    elif kind == "linkedmesh":
        doc["skins"][0]["attachments"]["art"]["linked"] = {"type": "linkedmesh", "parent": "body"}
    elif kind == "sequence":
        mesh(doc)["sequence"] = {"count": 2}
    else:
        doc["skeleton"]["spine"] = "4.2.1"
    before = deepcopy(doc)
    with pytest.raises(ValueError):
        set_weights(doc, *selection(), [{"vertex": 0, "weights": {"head": 1}}])
    with pytest.raises(ValueError):
        replace_mesh(doc, *selection(), {k: mesh(doc)[k] for k in ("uvs", "vertices", "triangles", "hull")})
    assert doc == before


def test_pack_local_generator_and_large_weights():
    doc = rig()
    rows = [[{"bone": "head", "x": 1, "y": 2, "weight": 1e308},
             {"bone": "root", "x": 3, "y": 4, "weight": 1e308}]]
    assert pack_vertices(rows, doc["bones"]) == [2, 0, 3, 4, .5, 2, 1, 2, .5]
    rows[0].append(rows[0][0])
    with pytest.raises(ValueError):
        pack_vertices(rows, doc["bones"])


def test_legacy_unweighted_inspection_and_replacement():
    doc = rig()
    m = mesh(doc)
    geometry = {"uvs": m["uvs"], "vertices": [0, 0, 10, 0, 10, 10, 0, 10],
                "triangles": m["triangles"], "hull": 4}
    result = replace_mesh(doc, *selection(), geometry)
    assert "edges" not in mesh(result)
    assert mesh(result)["path"] == "painting"
    result["skins"] = {"default": result["skins"][0]["attachments"]}
    assert not inspect_meshes(result)["meshes"][0]["weighted"]
    assert get_weights(result, *selection(), 0, 1)["vertices"][0]["influences"][0]["bone"] == "root"
    with pytest.raises(ValueError):
        set_weights(result, *selection(), [{"vertex": 0, "weights": {"root": 1}}])


@pytest.mark.parametrize("change", ["unknown", "indices", "hull", "edges", "disconnected"])
def test_bad_replacement(change):
    doc = rig()
    geometry = {k: deepcopy(mesh(doc)[k]) for k in ("uvs", "vertices", "triangles", "hull")}
    if change == "unknown": geometry["path"] = "another-image"
    if change == "indices": geometry["triangles"][0] = 99
    if change == "hull": geometry["hull"] = 3
    if change == "edges": geometry["edges"] = [1, 2]
    if change == "disconnected": geometry["triangles"] = [0, 1, 2]
    with pytest.raises(ValueError):
        replace_mesh(doc, *selection(), geometry)


def test_point_connection_is_not_continuous_surface():
    report = topology({"uvs": [0, 0, 1, 0, 0, 1, -1, 0, 0, -1],
                       "triangles": [0, 1, 2, 0, 3, 4]})
    assert report["edge_components"] == 2
    assert report["nonmanifold_vertices"] == [0]
    assert not report["continuous_surface"]


def test_disconnected_duplicate_degenerate_and_nonmanifold():
    report = topology({"uvs": [0, 0, 1, 0, 0, 1, 2, 2, 3, 2, 2, 3, .5, 0],
                       "triangles": [0, 1, 2, 3, 4, 5, 0, 1, 2, 0, 1, 6]})
    assert report["edge_components"] == 2
    assert report["duplicate_triangles"] == [2]
    assert report["degenerate_uv_triangles"] == [3]
    assert [0, 1] in report["nonmanifold_edges"]
    assert not report["continuous_surface"]


def test_policy_budgets_rigidity_and_ancestor_isolation():
    doc = rig()
    assert validate_mesh_policy(doc, policy(continuous=True, max_vertices=4, max_influences=2))["valid"]
    assert not validate_mesh_policy(doc, policy(max_vertices=3))["valid"]
    assert not validate_mesh_policy(doc, policy(max_influences=1))["valid"]
    rigid = policy(regions=[{"vertices": [0], "rigid_bone": "head"}])
    assert not validate_mesh_policy(doc, rigid)["valid"]
    fixed = set_weights(doc, *selection(), [{"vertex": 0, "weights": {"head": 1}}])
    assert validate_mesh_policy(fixed, rigid)["valid"]
    rows = unpack_vertices(mesh(doc), doc["bones"])
    rows[0] = [{"bone": "cloth", "x": 0, "y": 0, "weight": 1}]
    mesh(doc)["vertices"] = pack_vertices(rows, doc["bones"])
    report = validate_mesh_policy(doc, policy(regions=[{"name": "cape", "vertices": [0],
        "allowed_bones": ["cloth"], "forbidden_ancestors": ["arm"]}]))
    assert not report["valid"]
    assert report["errors"][0]["message"] == "Region inherits a forbidden bone"


@pytest.mark.parametrize("region", [{"vertices": []}, {"vertices": [4], "rigid_bone": "head"},
    {"vertices": [0], "allowed_bones": ["typo"]}, {"vertices": [0], "rigid_bone": "typo"},
    {"vertices": [0, 0], "allowed_bones": ["head"]}, {"vertices": [0], "unknown": True}])
def test_policy_rejects_invalid_regions(region):
    with pytest.raises(ValueError):
        validate_mesh_policy(rig(), policy(regions=[region]))


def test_missing_selector_is_policy_failure():
    p = policy(continuous=True)
    p["rules"][0]["attachment"] = "typo"
    report = validate_mesh_policy(rig(), p)
    assert not report["valid"] and report["checked_meshes"] == 0


def test_hole_is_continuous_but_replacement_requires_single_boundary():
    doc = rig()
    geometry = {"uvs": [0, 0, 1, 0, 1, 1, 0, 1, .3, .3, .7, .3, .7, .7, .3, .7],
        "vertices": [0, 0, 10, 0, 10, 10, 0, 10, 3, 3, 7, 3, 7, 7, 3, 7], "hull": 4,
        "triangles": [0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7]}
    report = topology(geometry)
    assert report["continuous_surface"] and report["boundary_loops"] == 2
    with pytest.raises(ValueError, match="one boundary"):
        replace_mesh(doc, *selection(), geometry)


def test_duplicate_influences_in_unselected_vertex_are_rejected():
    doc = rig()
    mesh(doc)["vertices"][1] = 0
    with pytest.raises(ValueError, match="duplicate bone"):
        set_weights(doc, *selection(), [{"vertex": 1, "weights": {"head": 1}}])


def test_mesh_stdio_roundtrip_uses_new_job_and_preserves_source(tmp_path):
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    source = tmp_path / "source"
    source.mkdir()
    original = json.dumps(rig()).encode()
    (source / "rig.json").write_bytes(original)
    staging = tmp_path / "staging"

    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "spine_pipeline_mcp.server"],
            env={**os.environ, "SPINE_MCP_SOURCE_ROOT": str(source), "SPINE_MCP_STAGING_ROOT": str(staging)})
        async with Client(params) as client:
            async def call(name, args):
                result = await client.call_tool(name, args)
                assert not result.is_error, result
                return json.loads(next(c.text for c in result.content if c.type == "text"))
            a = await call("stage_json_copy", {"relative_path": "rig.json"})
            selected = {"skin": "default", "slot": "art", "attachment": "body"}
            await call("mesh_weights_get", {"job_id": a["job_id"], **selected, "limit": 1})
            b = await call("mesh_weights_set", {"job_id": a["job_id"], **selected,
                "updates": [{"vertex": 0, "weights": {"head": 1}}]})
            assert a["job_id"] != b["job_id"]
            inspected = await call("mesh_inspect", {"job_id": b["job_id"]})
            assert inspected["meshes"][0]["topology"]["continuous_surface"]
            report = await call("mesh_policy_validate", {"job_id": b["job_id"],
                "policy": policy(regions=[{"vertices": [0], "rigid_bone": "head"}])})
            assert report["valid"]
            assert (staging / a["job_id"] / "skeleton.json").read_bytes() == original
    asyncio.run(run())
    assert (source / "rig.json").read_bytes() == original
