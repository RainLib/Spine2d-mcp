# Handoff from Layers to Spine

Describe the actual assets without imposing a fixed character structure on the game. Reuse an existing manifest or create a JSON record with the fields below. This is a handoff convention, not an automatic import schema implemented by this MCP.

| Information | Purpose |
| --- | --- |
| Original relative image path, SHA-256, generation prompt or source | Distinguish originals, revisions, and exported textures |
| Editable project path, application/interface, and export version | Support further edits and reproducible exports |
| Canvas size, axis directions, Spine origin, and unit scale | Avoid treating canvas pixels as bone-local coordinates |
| Stable layer names, export paths, crop rectangles, and canvas anchors | Reconstruct placement after cropping |
| Required skin, slot, attachment keys, and draw order | Keep filenames, placeholders, and actual attachment names distinct |
| State combinations, default visibility, and mutual exclusions | Preserve mouth/prop states and the default pose |
| Image dimensions, export hashes, and preview paths | Bind validation to the exported textures rather than stale files |

Image coordinates commonly increase right/down, while skeleton coordinates increase right/up. For a simple origin-and-scale mapping, record and verify `spine_x=(canvas_x-origin_x)*scale` and `spine_y=(origin_y-canvas_y)*scale`. Record the actual transform when rotation, nonuniform scale, or rasterized transforms are involved; this simplified mapping no longer suffices.

Add crop offsets to points in cropped images to recover canvas coordinates before mapping them into the skeleton. Bone-local bind coordinates also require the inverse of the bone's world transform. A layer anchor is not automatically a Spine bone-local coordinate.

Higher layers usually draw in front in an image editor. Spine's exported slot array represents draw order according to its own format. Verify the imported preview instead of copying layer-panel indices. Groups, masks, and blend modes may have no equivalent at runtime; bake required effects into derived textures while preserving the editable master and documenting differences.

Compare the assembled character and each required state: occlusion, mouth alignment, transparent edges, prop grip points, foot baseline, and crop placement. Unchanged source pixels do not prove export alignment, and a matching composite does not prove that the layered file remains editable.

When using the official Photoshop-to-Spine script or another exporter, confirm naming tags and coordinate rules in that version's documentation. Do not invent syntax such as `[slot]`. The generic `stage_asset_bundle` tool consumes existing Spine JSON and images; it does not automatically convert PSD or `.pcraft` files into a complete skeleton.
