"""Pure mesh inspection and copy-on-write editing; no artwork or engine dependency.

Selectors always use (skin, slot, attachment map key). Bind coordinates are
bone-local. Editing weights does not compensate or promise an unchanged pose.
"""
from collections import defaultdict
from copy import deepcopy
import math
import re

from .animation import _number
from .pipeline import attachments
from .validation import validate_document


def require_valid(doc):
    report = validate_document(doc)
    if not report["valid"]:
        first = report["errors"][0]
        raise ValueError(f"Invalid skeleton at {first['path']}: {first['message']}")


def select_mesh(doc, skin, slot, attachment):
    matches = [data for s, t, a, data in attachments(doc)
               if (s, t, a) == (skin, slot, attachment)]
    if len(matches) != 1 or matches[0].get("type") != "mesh":
        raise ValueError("Selector must resolve to exactly one concrete mesh")
    return matches[0]


def unpack_vertices(mesh, bones):
    """Decode validated weighted vertices to named influences, or return None."""
    raw = mesh["vertices"]
    if len(raw) == len(mesh["uvs"]):
        return None
    rows, cursor = [], 0
    for _ in range(len(mesh["uvs"]) // 2):
        count = raw[cursor]
        cursor += 1
        row = []
        for _ in range(count):
            index, x, y, weight = raw[cursor:cursor + 4]
            row.append({"bone": bones[index]["name"], "x": x, "y": y, "weight": weight})
            cursor += 4
        rows.append(row)
    return rows


def pack_vertices(rows, bones):
    """Encode named influences, normalized and sorted by skeleton bone index.

    Local authoring adapters can generate coordinates/weights themselves and
    pass the resulting array to replace_mesh. Zero influences are omitted.
    """
    indices = {b["name"]: i for i, b in enumerate(bones)}
    if len(indices) != len(bones):
        raise ValueError("Duplicate bone names")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Expected nonempty vertex influence rows")
    packed = []
    for row in rows:
        if not isinstance(row, list) or not row:
            raise ValueError("Each vertex needs influences")
        seen, values = set(), []
        for value in row:
            if not isinstance(value, dict) or set(value) != {"bone", "x", "y", "weight"}:
                raise ValueError("Influence needs exactly bone, x, y and weight")
            bone = value["bone"]
            if not isinstance(bone, str) or bone not in indices or bone in seen:
                raise ValueError("Unknown or duplicate influence bone")
            seen.add(bone)
            x, y = _number(value["x"], "x"), _number(value["y"], "y")
            weight = _number(value["weight"], "weight")
            if weight < 0:
                raise ValueError("Weights cannot be negative")
            if weight > 0:
                values.append((indices[bone], x, y, weight))
        # Scale first to avoid overflow when normalizing large finite values.
        maximum = max((v[3] for v in values), default=0)
        if maximum <= 0:
            raise ValueError("A vertex must retain positive weight")
        total = math.fsum(v[3] / maximum for v in values)
        normalized = [(i, x, y, (w / maximum) / total) for i, x, y, w in values]
        normalized = [v for v in normalized if v[3] > 0]
        packed.append(len(normalized))
        for value in sorted(normalized):
            packed.extend(value)
    return packed


def _components(nodes, neighbors):
    remaining, sizes = set(nodes), []
    while remaining:
        stack = [remaining.pop()]
        size = 0
        while stack:
            node = stack.pop()
            size += 1
            found = remaining.intersection(neighbors.get(node, ()))
            remaining.difference_update(found)
            stack.extend(found)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def topology(mesh):
    """Report indexed topology in UV space; not animated/visible continuity.

    Triangles connected only at a point are separate edge components. Vertex
    fans are checked independently so a bow-tie inside a larger surface is
    still reported. Geometric self-intersections are not tested.
    """
    uvs, indices = mesh["uvs"], mesh["triangles"]
    count = len(uvs) // 2
    triangles = [indices[i:i + 3] for i in range(0, len(indices), 3)]
    edges, incident = defaultdict(list), defaultdict(set)
    neighbors, boundary = defaultdict(set), defaultdict(set)
    duplicates, degenerate, seen = [], [], set()
    for number, (a, b, c) in enumerate(triangles):
        key = tuple(sorted((a, b, c)))
        if key in seen:
            duplicates.append(number)
        seen.add(key)
        ax, ay, bx, by, cx, cy = [uvs[v * 2 + offset] for v in (a, b, c) for offset in (0, 1)]
        area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        if not math.isfinite(area) or abs(area) <= 1e-12:
            degenerate.append(number)
        for x, y in ((a, b), (b, c), (c, a)):
            edges[tuple(sorted((x, y)))].append((number, x, y))
            incident[x].add(number)
    nonmanifold_edges, inconsistent_edges = [], []
    # Per-vertex triangle adjacency tests the connected fan around each vertex.
    fans = defaultdict(lambda: defaultdict(set))
    for edge, faces in edges.items():
        first = faces[0][0]
        for number, _, _ in faces[1:]:
            neighbors[first].add(number)
            neighbors[number].add(first)
            for vertex in edge:
                fans[vertex][first].add(number)
                fans[vertex][number].add(first)
        if len(faces) == 1:
            x, y = edge
            boundary[x].add(y)
            boundary[y].add(x)
        elif len(faces) > 2:
            nonmanifold_edges.append(list(edge))
        elif faces[0][1:] == faces[1][1:]:
            inconsistent_edges.append(list(edge))
    components = _components(range(len(triangles)), neighbors)
    nonmanifold_vertices = [v for v, faces in incident.items()
                            if len(_components(faces, fans[v])) != 1
                            or (v in boundary and len(boundary[v]) != 2)]
    boundary_loops = (len(_components(boundary, boundary))
                      if all(len(n) == 2 for n in boundary.values()) else None)
    unused = sorted(set(range(count)) - incident.keys())
    hull = mesh.get("hull", 0)
    hull_valid = isinstance(hull, int) and not isinstance(hull, bool) and 0 <= hull <= count
    hull_matches = (all(tuple(sorted((i, (i + 1) % hull))) in edges
                        and len(edges[tuple(sorted((i, (i + 1) % hull)))]) == 1
                        for i in range(hull)) if hull_valid and hull >= 3 else None)
    return {"vertices": count, "triangles": len(triangles), "edge_components": len(components),
            "component_triangle_counts": components, "boundary_loops": boundary_loops,
            "unused_vertices": unused, "duplicate_triangles": duplicates,
            "degenerate_uv_triangles": degenerate, "nonmanifold_edges": nonmanifold_edges,
            "nonmanifold_vertices": sorted(nonmanifold_vertices), "inconsistent_winding_edges": inconsistent_edges,
            "hull_vertices": hull, "hull_valid": hull_valid, "hull_edges_on_boundary": hull_matches,
            "continuous_surface": len(components) == 1 and not any((unused, duplicates, degenerate,
                nonmanifold_edges, nonmanifold_vertices, inconsistent_edges))}


def inspect_meshes(doc):
    """Inventory every concrete/linked attachment, including inactive skins."""
    validation = validate_document(doc)
    result = {"validation": validation, "meshes": [], "linked_meshes": [],
              "scope": "Static indexed topology and stored weights; not visual or animated quality"}
    if not validation["valid"]:
        return result
    bone_indices = {b["name"]: i for i, b in enumerate(doc["bones"])}
    for skin, slot, name, mesh in attachments(doc):
        selector = {"skin": skin, "slot": slot, "attachment": name}
        if mesh.get("type") == "linkedmesh":
            result["linked_meshes"].append({**selector, "resolved": False})
        if mesh.get("type") != "mesh":
            continue
        rows = unpack_vertices(mesh, doc["bones"])
        result["meshes"].append({**selector, "path": mesh.get("path", mesh.get("name", name)),
            "weighted": rows is not None, "topology": topology(mesh),
            "max_influences": max(map(len, rows)) if rows else 1,
            "influence_bones": sorted({v["bone"] for row in rows for v in row}) if rows else [],
            "unsorted_weight_vertices": [i for i, row in enumerate(rows or [])
                if [v["bone"] for v in row] != sorted((v["bone"] for v in row),
                   key=bone_indices.__getitem__)]})
    return result


def get_weights(doc, skin, slot, attachment, offset=0, limit=100):
    require_valid(doc)
    if (type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 256):
        raise ValueError("Offset must be nonnegative; limit must be 1..256")
    mesh = select_mesh(doc, skin, slot, attachment)
    rows = unpack_vertices(mesh, doc["bones"])
    count = len(mesh["uvs"]) // 2
    if offset >= count:
        raise ValueError("Vertex offset is outside mesh")
    slot_bone = next(s["bone"] for s in doc["slots"] if s["name"] == slot)
    return {"skin": skin, "slot": slot, "attachment": attachment, "weighted": rows is not None,
            "total_vertices": count, "offset": offset,
            "vertices": [{"vertex": i, "uv": mesh["uvs"][i * 2:i * 2 + 2],
                "influences": rows[i] if rows is not None else [{"bone": slot_bone,
                    "x": mesh["vertices"][i * 2], "y": mesh["vertices"][i * 2 + 1], "weight": 1}]}
                for i in range(offset, min(count, offset + limit))]}


def _editable(doc):
    require_valid(doc)
    version = doc["skeleton"].get("spine", "")
    if not isinstance(version, str) or not re.fullmatch(r"4\.3\.[0-9]+", version):
        raise ValueError("Mesh editing currently requires Spine 4.3.x")
    for _, _, _, data in attachments(doc):
        if data.get("type") == "linkedmesh" or data.get("sequence"):
            raise ValueError("Mesh editing rejects documents with linked meshes or image sequences")
    for animation in doc.get("animations", {}).values():
        if any(animation.get(key) for key in ("deform", "ffd", "attachments")):
            raise ValueError("Mesh editing rejects deform/FFD/attachment timelines; remapping is not implemented")


def _canonical_vertices(mesh):
    """Sort every row consistently, without changing bind values or weights.

    Native editor import can fail when just one row is sorted in an otherwise
    descending/mixed-order attachment. No deform data is allowed on this path.
    """
    raw = mesh["vertices"]
    if len(raw) == len(mesh["uvs"]):
        return raw
    result, cursor = [], 0
    while cursor < len(raw):
        count = raw[cursor]
        rows = [raw[cursor + 1 + j * 4:cursor + 5 + j * 4] for j in range(count)]
        if len({row[0] for row in rows}) != count:
            raise ValueError("Cannot edit duplicate bone influences")
        result.append(count)
        for row in sorted(rows, key=lambda row: row[0]):
            result.extend(row)
        cursor += 1 + count * 4
    return result


def set_weights(doc, skin, slot, attachment, updates):
    """Replace selected vertices' existing influences; keep their bind x/y.

    Each update is {vertex: int, weights: {bone_name: nonnegative weight}}.
    Unlisted influences at that vertex are removed. Other vertices retain their
    weights/bind coordinates; all rows in this mesh use canonical bone order.
    New bone bindings need explicit local coordinates through replace_mesh.
    """
    _editable(doc)
    mesh = select_mesh(doc, skin, slot, attachment)
    rows = unpack_vertices(mesh, doc["bones"])
    if rows is None:
        raise ValueError("Weight edits require a weighted mesh; use replace_mesh for explicit binding")
    if not isinstance(updates, list) or not updates or len(updates) > len(rows):
        raise ValueError("Expected nonempty updates, at most one per vertex")
    seen = set()
    replacements = {}
    for update in updates:
        if not isinstance(update, dict) or set(update) != {"vertex", "weights"}:
            raise ValueError("Update needs exactly vertex and weights")
        vertex, weights = update["vertex"], update["weights"]
        if type(vertex) is not int or not 0 <= vertex < len(rows) or vertex in seen:
            raise ValueError("Duplicate or out-of-range vertex")
        seen.add(vertex)
        current = {v["bone"]: v for v in rows[vertex]}
        if len(current) != len(rows[vertex]):
            raise ValueError("Cannot edit duplicate bone influences")
        if not isinstance(weights, dict) or not weights or any(b not in current for b in weights):
            raise ValueError("Weights must select existing vertex bindings; new bones need explicit bind coordinates")
        replacements[vertex] = pack_vertices([[{**current[b], "weight": w} for b, w in weights.items()]], doc["bones"])
    # Preserve unselected values, then canonicalize the whole attachment's order.
    raw, packed, cursor = mesh["vertices"], [], 0
    for vertex in range(len(rows)):
        end = cursor + 1 + raw[cursor] * 4
        packed.extend(replacements.get(vertex, raw[cursor:end]))
        cursor = end
    result = deepcopy(doc)
    updated = select_mesh(result, skin, slot, attachment)
    updated["vertices"] = packed
    updated["vertices"] = _canonical_vertices(updated)
    require_valid(result)
    return result


def replace_mesh(doc, skin, slot, attachment, geometry):
    """Replace explicit geometry in a copy, retaining texture/slot metadata.

    Local alpha-contour/grid/rig generators supply geometry. UVs, triangles,
    vertices and hull are required; edges optional. No source image is edited.
    """
    _editable(doc)
    required = {"uvs", "triangles", "vertices", "hull"}
    if not isinstance(geometry, dict) or not required <= geometry.keys() or geometry.keys() - required - {"edges"}:
        raise ValueError("Geometry needs uvs, triangles, vertices, hull; only edges is optional")
    result = deepcopy(doc)
    mesh = select_mesh(result, skin, slot, attachment)
    mesh.pop("edges", None)
    mesh.update(deepcopy(geometry))
    require_valid(result)
    mesh["vertices"] = _canonical_vertices(mesh)
    report = topology(mesh)
    if (not report["continuous_surface"] or report["boundary_loops"] != 1
            or not report["hull_valid"] or report["hull_edges_on_boundary"] is not True):
        raise ValueError("Replacement needs one continuous surface, one boundary, and its hull vertices ordered first")
    edges = mesh.get("edges", [])
    # Spine nonessential edges use offsets into coordinate pairs (2 * vertex).
    if (not isinstance(edges, list) or len(edges) % 2
            or any(type(v) is not int or v < 0 or v % 2 or v >= len(mesh["uvs"]) for v in edges)):
        raise ValueError("Edges must be pairs of even coordinate offsets in vertex range")
    return result
