# Riley Core v0.1 — development plan

Baseline: `cadd0558e19cc92ba7cbc313e18f5fcccef6adfd` on `main`. Do not modify `main` during development.

## Preserve
- Existing `index.html` browser UI, Riley persona, voice tools, cybersecurity utilities, slash commands.
- `manifest.json` and existing browser entrypoint.

## Build
1. Local-only Python backend with Anthropic cloud and Ollama local adapters.
2. SQLite persistent messages and memory, with explicit import from legacy browser localStorage.
3. Workspace-restricted file reads, write previews and user confirmation.
4. Browser UI integration; migrate existing interface incrementally.
5. Tests for storage, paths, permissions, provider failures, and HTTP endpoints.
6. Security hardening: local authentication and origin checks, secrets outside repository, backups, symlink protections.

## Release criteria
- Cloud and local inference tested on a real device; offline fallback verified.
- Legacy UI and commands regression-tested.
- No API keys or personal data committed.
- No unrestricted filesystem or code execution.
- Tests pass, with documented launch instructions.

## Status
Development branch created; baseline preserved. Prototype exists separately as `riley-core-v0.1.zip` in the conversation. Integration and runtime testing pending.
