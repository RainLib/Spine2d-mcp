# Changelog

## Plugin 0.2.2 — 2026-11-15

- All three Skills now use English throughout their instructions, reference documents, and interface metadata.
- English, Simplified Chinese, Japanese, and Korean README entry points link to each other from the repository root; the former Chinese documentation path links to `README_CN.md`.
- Repository plugin version 0.2.2 carries the updated Skills. The MCP server and published Registry bundle are version 0.2.1.

## 0.2.1 — 2026-11-15

- MCPB 0.4 UV bundle for public Registry distribution, with required source/staging configuration and optional native executable settings.
- Deterministic bundle packaging includes only public runtime files; no user settings, credentials, game assets or local environments.
- skills.sh repository grouping and public discovery/install entry points.

## 0.2.0 — 2026-11-15

- Three reusable authoring skills for optional PhotoCraft/Photoshop preparation, Spine rigging/animation, and runtime slots/skins integration.
- Codex and Claude Code repository marketplaces bundle the MCP with all three skills; installation guides also cover skills.sh and direct Git-based `uvx` use.
- Five mesh tools: source/job inventory, paged named weights, immutable weight edits, explicit geometry replacement and declarative project policies.
- Edge-connected topology checks include isolated triangles, bow-tie fans, nonmanifold edges, duplicate/degenerate triangles, winding and hull boundary diagnostics.
- Local Python `ProjectAdapter` validates project transforms before staging; custom character code stays outside the public package.
- Mesh edits require Spine 4.3.x and reject linked meshes/sequences/deform-dependent documents instead of silently invalidating them.
- Canonicalize every influence row in the edited attachment: sorting only a patched row can break native editor import of otherwise descending-order input. Unselected weights/bind coordinates are retained.
- JSON-only staged copies now use the common job skeleton filename, so they can feed animation/mesh edits without images.

## 0.1.0 (unreleased prototype)

- Official MCP SDK 2.3.0 stdio server with ten tools.
- Bounded JSON inspection, static bones/mesh/weights/timeline validation.
- Isolated JSON/image staging, immutable animation copying/linear retiming/key edits.
- Configured exact-version Spine CLI project/runtime export and isolated native Godot load/brief-sampling checks.
- Synthetic unit/transport tests; local opt-in native smoke evidence kept outside the public repository.
- No automatic rigging, weight painting, rendered preview or production publication.
