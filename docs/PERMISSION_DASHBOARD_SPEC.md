# Riley — Permission dashboard (planned UI)

The persistent grant storage foundation lives in `riley/standing_permissions.py`. No UI or runtime integration exists yet.

A trusted, local dashboard should show each grant's action, exact canonical scope, whether it covers one file or an existing folder, and a Revoke button. The dashboard must require a human confirmation for each new grant; AI-generated messages or tool arguments must never count as approval. It should show a proposed rename with old and new paths and require a separate confirmation. Every deletion must require fresh confirmation naming the exact target, even within a write-approved folder.

The UI/controller must bind confirmation to an unforgeable pending request and approved workspace. Only the trusted controller may call `approve_write`. Add an audit log, collision checks, backup/undo, platform-specific path protection, and race-safe filesystem operations before enabling real writes. This module is not an authorization boundary for filesystem execution by itself.

Persistent write grants do not expire automatically; they remain until revoked. They never include delete or rename permission. Do not expose the database or the approval method to Riley's AI tools.
