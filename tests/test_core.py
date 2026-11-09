import os
import tempfile
import unittest
from pathlib import Path

class RileyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        os.environ["RILEY_DATA"]=cls.tmp.name+"/data"
        os.environ["RILEY_WORKSPACE"]=cls.tmp.name+"/workspace"
        import importlib
        from riley import core
        cls.core=importlib.reload(core)
        core.init()
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
    def test_memory(self):
        self.core.remember("favorite","cyan")
        self.assertEqual(self.core.memories()["favorite"],"cyan")
    def test_history(self):
        self.core.add_message("user","hello")
        self.core.add_message("assistant","hi")
        self.assertEqual(self.core.history()[-2:],[{"role":"user","content":"hello"},{"role":"assistant","content":"hi"}])
    def test_preview_requires_approval(self):
        self.assertTrue(self.core.write_file("notes/test.txt","hello")["requires_approval"])
        self.assertFalse((self.core.WORKSPACE/"notes/test.txt").exists())
        preview=self.core.write_file("notes/test.txt","hello")
        with self.assertRaises(ValueError): self.core.write_file("notes/test.txt","hello",True)
        with self.assertRaises(ValueError): self.core.write_file("notes/test.txt","changed",True,preview["token"])
        preview=self.core.write_file("notes/test.txt","hello")
        self.core.write_file("notes/test.txt","hello",True,preview["token"])
        with self.assertRaises(ValueError): self.core.write_file("notes/test.txt","hello",True,preview["token"])
        self.assertEqual(self.core.read_file("notes/test.txt"),"hello")
    def test_path_traversal(self):
        for p in ("../secret","/etc/passwd","foo/../../secret",""):
            with self.assertRaises(ValueError): self.core.safe_path(p)
    def test_symlink_escape(self):
        target=Path(self.tmp.name)/"outside";target.mkdir()
        link=self.core.WORKSPACE/"escape";link.symlink_to(target,target_is_directory=True)
        with self.assertRaises(ValueError): self.core.safe_path("escape/private.txt")
    def test_invalid_memory(self):
        with self.assertRaises(ValueError): self.core.remember("","bad")
    def test_missing_model(self):
        keys=("ANTHROPIC_API_KEY","RILEY_LOCAL_MODEL","RILEY_PROVIDER")
        old={k:os.environ.pop(k,None) for k in keys}
        try:
            with self.assertRaisesRegex(RuntimeError,"No available model"):
                self.core.model_request([{"role":"user","content":"hello"}])
        finally:
            for k,v in old.items():
                if v is not None: os.environ[k]=v

if __name__=="__main__":unittest.main()
