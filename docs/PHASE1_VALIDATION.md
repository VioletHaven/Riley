# Phase 1 validation report

Development branch only; do not merge to `main` until live hardware and provider acceptance tests pass.

## Automated checks
GitHub Actions `Riley Core validation` runs on each push and validates:
- Python syntax compilation
- Python unit and HTTP smoke tests
- Inline JavaScript syntax in the original and prototype interfaces

Tests include memory/history persistence and clearing, path traversal, symlink escapes, write preview token use and replay rejection, session cookie issuance, unauthenticated API rejection, and mocked cloud/local/fallback routing.

See [GitHub Actions](https://github.com/VioletHaven/Riley/actions/workflows/validate.yml) for the authoritative status of the latest commit. Previous passing runs do not prove later commits pass.

## Live acceptance tests still required
These tests cannot be completed with mock credentials:
1. On a supported computer, configure `ANTHROPIC_API_KEY` in the OS environment, launch `python -m riley.core`, open `http://127.0.0.1:8765/`, send a prompt, and verify the response.
2. Configure Ollama and a downloaded compatible local model, set `RILEY_PROVIDER=local` and `RILEY_LOCAL_MODEL`, disconnect internet, restart, and verify a response.
3. In `auto` mode with both configured, simulate a network outage and verify local fallback; restore internet and verify cloud recovery on a subsequent prompt.
4. Check all original UI controls and slash commands manually in a supported browser, including voice input/output, notes, timers, and file workspace.
5. Inspect actual workspace write permissions and attempts to use symlinks/races; security review is not complete.

## Known limitations
- No live provider credentials or Ollama runtime are available in CI.
- Local loopback authentication is per-run cookie-based; it is not a comprehensive defense against malicious software running under the same OS account.
- Workspace path checking may have a time-of-check/time-of-use race with concurrent filesystem changes; avoid untrusted local processes.
- Existing browser localStorage memory and chat history are not automatically imported.
- Missing legacy PWA assets/service worker may cause optional browser features to fail.
- Do not expose the local server publicly or merge until acceptance testing and remaining security review are complete.

## Scope achieved
The original browser UI is served from the local backend; model calls are routed through backend providers; SQLite stores chat and memory; file preview and approval are available; tests run on GitHub Actions. The original `main` branch remains unchanged.
