"""Persistent workspace write grants; policy layer only, never a file executor.

Only a trusted approval UI/controller may call approve_write(). Never expose
that method as a callable AI tool. Deletions and renames always require fresh
approval, independent of standing grants.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from riley.permissions import PermissionResult, decide


class StandingPermissions:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS write_grants (
                id TEXT PRIMARY KEY, workspace TEXT NOT NULL,
                scope TEXT NOT NULL, scope_kind TEXT NOT NULL,
                action TEXT NOT NULL CHECK(action = 'workspace.write')
            )""")

    @contextmanager
    def _connect(self):
        db=sqlite3.connect(self.db_path)
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _resolve(workspace, target):
        if not isinstance(workspace, str) or not workspace:
            raise ValueError("Missing approved workspace")
        if not isinstance(target, str) or not target:
            raise ValueError("Missing target")
        root = Path(workspace).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("Workspace must be a directory")
        candidate = (root / target).resolve(strict=False)
        if candidate == root or not candidate.is_relative_to(root):
            raise ValueError("Target outside approved workspace")
        return root, candidate

    def approve_write(self, *, workspace, target, scope_kind, trusted_user_confirmation=False):
        """Called ONLY after a trusted UI verifies the user's specific approval."""
        if trusted_user_confirmation is not True:
            raise PermissionError("Verified user approval required")
        if scope_kind not in ("file", "folder"):
            raise ValueError("Scope must be file or folder")
        root, candidate = self._resolve(workspace, target)
        if scope_kind == "folder" and not candidate.is_dir():
            raise ValueError("Folder scope must name an existing directory")
        if scope_kind == "file" and candidate.exists() and not candidate.is_file():
            raise ValueError("File scope must name a file")
        if decide("workspace.write", target=str(candidate), workspace=str(root)).decision != "ask":
            raise PermissionError("Write permission cannot be granted for this target")
        grant_id = uuid4().hex
        with self._connect() as db:
            db.execute("INSERT INTO write_grants VALUES (?, ?, ?, ?, ?)",
                       (grant_id, str(root), str(candidate), scope_kind, "workspace.write"))
        return grant_id

    def list_grants(self):
        with self._connect() as db:
            return [dict(zip(("id", "workspace", "scope", "scope_kind", "action"), row))
                    for row in db.execute("SELECT id, workspace, scope, scope_kind, action FROM write_grants ORDER BY rowid")]

    def revoke(self, grant_id):
        with self._connect() as db:
            return db.execute("DELETE FROM write_grants WHERE id = ?", (grant_id,)).rowcount > 0

    def check(self, action, *, workspace="", target=""):
        base = decide(action, target=target, workspace=workspace)
        if base.decision != "ask" or action != "workspace.write":
            return base
        try:
            root, candidate = self._resolve(workspace, target)
        except (OSError, ValueError, RuntimeError):
            return PermissionResult("deny", "Invalid workspace target")
        for grant in self.list_grants():
            if grant["workspace"] != str(root):
                continue
            scope = Path(grant["scope"])
            # A symlink or path change after approval cannot silently expand
            # permission beyond the stored, canonical scope.
            if grant["scope_kind"] == "file" and candidate == scope:
                return PermissionResult("allow", "Standing file write grant")
            if grant["scope_kind"] == "folder" and candidate != scope and candidate.is_relative_to(scope):
                return PermissionResult("allow", "Standing folder write grant")
        return base
