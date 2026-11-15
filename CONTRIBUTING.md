# Contributing

Start with an issue describing the use case and the boundary affected. Keep changes small and include synthetic regression fixtures.

```sh
uv sync --locked
uv run --locked pytest -q
uv build
```

Never submit real game artwork, proprietary `.spine` projects, credentials, private paths, generated runtime assets or unlicensed third-party fixtures. Prefer hand-authored minimal JSON. Do not run tests against production asset directories.

Preserve read-only source behavior and staging isolation. New transformations should be pure functions first. CLI/preview adapters need version handling, timeout/cancellation, bounded logs and explicit output verification. No arbitrary-shell tools. Publication requires a separate design review rather than a side effect of another tool.

Document whether a feature is implemented, experimentally verified or only planned. Do not claim editor/runtime compatibility from parsing alone. By submitting code, you agree to license your contribution under this repository's MIT license.
