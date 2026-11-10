# Riley balanced autonomy — implementation plan

## Decisions (2026-11-10)
- **Files:** only explicitly approved workspaces.
- **Initiative:** Riley may initiate conversations and suggest help, with cooldowns and quiet hours.
- **Memory:** ordinary preferences may be remembered; sensitive information requires explicit consent.
- **Computer actions:** narrowly scoped reversible low-risk actions may run automatically; sensitive actions require specific approval.

## Guardrails
- Deny unknown actions by default.
- The model never directly executes OS commands or filesystem operations; a separate gateway checks all requests.
- Permissions bind to action, target, scope, expiration, and initiating session.
- One-time approval tokens are single-use; reject modified requests and expired approvals.
- Audit attempted, allowed, denied, and failed actions, without logging secrets or unnecessary personal content.
- Provide stop, revoke, recovery, and backup mechanisms.
- No self-modification, arbitrary shell access, silent messaging, or access to secrets.
- Untrusted web or file content cannot grant permissions.

## Existing baseline
Development base: `feature/riley-core-v0.1` (27 commits ahead of `main` at initial inspection).
Existing files include `riley/core.py`, `tests/test_core.py`, `tests/test_http.py`, `web/index.html`, and original `index.html`.
Existing file preview tokens and workspace restrictions are useful but not a complete autonomous authorization gateway.
Existing local server is development-only and requires further security review.

## Stages and acceptance criteria
0. **Baseline:** inspect files, capture exact commit, run existing tests and browser smoke tests; preserve original interface.
1. **Permission gateway:** pure decision function with action+target+scope policy; default deny; unit tests for unknown actions, path escape, and privilege escalation.
2. **Approval service:** time-limited, single-use, exact-action approvals; cancellation, concurrency, and replay tests.
3. **Workspace tools:** safe create/read/organize with atomic writes, file version checks, backups, and undo; test symlinks and race conditions.
4. **Memory consent:** classify sensitive writes and require approval; allow review, edit, deletion, and export.
5. **Initiative:** suggestion-only scheduler with cooldown, quiet hours, opt-out; no unsolicited tool execution.
6. **Restricted computer tools:** narrow allowlist and approval prompts; never generic shell access.
7. **UI integration:** integrate permissions and action history into preserved original UI; manual regression testing.

## Development process
Use `feature/balanced-autonomy-foundation`; do not push changes to `main` or deploy without review.
Implement small changes with tests and human-readable notes in `learning/`.
Before behavior-changing work, confirm test baseline. Live hardware/provider tests remain necessary.

## Updated file permission decisions (user clarification)
- Read only within explicitly approved workspaces.
- Write permission can be granted to one file or to a specific folder, with persistent scope when explicitly chosen by the user. A folder grant covers ordinary writes only; it does not imply delete or rename.
- New folder access must be approved through a trusted UI. Natural-language text alone is not a verified approval.
- Every delete requires its own fresh, exact-target approval. No standing delete grants.
- Riley may proactively suggest file or folder names, but renaming requires approval of the exact old and new paths; check collisions.
- Permissions persist until revoked if the user chooses a standing grant; short-lived one-time approval tokens still expire. The existing five-minute grant prototype does not implement persistent grants.
- Restrict symlink escapes, special/protected locations, and dangerous file types; record changes and provide backups or undo where possible.
- An AI suggestion is never an authorization. All mutations must pass a trusted permission gateway.

### Implementation follow-up
Replace the isolated in-memory exact-file grant prototype with a reviewed persistent grant store, trusted approval workflow, folder-scope enforcement, explicit delete/rename action types, and audit tests. Do not connect the prototype grant method directly to model output.
