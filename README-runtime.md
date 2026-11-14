# Packaged text MCP runtime

Run `python -m pip install -r requirements.txt`, then `python -X utf8 large_text_viewer_mcp.py`. The server resolves `runtime.json` and `bin/` next to itself, independently of its working directory. No developer-tree fallback is used.

`runtime_health` reports startup capabilities without local paths by default. `include_paths=true` explicitly adds the resolved runtime path. Missing or incompatible runtimes return structured errors with `isError=true`; they do not expose executable paths.

An explicit absolute `LARGE_TEXT_VIEWER_BIN` override is supported and capability-checked. A broken override remains an error. `LARGE_TEXT_STARTUP_TIMEOUT_MS` defaults to 5000; `LARGE_TEXT_TOOL_TIMEOUT_MS` defaults to 0 (no deadline). Either deadline accepts 0 for unlimited. `LARGE_TEXT_MAX_OUTPUT_BYTES` defaults to 262144, range 1024 to 8388608; exceeding it returns an incomplete-result error, never silent truncated success.

Build the standalone CLI with `cargo build --locked --release --manifest-path runtime/Cargo.toml`. It uses the published MIT large-text-core 0.1.1 and has no GUI dependencies. Package it with `python tools/package_runtime.py --runtime <built-cli> --output <new-package-directory>`. The package can be copied to another directory and launched from an unrelated cwd. Host Python >=3.11 and the declared requirements remain prerequisites.
