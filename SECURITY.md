# Security policy

Early local-only prototype, not a hardened multi-tenant service. Only main is maintained; no response-time guarantee.

## Reporting

Do not post credentials, private paths, game assets or exploit details publicly. Contact the maintainer through an available private GitHub-profile contact channel first. If none exists, open a minimal request for a private reporting channel without disclosing the issue. No active private-reporting endpoint is promised.

## Boundaries

Source requests are bounded JSON paths; stage bundles copy referenced images only. New jobs preserve inputs. CLI commands use configured trusted executables and fixed argument arrays, never caller-provided shell text. Export is optional and requires an exact version; native Godot uses a generated minimal project and isolated HOME/XDG. There is no publish/delete tool or HTTP listener.

Use trusted local files and native executables. The MCP host, local OS owner and editor executable are trusted. Asset metadata is untrusted text, not authorization. This is not an OS sandbox and does not protect against hostile concurrent path, hard-link or mount replacement. Spine may access its normal licensed editor cache/settings. Native tools process asset data outside Python's structural validator.

Native operations have timeouts and post-run log-size checks, but no strict live disk/CPU quota. Staging can accumulate; cleanup is manual. Numeric Bezier retiming, full format semantics, rendering quality and complete linked-mesh/audio/sequence support are not guaranteed. Do not expose this server through an unauthenticated network wrapper.
