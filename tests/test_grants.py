"""Grant policy tests. No filesystem operations are executed."""
import tempfile
import unittest
from pathlib import Path
from riley.grants import GrantStore


class GrantTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "workspace"
        self.root.mkdir()
        self.now = [100.0]
        self.store = GrantStore(clock=lambda: self.now[0])

    def make_grant(self):
        return self.store.grant("workspace.write", target="a.txt", workspace=str(self.root), user_approved=True)

    def test_requires_explicit_approval(self):
        with self.assertRaises(PermissionError):
            self.store.grant("workspace.write", target="a.txt", workspace=str(self.root))

    def test_exact_action_and_target(self):
        grant = self.make_grant()
        self.assertEqual(self.store.check("workspace.write", target="a.txt", workspace=str(self.root), grant_id=grant.id).decision, "allow")
        self.assertEqual(self.store.check("workspace.write", target="b.txt", workspace=str(self.root), grant_id=grant.id).decision, "ask")
        self.assertEqual(self.store.check("workspace.delete", target="a.txt", workspace=str(self.root), grant_id=grant.id).decision, "ask")

    def test_expiry(self):
        grant = self.make_grant()
        self.now[0] += 301
        self.assertEqual(self.store.check("workspace.write", target="a.txt", workspace=str(self.root), grant_id=grant.id).decision, "ask")

    def test_revocation(self):
        grant = self.make_grant()
        self.assertTrue(self.store.revoke(grant.id))
        self.assertFalse(self.store.revoke(grant.id))
        self.assertEqual(self.store.check("workspace.write", target="a.txt", workspace=str(self.root), grant_id=grant.id).decision, "ask")

    def test_unknown_actions_never_granted(self):
        with self.assertRaises(PermissionError):
            self.store.grant("computer.run_shell", target="a.txt", workspace=str(self.root), user_approved=True)

    def test_no_override_for_unapproved_path(self):
        grant = self.make_grant()
        self.assertEqual(self.store.check("workspace.write", target="../outside", workspace=str(self.root), grant_id=grant.id).decision, "deny")

    def test_read_cannot_be_granted(self):
        with self.assertRaises(PermissionError):
            self.store.grant("workspace.read", target="a.txt", workspace=str(self.root), user_approved=True)

    def test_invalid_duration(self):
        for duration in (0, -1, 3601, True, "300"):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                self.store.grant("workspace.write", target="a.txt", workspace=str(self.root), duration_seconds=duration, user_approved=True)


if __name__ == "__main__":
    unittest.main()
