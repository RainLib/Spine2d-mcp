"""Explicit local Python extension seam; never imports project code from assets."""
from copy import deepcopy

from .mesh import inspect_meshes, require_valid
from .mesh_policy import validate_mesh_policy


class ProjectAdapter:
    """Compose the generic pipeline with trusted, locally registered validators.

    A validator receives a document copy and returns {valid: bool, ...}. A
    transformer receives a copy through Pipeline.transform. Callbacks are
    normal trusted Python, not a sandbox or dynamically loaded MCP plugins.
    """

    def __init__(self, pipeline, validators=()):
        self.pipeline = pipeline
        self.validators = tuple(validators)
        if any(not callable(v) for v in self.validators):
            raise ValueError("Validators must be explicitly registered callables")

    def check(self, doc, policy=None):
        report = inspect_meshes(doc)
        report["local_checks"] = []
        report["valid"] = report["validation"]["valid"]
        if not report["valid"]:
            return report
        if policy is not None:
            report["policy"] = validate_mesh_policy(doc, policy)
            report["valid"] &= report["policy"]["valid"]
        for validator in self.validators:
            check = validator(deepcopy(doc))
            if not isinstance(check, dict) or type(check.get("valid")) is not bool:
                raise ValueError("Local validator must return an object with a boolean valid field")
            report["local_checks"].append(check)
            report["valid"] &= check["valid"]
        return report

    def inspect(self, relative_path, policy=None):
        _, doc = self.pipeline.ws.read(relative_path)
        return self.check(doc, policy)

    def transform(self, job_id, operation, transformer, policy=None):
        """Validate local output before a new job is created; fail closed."""
        if not isinstance(operation, str) or not operation.strip() or len(operation) > 128:
            raise ValueError("Local operation needs a name of at most 128 characters")
        checks = None

        def checked(doc):
            nonlocal checks
            candidate = transformer(deepcopy(doc))
            require_valid(candidate)
            checks = self.check(candidate, policy)
            if not checks["valid"]:
                raise ValueError("Local transform failed project validation: " + str(checks))
            return candidate

        result = self.pipeline.transform(job_id, "local:" + operation, checked)
        return {**result, "checks": checks}
