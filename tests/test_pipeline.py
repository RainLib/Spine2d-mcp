import json
from pathlib import Path
import pytest
from spine_pipeline_mcp.core import Workspace
from spine_pipeline_mcp.pipeline import Pipeline

@pytest.fixture
def pipeline(tmp_path):
    source=tmp_path/'source';source.mkdir()
    (source/'pixel.png').write_bytes(b'synthetic-image-test')
    (source/'rig.json').write_text(json.dumps({'skeleton':{'spine':'4.3.26','images':'./'},'bones':[{'name':'root'}], 'skins':[{'name':'default','attachments':{'body':{'body':{'path':'pixel'}}}}]}))
    return Pipeline(Workspace(source,tmp_path/'staging'))

def test_stage_bundle(pipeline):
    before=(pipeline.ws.source/'rig.json').read_bytes()
    result=pipeline.stage_bundle('rig.json');job,doc=pipeline.read_job(result['job_id'])
    assert result['images']==1
    assert doc['skeleton']['images']=='images/'
    assert (job/'images/pixel.png').is_file()
    assert before==(pipeline.ws.source/'rig.json').read_bytes()

def test_transform_is_copy(pipeline):
    a=pipeline.stage_bundle('rig.json')
    b=pipeline.transform(a['job_id'],'test',lambda d:{**d,'animations':{'new':{}}})
    assert a['job_id']!=b['job_id']
    assert 'animations' not in pipeline.read_job(a['job_id'])[1]
    assert 'new' in pipeline.read_job(b['job_id'])[1]['animations']

def test_job_traversal_rejected(pipeline):
    with pytest.raises(ValueError):pipeline.read_job('../source')

def test_no_cli_config(pipeline,monkeypatch):
    monkeypatch.delenv('SPINE_MCP_CLI',raising=False)
    a=pipeline.stage_bundle('rig.json')
    with pytest.raises(ValueError):pipeline.export(a['job_id'])

@pytest.mark.parametrize('imagepath',['/etc','../../escape'])
def test_bundle_image_root_rejected(pipeline,imagepath):
    p=pipeline.ws.source/'rig.json';d=json.loads(p.read_text());d['skeleton']['images']=imagepath;p.write_text(json.dumps(d))
    with pytest.raises((ValueError,FileNotFoundError)):pipeline.stage_bundle('rig.json')

def test_missing_texture(pipeline):
    (pipeline.ws.source/'pixel.png').unlink()
    with pytest.raises(ValueError):pipeline.stage_bundle('rig.json')

def test_symlink_image(pipeline):
    p=pipeline.ws.source/'alias.png';p.symlink_to(pipeline.ws.source/'pixel.png')
    f=pipeline.ws.source/'rig.json';d=json.loads(f.read_text());d['skins'][0]['attachments']['body']['body']['path']='alias';f.write_text(json.dumps(d))
    with pytest.raises(ValueError):pipeline.stage_bundle('rig.json')
