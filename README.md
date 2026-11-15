# Spine Pipeline MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**A local, staging-first MCP foundation for Spine asset pipelines.**

[中文说明](docs/README.zh-CN.md) · [Architecture](docs/architecture.md) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)

> **Early prototype, project version 0.1.0.** This repository uses the official Python MCP SDK **2.3.0**. That SDK version is not a claim of “MCP protocol 2.0”, FastMCP 2.x, or project version 2.0. Only the two tools below are implemented.

## What works today

| Tool | Behavior | Writes |
| --- | --- | --- |
| `skeleton_inspect` | Inspect JSON version, bone names, animation names, SHA-256; warn on duplicate bones and missing parents | None |
| `stage_json_copy` | Copy one validated JSON byte-for-byte into a fresh UUID job directory | Staging only |

Basic structure checking is **not** full Spine validation. A successful inspection does not prove that a skeleton loads, weights deform correctly, animation looks good, or a runtime version is compatible.

### Not implemented

- Spine editor GUI control or live timeline/weight-paint editing
- Spine CLI import/export, `.spine` binary inspection, atlas/texture copying
- Motion generation, mesh/weight/constraint editing, GIF or engine previews
- Publishing output back into a game, background jobs, remote HTTP hosting

No Spine executable, commercial assets, proprietary project files, or game-specific scripts are included. The example fixture is synthetic test data, not a production rig.

## Quick start

Requirements: Python **3.11+**, [uv](https://docs.astral.sh/uv/), and an MCP client supporting stdio. You do **not** need Spine installed to use the current JSON-only tools.

```sh
git clone https://github.com/RainLib/spine-pipeline-mcp.git
cd spine-pipeline-mcp
uv sync --locked
uv run --locked pytest -q

SPINE_MCP_SOURCE_ROOT="$PWD/examples/source" \
SPINE_MCP_STAGING_ROOT="$PWD/.staging" \
uv run --locked spine-pipeline-mcp
```

The last command starts a stdio MCP server waiting for a client; it is not an interactive CLI. Stop it with Ctrl-C. Start with the synthetic sample or your own **test copies**, not a production asset root.

### MCP client configuration

Adapt this JSON to your client's MCP settings. Replace every placeholder with an actual absolute path. If the client cannot find `uv`, use its absolute executable path.

```json
{
  "mcpServers": {
    "spine-pipeline": {
      "command": "uv",
      "args": ["--directory", "/path/to/spine-pipeline-mcp", "run", "--locked", "spine-pipeline-mcp"],
      "env": {
        "SPINE_MCP_SOURCE_ROOT": "/path/to/spine-pipeline-mcp/examples/source",
        "SPINE_MCP_STAGING_ROOT": "/path/to/spine-pipeline-mcp/.staging"
      }
    }
  }
}
```

Example calls for either tool:

```json
{"relative_path": "minimal.json"}
```

Both root variables are required. Source must already exist. Source and staging must be separate and neither may contain the other. Tools fail closed if the configuration is absent or invalid. Source paths must be relative to the configured source root.

## Architecture

```text
MCP client
    │ stdio (no listening port)
    ▼
Official Python MCP SDK server
    ├── skeleton_inspect ──► read-only source root
    └── stage_json_copy ──► new staging/<uuid>/source.json
                              (never overwrites source)
```

`server.py` is the protocol layer; `core.py` handles bounded reads, basic JSON checks and isolated copies. A future pipeline can add game-specific adapters around this core without embedding project paths or exposing arbitrary shell commands. See [the architecture and roadmap](docs/architecture.md).

**Why Python rather than Go?** Python makes it straightforward to reuse image processing, NumPy/Pillow mesh work, JSON transforms and validation scripts in existing art pipelines. Go has attractive binary distribution, but requiring a Python worker for those operations would add another boundary before it adds value. This foundation deliberately prioritizes iteration and testability over a standalone binary.

## Safety model

- Explicit read root, JSON/`.spine-json` files only, 16 MiB per-file limit.
- Reject absolute paths, parent traversal, symlinks, and non-regular files.
- UUID staging directories, exclusive file creation, no overwrite/delete/publish tools.
- No arbitrary shell, Spine execution, network listener, credential requirement or automatic client configuration.
- Tool descriptions and annotations aid clients; they are not authorization enforcement.

This is **not an OS sandbox** and does not defend against a hostile local process changing directories/mounts during a request. Use trusted directories. JSON and tool output remain untrusted data; do not follow instructions embedded in asset metadata. Staging has no automatic retention/quota policy, so repeated copies can consume disk space. Delete expendable staging copies yourself after inspection. See [SECURITY.md](SECURITY.md).

## Testing and compatibility

Tests use synthetic temporary copies, never user assets. They cover successful inspection, unchanged source hashes, unique staging jobs, malformed input, size limits, traversal/symlink rejection, and real stdio MCP initialization/list/call round trips.

An inactive [CI template](docs/ci-workflow.yml.example) is provided for Linux with Python 3.11 and 3.12, plus a package build. **Hosted CI is not enabled or verified yet**: the publishing credential cannot write GitHub workflows. A maintainer with appropriate access can place this template at `.github/workflows/ci.yml` and inspect the resulting run. The initial implementation was also tested locally on macOS ARM with Python 3.12. Neither this nor the version string in the sample establishes compatibility with any Spine editor/runtime release.

## License and third-party software

Project code and synthetic examples: [MIT](LICENSE). Dependencies retain their own licenses. **Spine is commercial software by Esoteric Software and is not bundled or licensed by this project.** Future CLI integrations require a separately installed, appropriately licensed copy and compliance with the applicable Spine terms. This is an independent community project, not an official Spine integration.

## References

- [Official Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Spine JSON format](https://esotericsoftware.com/spine-json-format)
- [Spine export documentation](https://esotericsoftware.com/spine-export)
