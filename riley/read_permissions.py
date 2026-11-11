"""Persistent, read-only folder grants for Riley.

Policy storage only: this module never opens files. A trusted local controller
must verify user approval before calling grant_folder(). Do not expose that
method to the language model.
"""
import sqlite3
from pathlib import Path
from uuid import uuid4


class ReadPermissions:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS read_grants (
                id TEXT PRIMARY KEY, folder TEXT NOT NULL
            )""")

    def grant_folder(self, folder, *, trusted_user_confirmation=False):
        if trusted_user_confirmation is not True:
            raise PermissionError("Trusted user confirmation required")
        if not isinstance(folder, str) or not folder:
            raise ValueError("A folder is required")
        path = Path(folder).resolve(strict=True)
        if not path.is_dir() or path.is_symlink():
            raise ValueError("An existing, non-symlink folder is required")
        grant_id = uuid4().hex
        with sqlite3.connect(self.db_path) as db:
            db.execute("INSERT INTO read_grants VALUES (?,?)", (grant_id, str(path)))
        return grant_id

    def list_grants(self):
        with sqlite3.connect(self.db_path) as db:
            return [{"id": row[0], "folder": row[1]}
                    for row in db.execute("SELECT id, folder FROM read_grants ORDER BY rowid")]

    def revoke(self, grant_id):
        with sqlite3.connect(self.db_path) as db:
            return db.execute("DELETE FROM read_grants WHERE id=?", (grant_id,)).rowcount > 0

    def allows_read(self, target):
        if not isinstance(target, str) or not target:
            return False
        try:
            raw = Path(target)
            if raw.is_symlink():
                return False
            path = raw.resolve(strict=True)
            if not path.is_file():
                return False
            for grant in self.list_grants():
                root = Path(grant["folder"])
                if root.is_symlink() or not root.is_dir():
                    continue
                if root.resolve(strict=True) != root:
                    continue
                if path != root and path.is_relative_to(root):
                    return True
        except (OSError, ValueError, RuntimeError):
            return False
        return False
