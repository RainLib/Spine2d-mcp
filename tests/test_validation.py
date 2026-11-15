from copy import deepcopy
import pytest
from spine_pipeline_mcp.validation import validate_document


def rig(weighted=False):
    mesh = {"type": "mesh", "uvs": [0, 0, 1, 0, 0, 1], "triangles": [0, 1, 2],
            "vertices": [0, 0, 1, 0, 0, 1]}
    if weighted:
        mesh["vertices"] = [1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1]
    return {"skeleton": {"spine": "4.3.26"}, "bones": [{"name": "root"}],
            "slots": [{"name": "art", "bone": "root"}],
            "skins": [{"name": "default", "attachments": {"art": {"body": mesh}}}],
            "animations": {"idle": {"bones": {"root": {"rotate": [{"value": 0}, {"time": 1, "value": 2}]}}}}}


def mesh(doc):
    return doc["skins"][0]["attachments"]["art"]["body"]


@pytest.mark.parametrize('weighted', [False, True])
def test_valid_mesh_and_no_mutation(weighted):
    doc = rig(weighted)
    before = deepcopy(doc)
    result = validate_document(doc)
    assert result['valid']
    assert result['counts']['meshes'] == 1
    assert result['counts']['weighted_meshes'] == int(weighted)
    assert doc == before


def test_legacy_skin():
    doc = rig()
    doc['skins'] = {'default': doc['skins'][0]['attachments']}
    assert validate_document(doc)['valid']


@pytest.mark.parametrize('change', ['duplicate', 'cycle', 'parent', 'slot', 'animation'])
def test_bone_references(change):
    doc = rig()
    if change == 'duplicate': doc['bones'].append({'name': 'root'})
    elif change == 'cycle': doc['bones'][0]['parent'] = 'root'
    elif change == 'parent': doc['bones'][0]['parent'] = 'absent'
    elif change == 'slot': doc['slots'][0]['bone'] = 'absent'
    else: doc['animations']['idle']['bones']['absent'] = {}
    assert not validate_document(doc)['valid']


@pytest.mark.parametrize('time', [-1, float('nan'), float('inf'), True, 0])
def test_invalid_times(time):
    doc = rig()
    doc['animations']['idle']['bones']['root']['rotate'][1]['time'] = time
    assert not validate_document(doc)['valid']


@pytest.mark.parametrize('change', ['uv_odd', 'uv_nan', 'triangle_range', 'triangle_bool', 'triangle_count', 'triangle_duplicate', 'weight_sum', 'weight_negative', 'index', 'truncated', 'extra', 'count'])
def test_mesh_errors(change):
    doc = rig(True)
    m = mesh(doc)
    if change == 'uv_odd': m['uvs'].append(0)
    elif change == 'uv_nan': m['uvs'][0] = float('nan')
    elif change == 'triangle_range': m['triangles'][0] = 3
    elif change == 'triangle_bool': m['triangles'][0] = True
    elif change == 'triangle_count': m['triangles'].pop()
    elif change == 'triangle_duplicate': m['triangles'][0] = 1
    elif change == 'weight_sum': m['vertices'][4] = .5
    elif change == 'weight_negative': m['vertices'][4] = -1
    elif change == 'index': m['vertices'][1] = 9
    elif change == 'truncated': m['vertices'].pop()
    elif change == 'extra': m['vertices'].append(1)
    elif change == 'count': m['vertices'][0] = 0
    assert not validate_document(doc)['valid']


def test_multiple_mesh_warning():
    doc = rig()
    doc['skins'][0]['attachments']['art']['other'] = deepcopy(mesh(doc))
    result = validate_document(doc)
    assert result['valid']
    assert result['counts']['attachments'] == 2
    assert result['warnings']


@pytest.mark.parametrize('doc', [None, [], {'bones': None}, {'slots': [None]}, {'skins': [None]}, {'animations': None}])
def test_malformed_containers(doc):
    assert not validate_document(doc)['valid']
