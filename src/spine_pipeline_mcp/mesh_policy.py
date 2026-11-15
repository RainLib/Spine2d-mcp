"""Declarative project policies; character names and budgets stay with callers."""
from .mesh import require_valid, select_mesh, topology, unpack_vertices


def validate_mesh_policy(doc, policy):
    """Check explicit mesh selectors and per-vertex regions. No visual claims.

    A region supplies vertex indices and allowed_bones, rigid_bone and/or
    forbidden_ancestors. An ancestor ban includes that bone itself. These are
    stored-weight/hierarchy checks; constraints and deform need runtime checks.
    """
    require_valid(doc)
    if not isinstance(policy, dict) or set(policy) != {"rules"}:
        raise ValueError("Policy needs exactly a rules array")
    rules = policy["rules"]
    if not isinstance(rules, list) or not rules:
        raise ValueError("Policy rules must be nonempty")
    parents = {b["name"]: b.get("parent") for b in doc["bones"]}
    errors, checked = [], 0
    ancestors = {}
    for name in parents:
        lineage, at = set(), name
        while at is not None:
            lineage.add(at)
            at = parents[at]
        ancestors[name] = lineage

    def fail(index, message, **details):
        errors.append({"rule": index, "message": message, **details})

    def bone_list(value, label):
        if (not isinstance(value, list) or not value
                or any(not isinstance(v, str) or v not in parents for v in value)):
            raise ValueError(f"{label} must list existing bones")
        return set(value)

    for index, rule in enumerate(rules):
        selectors = {"skin", "slot", "attachment"}
        allowed = selectors | {"continuous", "max_vertices", "max_influences", "regions"}
        if (not isinstance(rule, dict) or not selectors <= rule.keys() or rule.keys() - allowed
                or any(not isinstance(rule[k], str) or not rule[k] for k in selectors)):
            raise ValueError("Each rule needs skin, slot, attachment and supported policy fields")
        if "continuous" in rule and type(rule["continuous"]) is not bool:
            raise ValueError("continuous must be boolean")
        for field in ("max_vertices", "max_influences"):
            if field in rule and (type(rule[field]) is not int or rule[field] < 1):
                raise ValueError(field + " must be a positive integer")
        try:
            mesh = select_mesh(doc, rule["skin"], rule["slot"], rule["attachment"])
        except ValueError as exc:
            fail(index, str(exc))
            continue
        checked += 1
        count = len(mesh["uvs"]) // 2
        rows = unpack_vertices(mesh, doc["bones"])
        if rows is None:
            bone = next(s["bone"] for s in doc["slots"] if s["name"] == rule["slot"])
            rows = [[{"bone": bone, "weight": 1}] for _ in range(count)]
        if rule.get("continuous") and not topology(mesh)["continuous_surface"]:
            fail(index, "Mesh is not one continuous indexed surface")
        if "max_vertices" in rule and count > rule["max_vertices"]:
            fail(index, "Vertex budget exceeded", actual=count, maximum=rule["max_vertices"])
        if "max_influences" in rule:
            bad = [i for i, row in enumerate(rows) if sum(v["weight"] > 0 for v in row) > rule["max_influences"]]
            if bad:
                fail(index, "Influence budget exceeded", vertices=bad)
        regions = rule.get("regions", [])
        if not isinstance(regions, list):
            raise ValueError("Regions must be an array")
        for region in regions:
            fields = {"name", "vertices", "allowed_bones", "rigid_bone", "forbidden_ancestors"}
            constraints = {"allowed_bones", "rigid_bone", "forbidden_ancestors"}
            if (not isinstance(region, dict) or region.keys() - fields or "vertices" not in region
                    or not region.keys() & constraints):
                raise ValueError("Each region needs vertices and at least one supported weight constraint")
            label = region.get("name", "region")
            if not isinstance(label, str):
                raise ValueError("Region name must be a string")
            vertices = region["vertices"]
            if (not isinstance(vertices, list) or not vertices
                    or any(type(v) is not int or not 0 <= v < count for v in vertices)
                    or len(set(vertices)) != len(vertices)):
                raise ValueError("Region vertices must be nonempty unique indices within mesh")
            allowed_bones = bone_list(region["allowed_bones"], "allowed_bones") if "allowed_bones" in region else None
            forbidden = bone_list(region["forbidden_ancestors"], "forbidden_ancestors") if "forbidden_ancestors" in region else set()
            rigid = region.get("rigid_bone")
            if "rigid_bone" in region and (not isinstance(rigid, str) or rigid not in parents):
                raise ValueError("rigid_bone must be an existing bone")
            disallowed, inherited, nonrigid = [], [], []
            for vertex in vertices:
                active = {v["bone"] for v in rows[vertex] if v["weight"] > 0}
                if allowed_bones is not None and active - allowed_bones:
                    disallowed.append(vertex)
                if any(ancestors[b] & forbidden for b in active):
                    inherited.append(vertex)
                if rigid is not None and active != {rigid}:
                    nonrigid.append(vertex)
            for bad, message in ((disallowed, "Region has forbidden direct weights"),
                                 (inherited, "Region inherits a forbidden bone"),
                                 (nonrigid, "Region is not rigidly bound to the specified bone")):
                if bad:
                    fail(index, message, region=label, vertices=bad)
    return {"valid": not errors, "checked_meshes": checked, "errors": errors,
            "scope": "Static weights, hierarchy and topology only; constraints, deform and motion require native verification"}
