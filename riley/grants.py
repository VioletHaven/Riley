"""Narrow, temporary permission grants. No persistence or execution yet.

Grants can only relax actions already marked 'ask' by the static policy.
They cannot override a denied action, grant unsupported capabilities,
or expand beyond an approved workspace.
"""
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from uuid import uuid4

from riley.permissions import decide, PermissionResult

MAX_GRANT_SECONDS = 3600


@dataclass(frozen=True)
class Grant:
    id: str
    action: str
    scope: str
    expires_at: float


class GrantStore:
    """In-memory grants; a restart clears all permissions."""

    def __init__(self, clock=monotonic):
        self._clock = clock
        self._grants = {}

    def grant(self, action, *, target, workspace, duration_seconds=300, user_approved=False):
        if user_approved is not True:
            raise PermissionError("Explicit user approval is required")
        if isinstance(duration_seconds, bool) or not isinstance(duration_seconds, (int, float)) or not 0 < duration_seconds <= MAX_GRANT_SECONDS:
            raise ValueError("Invalid grant duration")
        policy = decide(action, target=target, workspace=workspace)
        if policy.decision != "ask" or not action.startswith("workspace."):
            raise PermissionError("Only supported workspace approval actions can be granted")
        # Scope is the exact file, not an entire directory. Folder grants need
        # a separately reviewed, explicit action/scope UI.
        root = Path(workspace).resolve(strict=True)
        scope = str((root / target).resolve(strict=False))
        grant = Grant(uuid4().hex, action, scope, self._clock() + duration_seconds)
        self._grants[grant.id] = grant
        return grant

    def revoke(self, grant_id):
        return self._grants.pop(grant_id, None) is not None

    def check(self, action, *, target="", workspace="", grant_id=None):
        base = decide(action, target=target, workspace=workspace)
        if base.decision != "ask" or not grant_id:
            return base
        grant = self._grants.get(grant_id)
        if grant is None or grant.expires_at <= self._clock():
            return base
        if not action.startswith("workspace."):
            return base
        resolved = str((Path(workspace).resolve(strict=True) / target).resolve(strict=False))
        if grant.action != action or grant.scope != resolved:
            return base
        return PermissionResult("allow", "Explicit temporary grant for this exact action and file")
