import tempfile
import unittest
from pathlib import Path
from riley.read_permissions import ReadPermissions


class ReadPermissionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.folder = root / "approved"
        self.folder.mkdir()
        self.file = self.folder / "hello.txt"
        self.file.write_text("hello", encoding="utf-8")
        self.outside = root / "outside.txt"
        self.outside.write_text("outside", encoding="utf-8")
        self.store = ReadPermissions(root / "grants.sqlite3")

    def test_requires_confirmation(self):
        with self.assertRaises(PermissionError):
            self.store.grant_folder(str(self.folder))

    def test_read_scope_and_revocation(self):
        self.assertFalse(self.store.allows_read(str(self.file)))
        grant = self.store.grant_folder(str(self.folder), trusted_user_confirmation=True)
        self.assertTrue(self.store.allows_read(str(self.file)))
        self.assertFalse(self.store.allows_read(str(self.outside)))
        self.assertTrue(self.store.revoke(grant))
        self.assertFalse(self.store.allows_read(str(self.file)))

    def test_persists_across_instances(self):
        self.store.grant_folder(str(self.folder), trusted_user_confirmation=True)
        other = ReadPermissions(Path(self.temp.name) / "grants.sqlite3")
        self.assertTrue(other.allows_read(str(self.file)))

    def test_symlink_escape_denied(self):
        self.store.grant_folder(str(self.folder), trusted_user_confirmation=True)
        link = self.folder / "outside-link.txt"
        try:
            link.symlink_to(self.outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable on this platform")
        self.assertFalse(self.store.allows_read(str(link)))


if __name__ == "__main__":
    unittest.main()
