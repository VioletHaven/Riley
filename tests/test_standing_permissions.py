import tempfile
import unittest
from pathlib import Path
from riley.standing_permissions import StandingPermissions


class StandingPermissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "approved"
        self.root.mkdir()
        (self.root / "biology").mkdir()
        self.db_path = Path(self.tmp.name) / "permissions.db"
        self.store = StandingPermissions(self.db_path)

    def test_confirmation_required(self):
        with self.assertRaises(PermissionError):
            self.store.approve_write(workspace=str(self.root), target="biology", scope_kind="folder")

    def test_folder_scope_persists(self):
        grant = self.store.approve_write(workspace=str(self.root), target="biology", scope_kind="folder", trusted_user_confirmation=True)
        restarted = StandingPermissions(self.db_path)
        self.assertEqual(restarted.check("workspace.write", workspace=str(self.root), target="biology/notes.txt").decision, "allow")
        self.assertEqual(restarted.check("workspace.write", workspace=str(self.root), target="other.txt").decision, "ask")
        self.assertEqual(restarted.check("workspace.delete", workspace=str(self.root), target="biology/notes.txt").decision, "ask")
        self.assertEqual(restarted.check("workspace.rename", workspace=str(self.root), target="biology/notes.txt").decision, "deny")
        self.assertTrue(restarted.revoke(grant))
        self.assertEqual(restarted.check("workspace.write", workspace=str(self.root), target="biology/notes.txt").decision, "ask")

    def test_file_scope_only(self):
        self.store.approve_write(workspace=str(self.root), target="biology/notes.txt", scope_kind="file", trusted_user_confirmation=True)
        self.assertEqual(self.store.check("workspace.write", workspace=str(self.root), target="biology/notes.txt").decision, "allow")
        self.assertEqual(self.store.check("workspace.write", workspace=str(self.root), target="biology/other.txt").decision, "ask")

    def test_folder_must_exist(self):
        with self.assertRaises(ValueError):
            self.store.approve_write(workspace=str(self.root), target="missing", scope_kind="folder", trusted_user_confirmation=True)

    def test_outside_denied(self):
        with self.assertRaises(ValueError):
            self.store.approve_write(workspace=str(self.root), target="../outside", scope_kind="file", trusted_user_confirmation=True)
        self.assertEqual(self.store.check("workspace.write", workspace=str(self.root), target="../outside").decision, "deny")

    def test_unknown_not_authorized(self):
        self.store.approve_write(workspace=str(self.root), target="biology", scope_kind="folder", trusted_user_confirmation=True)
        self.assertEqual(self.store.check("computer.run_shell").decision, "deny")


if __name__ == "__main__":
    unittest.main()
