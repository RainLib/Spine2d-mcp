---
name: spine-asset-prep
description: "Prepare AI-generated or existing character art for Spine 2D. Discover optional PhotoCraft or Photoshop MCP tools and prefer an available editor for layers, state previews, and transparent PNG exports. Use for layered asset preparation and Spine handoff, not general photo editing."
---

# Spine Asset and Layer Preparation

Deliver an editable layered project, aligned assets, state previews, and a handoff record. Derive character decomposition, directories, and naming from the current task; this skill does not impose conventions from a particular game.

## Choose an available workflow

Discover the current session's tools and perform a read-only probe. PhotoCraft and Photoshop are **optional**: an installed application, a configured server, and a working MCP connection are three different states. Follow [editor discovery and operations](references/photo-tools.md).

- When a PhotoCraft or Photoshop MCP is callable, prefer it for AI assets, layers, masks, states, and exports. If both work, use the application the user specifies or the one associated with the existing editable project.
- If the application exists but its MCP is unavailable, state that limitation. Use a verified local CLI, script bridge, or user-specified UI workflow when available. CLI success does not establish MCP connectivity, and an absent optional plugin does not block the entire task.
- If neither editor is available, preserve the original images and provenance, and prepare a file handoff with relative paths. Use available image tools within the task's authorization. Do not claim to have created or inspected a layered project.

When new AI art is needed, use an available image-generation capability and retain the original output and prompt provenance. Read an image skill only when the task actually requires generating or editing images. Creating this skill does not itself initiate asset generation, application installation, or changes to an existing project.

## Organize the layered project

Inspect the user-specified document's layer tree, dimensions, unsaved changes, visible state, and preview. Preserve manual adjustments. Edit a copy or an explicit version instead of regenerating and overwriting the current project. Use reference-layer locking or hiding only when the actual interface supports it.

Organize layers around the required motion: a continuous body, parts that need independent movement, mutually exclusive states, equipment, and separate effects. A continuous body may have several editable source layers and still export as one texture. Layer count does not determine Spine mesh count. Do not automatically split every joint or force every character into a single mesh.

Keep original AI images traceable. Put masks, selections, color revisions, and separated parts in derived layers. When an image editor is available, use its engine for these raster operations. Local code may read pixels, analyze contours, compute hashes, and calculate geometry; those operations do not constitute layer editing. If hidden or rear surfaces need new artwork, create it within the user's authorization instead of stretching a mesh to invent missing content.

Use Layer Comps or equivalent states for the combinations actually required, such as open/closed mouths, equipped/empty hands, poses, or phases. Set correct defaults for mutually exclusive assets. Exclude original references, annotations, and debugging layers from runtime textures.

## Hand off to Spine

Read [handoff and alignment conventions](references/art-handoff.md) before exporting. Track transparency, canvas coordinates, crop offsets, anchors, scale, and draw order. Group exports may merge their children: inspect each output instead of treating a successful export as proof that every leaf layer was exported.

Save the native editable document. Export PSD as an additional interchange format when needed, then reopen it and compare layers and state previews. Record compatibility warnings for lossy features. Check the composite for every required state and each separate transparent PNG, and retain the actual file paths returned by the application.

The delivery record should identify original assets, editable projects, exported textures, coordinate metadata, and verified previews. For rigging, use `spine-rig-animation` if installed. Otherwise continue from the handoff record with available Spine tools; an optional companion skill must not become a blocker.
