# Optional Editor Discovery and Operations

## Discovery

Search the current tool catalog by PhotoCraft/Photoshop name and description, then read the actual schemas. A host may expose `ALL_TOOLS` through `functions.exec`; other hosts provide their own discovery mechanisms. Do not infer parameters from tool names or invent Photoshop MCP commands.

If PhotoCraft exposes `session_list`, use it to verify read-only connectivity. An empty document list means the connection works. A `command_list` response with `needsDocument=true` or `disabledReason="no document open"` means a document must be opened first, not that the capability is absent. To inspect layer/state support, query `command_list(filter="layerComp")` and inspect the available `doc_export_layers`, `doc_inspect`, and preview tools.

If Photoshop exposes a document list, application status, or tool catalog, choose a read-only call to verify it. If no Photoshop tools are available, report only that this session has no discovered, usable Photoshop MCP. Do not infer that Photoshop is not installed. A connection configuration alone does not establish a successful call.

Record the application, interface type, probe result, and input/output scope used for this task. Recheck availability for each task; one machine's setup is not a universal default. Do not add mandatory `dependencies.tools` entries for optional editors.

## PhotoCraft workflow

Tool prefixes vary by host. These are capability names; consult the actual schemas before calling them.

| Task | Preferred interface and considerations |
| --- | --- |
| Identify open documents | `session_list`; inspect document ID/index, dimensions, and dirty state; preserve unsaved documents |
| Open or create | `doc_open` or `doc_new`; retain the returned index and explicitly target later operations |
| Inspect layers | `doc_inspect`; confirm layer IDs, hierarchy, visibility, and top-to-bottom order |
| Edit layers or masks | Discover commands and parameters with `command_list`, then use `command_run`; batches are not atomic, so completed steps may persist after a failure |
| Place original images | Use `doc_place` if available to retain traceable content in the working copy; do not assume Smart Object support |
| Manage state combinations | Use `layerComp.new/list/apply` when exposed; check missing layers and the default state |
| Preview a state | `doc_render_preview` or `render_preview`; image mode and bridge mode have different parameters |
| Save | Save `.pcraft` to a new path with `doc_save`; record PSD compatibility warnings and inspect an actual composite for the assembled preview |
| Export layers | `doc_export_layers` exports top-level layers and merges groups; inspect both `files` and `skipped` |

File operations respect the MCP server's read/write roots. Do not silently reinterpret a project-relative path as a server-root path. Establish the mapping from returned state, known startup configuration, or an explicit path error. Do not automatically broaden access.

The default `visible_only=true` skips hidden states. Export mutually exclusive states using the confirmed layer combinations in separate passes, or explicitly select layers in an isolated export copy. Exclude reference layers. One default export does not necessarily include both open and closed mouth states.

Reopen exported files when needed to check coordinates, compositing, transparent edges, and states. Reopening changes the active document, so subsequent operations must use explicit target IDs. Preserve the documents the user originally had open.

## Photoshop and fallback workflows

Keep the same outcome requirements: inspect the document, preserve editable sources, manage layers/states, export transparent assets, and verify by reopening. Obtain commands from the discovered Photoshop MCP documentation. PhotoCraft command IDs are not Photoshop commands.

If the project already maintains a Photoshop export script or official bridge workflow, inspect its version, output coordinates, and side effects before using it. Do not apply an unknown downloaded script directly to the current project. Without a verified bridge, continue preparing files, the layer plan, and Spine coordinates, and identify the unfinished editor steps. Request missing information when essential inputs such as original artwork are absent, not repeatedly because an optional MCP is unavailable.
