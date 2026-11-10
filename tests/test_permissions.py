"""Security boundary tests for Riley's pure policy decisions."""
import tempfile
import unittest
from pathlib import Path
from riley.permissions import decide


class PermissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "approved"
        self.root.mkdir()

    def test_unknown_action_denied(self):
        self.assertEqual(decide("computer.run_shell").decision, "deny")
        self.assertEqual(decide("workspace.superuser").decision, "deny")
        self.assertEqual(decide(None).decision, "deny")

    def test_workspace_read_and_write(self):
        self.assertEqual(decide("workspace.read", target="notes.txt", workspace=str(self.root)).decision, "allow")
        self.assertEqual(decide("workspace.write", target="notes.txt", workspace=str(self.root)).decision, "ask")
        self.assertEqual(decide("workspace.delete", target="notes.txt", workspace=str(self.root)).decision, "ask")

    def test_workspace_requires_scope_and_target(self):
        self.assertEqual(decide("workspace.read", target="notes.txt").decision, "deny")
        self.assertEqual(decide("workspace.read", workspace=str(self.root)).decision, "deny")
        self.assertEqual(decide("workspace.read", target=".", workspace=str(self.root)).decision, "deny")

    def test_escape_denied(self):
        for target in ("../outside.txt", "/etc/passwd", "sub/../../outside", "a\x00b"):
            with self.subTest(target=target):
                self.assertEqual(decide("workspace.read", target=target, workspace=str(self.root)).decision, "deny")

    def test_symlink_escape_denied(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        link = self.root / "link"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable")
        self.assertEqual(decide("workspace.read", target="link/file.txt", workspace=str(self.root)).decision, "deny")

    def test_memory_and_initiative(self):
        self.assertEqual(decide("memory.preference.save").decision, "allow")
        self.assertEqual(decide("memory.sensitive.save").decision, "ask")
        self.assertEqual(decide("initiative.suggest").decision, "allow")
        self.assertEqual(decide("computer.send_message").decision, "ask")

    def test_missing_workspace_denied(self):
        self.assertEqual(decide("workspace.read", target="notes.txt", workspace=str(self.root / "missing")).decision, "deny")


if __name__ == "__main__":
    unittest.main()
