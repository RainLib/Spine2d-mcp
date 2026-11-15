import asyncio
import json
import os
import sys
from pathlib import Path
import pytest
from spine_pipeline_mcp.core import Workspace

@pytest.fixture
def ws(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'rig.json').write_text(json.dumps({'skeleton': {'spine': '4.3.26'}, 'bones': [{'name':'root'}], 'animations': {'idle': {}}}))
    return Workspace(source, tmp_path / 'staging')

def test_inspect(ws):
    assert ws.inspect('rig.json')['animations'] == ['idle']

def test_stage_no_source_change(ws):
    original = (ws.source / 'rig.json').read_bytes()
    a, b = ws.stage('rig.json'), ws.stage('rig.json')
    assert a['job_id'] != b['job_id']
    assert Path(a['staged_path']).read_bytes() == original
    assert (ws.source / 'rig.json').read_bytes() == original

@pytest.mark.parametrize('path', ['../rig.json', '/etc/passwd', 'missing.json', '.'])
def test_path_rejected(ws, path):
    with pytest.raises((ValueError, FileNotFoundError)):
        ws.inspect(path)

def test_symlink_rejected(ws):
    (ws.source / 'link.json').symlink_to(ws.source / 'rig.json')
    with pytest.raises(ValueError): ws.inspect('link.json')

def test_overlap_rejected(ws):
    with pytest.raises(ValueError): Workspace(ws.source, ws.source / 'out')

def test_bad_json(ws):
    (ws.source / 'bad.json').write_text('{}')
    with pytest.raises(ValueError): ws.inspect('bad.json')

def test_limit(ws, monkeypatch):
    monkeypatch.setattr('spine_pipeline_mcp.core.MAX_BYTES', 2)
    with pytest.raises(ValueError): ws.inspect('rig.json')

def test_stdio_roundtrip(ws):
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
    async def run():
        params = StdioServerParameters(command=sys.executable, args=['-m', 'spine_pipeline_mcp.server'], env={**os.environ, 'SPINE_MCP_SOURCE_ROOT':str(ws.source), 'SPINE_MCP_STAGING_ROOT':str(ws.staging)})
        async with Client(params) as client:
            tools = await client.list_tools()
            assert {t.name for t in tools.tools} == {'skeleton_inspect', 'stage_json_copy', 'skeleton_validate', 'stage_asset_bundle', 'job_validate', 'animation_copy', 'animation_retime', 'bone_keys_set', 'spine_export', 'godot_validate', 'mesh_inspect', 'mesh_weights_get', 'mesh_weights_set', 'mesh_replace', 'mesh_policy_validate'}
            result = await client.call_tool('skeleton_inspect', {'relative_path':'rig.json'})
            assert not result.is_error
            staged = await client.call_tool('stage_json_copy', {'relative_path':'rig.json'})
            assert not staged.is_error
            denied = await client.call_tool('skeleton_inspect', {'relative_path':'../outside.json'})
            assert denied.is_error
    asyncio.run(run())


def test_special_file_rejected(ws):
    os.mkfifo(ws.source / 'pipe.json')
    with pytest.raises(ValueError): ws.inspect('pipe.json')


def test_invalid_animations(ws):
    (ws.source / 'bad.json').write_text(json.dumps({'skeleton': {}, 'bones': [], 'animations': None}))
    with pytest.raises(ValueError): ws.inspect('bad.json')
