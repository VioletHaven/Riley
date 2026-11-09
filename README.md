# Riley — Hybrid AI Companion

Riley's original browser interface is preserved. Development of the local-first hybrid AI core happens on `feature/riley-core-v0.1`; `main` remains the original baseline.

## Run the development build

Requires Python 3.10+ and a supported browser. From the repository root:

```bash
python -m riley.core
```

Open **http://127.0.0.1:8765/** on the same computer. Do not open `index.html` directly or use the GitHub Pages URL for the new backend. The original Riley interface is served by the local backend.

### Cloud model

Set `ANTHROPIC_API_KEY` in your OS environment (not the browser or GitHub), then start Riley. Optional: `RILEY_PROVIDER=cloud` and `RILEY_CLOUD_MODEL` to choose a supported model.

### Offline model

Install and run Ollama separately, download a model appropriate for your hardware, then set `RILEY_LOCAL_MODEL` to the model name and `RILEY_PROVIDER=local`. Riley talks to Ollama on loopback port 11434. In `auto` mode Riley tries cloud first if a key is present and otherwise uses local; cloud errors can trigger local fallback when a local model is configured.

### Data and security

Riley stores SQLite data under `~/.riley/` and limits file operations to `~/.riley/workspace/` by default. Set `RILEY_DATA` and `RILEY_WORKSPACE` to customize these locations. Do not commit secrets, SQLite files, or personal documents.

This is a **development prototype**. It is bound to loopback, not exposed to the internet. Do not expose port 8765 through a public proxy. The browser's old localStorage memory is not automatically migrated into SQLite; migration needs a separate reviewed import tool. Existing slash commands still run in the browser, and some old links/assets are not present in the repository.

### Tests

```bash
python -m unittest discover -s tests -v
```

### Current limitations

- Not yet a packaged native desktop or USB application.
- Live cloud/local provider behavior and complete UI regression tests still require execution on a supported computer.
- No email access, arbitrary shell execution, autonomous coding, or self-updating capability.
- File writing requires confirmation in the separate `/prototype` prototype UI; the preserved original UI does not yet expose those controls.
- `web/index.html` remains an isolated prototype for testing file previews and approvals.
