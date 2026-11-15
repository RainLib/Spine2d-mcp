# Connect Spine, Codex and Claude Code

[中文快速说明](#中文快速说明) · [Codex example](../examples/clients/codex.config.toml) · [Claude Code example](../examples/clients/claude.mcp.json)

```text
Codex or Claude Code (MCP client)
    ↓ stdio tool calls
Spine2d-mcp
    ↓ copied JSON + images, exact-version CLI
Licensed local Spine → isolated .spine / JSON / atlas / PNG
    ↓ optional native runtime check
Spine-enabled Godot in a separate generated project
```

**Spine is the local editor/CLI, not an MCP client.** You configure this server in an agent client and explicitly point it at Spine. It does not install an in-editor plugin or remotely manipulate the GUI. Codex and Claude names indicate interoperable clients, not endorsements or bundled models.

## 1. Prepare the server and safe directories

```sh
git clone https://github.com/RainLib/Spine2d-mcp.git
cd Spine2d-mcp
uv sync --locked
uv run --locked pytest -q
```

Choose a read-only source containing test copies and a separate staging directory. Neither root may contain the other. Use absolute paths; avoid broad home-directory roots. Start with `examples/source` for JSON inspection. Its synthetic sample is not an export-ready textured rig.

The MCP itself does not require a cloud API key. Your agent client still needs its own normal authentication. No credentials belong in this repository.

## 2. Codex

Review [the TOML template](../examples/clients/codex.config.toml), replace placeholders, then **merge only its named MCP table** into the intended configuration. Back up the file first. Do not overwrite your existing model/provider/MCP settings.

Alternatively, this explicitly registers a stdio server in the current Codex home:

```sh
codex mcp add spine-pipeline \
  --env SPINE_MCP_SOURCE_ROOT=/path/to/test-assets \
  --env SPINE_MCP_STAGING_ROOT=/path/to/separate-staging \
  -- uv --directory /path/to/Spine2d-mcp run --locked spine-pipeline-mcp
codex mcp get spine-pipeline --json
```

For native operations, use the template's 30-second startup and 300-second tool timeouts and optional executable variables. Configuration inspection only proves the entry parses; **it is not a tool-call test**. Start a new Codex session and ask:

> Call spine-pipeline skeleton_inspect once with relative_path="minimal.json". Report the version and bone/animation counts. Do not edit or export anything.

Use your own actual filename when using a different source root. Verify the session records a successful MCP tool call, not merely a guessed answer.

`CODEX_HOME` selects a separate Codex configuration/state directory. If an API-key wrapper launches Codex with another home, adding this entry to the default home does not automatically configure that wrapper. Decide explicitly whether to merge the entry into the second home; do not copy authentication files. See [Codex MCP configuration](https://developers.openai.com/codex/mcp/) and [configuration locations](https://learn.chatgpt.com/docs/config-file/config-advanced).

## 3. Claude Code

For a session-only connection, copy [the JSON template](../examples/clients/claude.mcp.json) **outside the repository**, replace placeholders, then run:

```sh
claude --mcp-config /path/to/private-spine.mcp.json --strict-mcp-config
```

`--strict-mcp-config` limits that session to the supplied MCP configuration; it does not bypass tool permissions. Ask the same read-only inspection prompt and review `/mcp` status.

For a persistent connection only in the current project:

```sh
cd /path/to/your/project
claude mcp add --transport stdio --scope local spine-pipeline \
  --env SPINE_MCP_SOURCE_ROOT=/path/to/test-assets SPINE_MCP_STAGING_ROOT=/path/to/separate-staging \
  -- uv --directory /path/to/Spine2d-mcp run --locked spine-pipeline-mcp
claude mcp get spine-pipeline
```

Local scope is personal configuration for that project; project scope writes shareable `.mcp.json`, so do not use it casually for private paths. Add native variables only after reviewing them. The JSON template sets a per-server 300,000 ms timeout. See the [official Claude Code MCP guide](https://code.claude.com/docs/en/mcp).

## 4. Enable the local Spine / Godot steps

Add these values to the selected server's environment, **not as a prompt**:

```text
SPINE_MCP_CLI=/path/to/Spine
SPINE_MCP_CLI_VERSION=4.3.26
SPINE_MCP_GODOT_EXECUTABLE=/path/to/spine-enabled-godot
```

Spine must already be installed and appropriately licensed. The JSON version must exactly match the configured editor version. Godot must include native `SpineSprite`; a stock build may not. You can leave all three unset for JSON-only operations.

Progress deliberately: inspect → static validate → stage bundle → edit a new job → export → optional runtime check. There is no publish-to-game tool, and passing runtime smoke checks does not imply visual correctness.

## Verification record and limits

- Codex CLI **0.169.0**: actual read-only MCP `skeleton_inspect` invocation confirmed in a temporary session; not just `mcp get`.
- Claude Code **2.1.325**: isolated local configuration and MCP health check returned **Connected**. A full Claude model-driven tool invocation has not been claimed or tested here.
- Official SDK client: real stdio initialization, tool discovery and end-to-end tool calls tested.
- Local native pipeline: Spine **4.3.26** export and Spine-enabled Godot **4.7.1 custom build** load/brief animation sampling tested on copies. Private assets and raw client logs are not distributed.

These are tested configurations, not a promise that every later client/editor/runtime version works. Hosted CI does not run licensed native tools.

## 中文快速说明

这条连接是 **Codex / Claude Code → MCP → 本机 Spine CLI**，不是Spine编辑器内置插件，也不是GUI自动化。

先复制模板到私有配置位置、替换绝对路径。Codex合并命名MCP条目，切勿覆盖整个config；使用独立 `CODEX_HOME` 的API模式不会自动继承默认配置。Claude可用 `--mcp-config ... --strict-mcp-config` 仅本次连接；需要持久化时优先 `--scope local`，别把私有路径写入共享项目配置。

本MCP无需API key，模型客户端使用自己的登录；Spine仍需商业许可。验证先用 `skeleton_inspect`，别把“配置能读取”当成“工具调用成功”。默认Codex真实只读调用已验证；Claude目前仅验证本地Connected健康状态。原生导出与Godot检查使用副本，不覆盖作品；不承诺视觉质量。
