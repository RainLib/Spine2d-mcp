from copy import deepcopy
import json

import pytest

from spine_pipeline_mcp.adapter import ProjectAdapter
from spine_pipeline_mcp.core import Workspace
from spine_pipeline_mcp.mesh import set_weights
from spine_pipeline_mcp.pipeline import Pipeline
from test_mesh import rig, policy, selection


@pytest.fixture
def adapter(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "rig.json").write_text(json.dumps(rig()))
    return ProjectAdapter(Pipeline(Workspace(source, tmp_path / "staging")))


def test_local_transform_and_policy(adapter):
    before = (adapter.pipeline.ws.source / "rig.json").read_bytes()
    a = adapter.pipeline.ws.stage("rig.json")
    b = adapter.transform(a["job_id"], "protect_face", lambda doc: set_weights(doc, *selection(),
        [{"vertex": 0, "weights": {"head": 1}}]),
        policy(regions=[{"vertices": [0], "rigid_bone": "head"}]))
    assert b["checks"]["valid"]
    assert b["operation"] == "local:protect_face"
    assert (adapter.pipeline.ws.source / "rig.json").read_bytes() == before
    assert (adapter.pipeline.job(a["job_id"]) / "skeleton.json").read_bytes() == before


def test_failed_local_validator_does_not_create_job(adapter):
    a = adapter.pipeline.ws.stage("rig.json")
    adapter.validators = (lambda doc: {"valid": False, "reason": "Missing local socket"},)
    with pytest.raises(ValueError, match="failed project validation"):
        adapter.transform(a["job_id"], "custom", lambda doc: doc)
    assert len(list(adapter.pipeline.ws.staging.iterdir())) == 1


def test_validators_cannot_mutate_candidate(adapter):
    def local_check(doc):
        doc["bones"].clear()
        return {"valid": True}
    adapter.validators = (local_check,)
    original = rig()
    before = deepcopy(original)
    assert adapter.check(original)["valid"]
    assert original == before
    a = adapter.pipeline.ws.stage("rig.json")
    b = adapter.transform(a["job_id"], "custom", lambda doc: doc)
    assert adapter.pipeline.read_job(b["job_id"])[1] == before


def test_local_validators_fail_closed(adapter):
    adapter.validators = (lambda doc: {"valid": "yes"},)
    with pytest.raises(ValueError, match="boolean"):
        adapter.inspect("rig.json")


def test_source_json_copy_can_feed_generic_transforms(adapter):
    a = adapter.pipeline.ws.stage("rig.json")
    b = adapter.pipeline.transform(a["job_id"], "copy", lambda doc: doc)
    assert adapter.pipeline.read_job(b["job_id"])[1] == rig()
