import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from spine_pipeline_mcp.core import Workspace
from spine_pipeline_mcp.pipeline import Pipeline
from spine_pipeline_mcp.godot_check import validate_export

@pytest.fixture
def exported(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    pipeline = Pipeline(Workspace(source, tmp_path / "staging"))
    job = pipeline.new_job()
    runtime = job / "runtime"
    runtime.mkdir()
    (runtime / "rig.json").write_text('{"skeleton":{},"bones":[],"animations":{}}')
    (runtime / "rig.atlas").write_text('rig.png\nsize: 1,1\n')
    (runtime / "rig.png").write_bytes(b"synthetic test only")
    (job / "export-result.json").write_text(json.dumps({"runtime_directory": str(runtime)}))
    monkeypatch.setenv("SPINE_MCP_GODOT_EXECUTABLE", sys.executable)
    return pipeline, job


def test_isolated_project(exported, monkeypatch):
    pipeline, original = exported
    before = {p.name: p.read_bytes() for p in (original / "runtime").iterdir()}
    calls = []
    def run(args, **kw):
        calls.append(args)
        project = Path(kw['cwd'])
        assert project != original
        assert 'autoload' not in (project / 'project.godot').read_text()
        assert Path(kw['env']['HOME']).parent == project.parent
        if '--script' in args:
            (project / 'report.json').write_text(json.dumps({'initialized': True, 'errors': [], 'animations': []}))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(subprocess, 'run', run)
    result = validate_export(pipeline, original.name)
    assert result['ok']
    assert len(calls) == 3
    assert '--import' in calls[0]
    assert before == {p.name: p.read_bytes() for p in (original / "runtime").iterdir()}


def test_import_failure(exported, monkeypatch):
    pipeline, job = exported
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=2))
    result = validate_export(pipeline, job.name)
    assert not result['ok'] and 'check' not in result


def test_timeout(exported, monkeypatch):
    pipeline, job = exported
    def timeout(*a, **kw):
        raise subprocess.TimeoutExpired(a[0], 60)
    monkeypatch.setattr(subprocess, 'run', timeout)
    result = validate_export(pipeline, job.name)
    assert not result['ok'] and result['texture_import']['reason'] == 'timeout'


def test_missing_report_is_failure(exported, monkeypatch):
    pipeline, job = exported
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=0))
    assert not validate_export(pipeline, job.name)['ok']


def test_atlas_escape_rejected(exported):
    pipeline, job = exported
    (job / 'runtime/rig.atlas').write_text('../outside.png\nsize: 1,1\n')
    with pytest.raises(ValueError): validate_export(pipeline, job.name)


def test_manifest_escape_rejected(exported):
    pipeline, job = exported
    (job / 'export-result.json').write_text('{"runtime_directory":"/outside"}')
    with pytest.raises(ValueError): validate_export(pipeline, job.name)


def test_executable_required(exported, monkeypatch):
    pipeline, job = exported
    monkeypatch.delenv('SPINE_MCP_GODOT_EXECUTABLE')
    with pytest.raises(ValueError): validate_export(pipeline, job.name)


def test_zero_exit_error_log_is_failure(exported, monkeypatch):
    pipeline, job = exported
    def run(*args, **kwargs):
        kwargs['stdout'].write(b'ERROR: synthetic import failure\n')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(subprocess, 'run', run)
    result=validate_export(pipeline, job.name)
    assert not result['ok']
    assert result['texture_import']['errors']
