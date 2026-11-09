"""Local HTTP smoke tests; no external API credentials or network required."""
import http.client
import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

class HttpSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        os.environ["RILEY_DATA"]=cls.tmp.name+"/data"
        os.environ["RILEY_WORKSPACE"]=cls.tmp.name+"/workspace"
        from riley import core
        cls.core=core
        core.init()
        cls.server=ThreadingHTTPServer(("127.0.0.1",0),core.Handler)
        cls.port=cls.server.server_port
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        # Handler's Host and Origin checks intentionally pin production port 8765.
        # Use mock headers in direct unit tests for non-default ephemeral test port.
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls.tmp.cleanup()

    def request(self,method,path,body=None,headers=None):
        conn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=5)
        headers=dict(headers or {})
        if body is not None:
            headers["Content-Type"]="application/json"
            body=json.dumps(body)
        conn.request(method,path,body=body,headers=headers)
        response=conn.getresponse()
        data=response.read()
        result=(response.status,dict(response.getheaders()),data)
        conn.close()
        return result

    def test_homepage_issues_session_cookie(self):
        status,headers,body=self.request("GET","/")
        self.assertEqual(status,200)
        self.assertIn(b"RILEY",body)
        self.assertIn("HttpOnly",headers["Set-Cookie"])
        self.assertIn("SameSite=Strict",headers["Set-Cookie"])

    def test_api_requires_session(self):
        status,_,body=self.request("GET","/api/history")
        self.assertEqual(status,403)
        self.assertIn(b"Open Riley",body)

    def test_file_write_requires_preview_token(self):
        c=self.core
        preview=c.write_file("test.txt","safe")
        with self.assertRaises(ValueError):
            c.write_file("test.txt","safe",approved=True,token="wrong")
        with self.assertRaises(ValueError):
            c.write_file("test.txt","changed",approved=True,token=preview["token"])
        preview=c.write_file("test.txt","safe")
        c.write_file("test.txt","safe",approved=True,token=preview["token"])
        self.assertEqual(c.read_file("test.txt"),"safe")
        with self.assertRaises(ValueError):
            c.write_file("test.txt","safe",approved=True,token=preview["token"])

    def test_clear_history_and_memory(self):
        c=self.core
        c.remember("smoke","test")
        c.add_message("user","hello")
        c.clear_memories()
        c.clear_history()
        self.assertNotIn("smoke",c.memories())
        self.assertEqual(c.history(),[])

    def test_no_cloud_fallback_on_http_auth_error(self):
        from urllib.error import HTTPError
        c=self.core
        with patch.dict(os.environ,{"RILEY_PROVIDER":"auto","ANTHROPIC_API_KEY":"invalid","RILEY_LOCAL_MODEL":"fake"}):
            with patch.object(c.urllib.request,"urlopen",side_effect=HTTPError("url",401,"unauthorized",None,None)):
                with self.assertRaisesRegex(RuntimeError,"HTTP 401"):
                    c.model_request([{"role":"user","content":"hi"}])

    def test_mock_cloud_success(self):
        from io import BytesIO
        c=self.core
        class Response:
            def __enter__(self): return BytesIO(b'{"content":[{"type":"text","text":"Hello from cloud"}]}')
            def __exit__(self,*args): return False
        with patch.dict(os.environ,{"RILEY_PROVIDER":"cloud","ANTHROPIC_API_KEY":"fake","RILEY_CLOUD_MODEL":"test-model"}):
            with patch.object(c.urllib.request,"urlopen",return_value=Response()):
                self.assertEqual(c.model_request([{"role":"user","content":"hello"}]),"Hello from cloud")

    def test_mock_local_success(self):
        from io import BytesIO
        c=self.core
        class Response:
            def __enter__(self): return BytesIO(b'{"message":{"content":"Hello offline"}}')
            def __exit__(self,*args): return False
        with patch.dict(os.environ,{"RILEY_PROVIDER":"local","RILEY_LOCAL_MODEL":"test-model"}):
            with patch.object(c.urllib.request,"urlopen",return_value=Response()):
                self.assertEqual(c.model_request([{"role":"user","content":"hello"}]),"Hello offline")

    def test_cloud_network_failure_falls_back_locally(self):
        from io import BytesIO
        from urllib.error import URLError
        c=self.core
        class Response:
            def __enter__(self): return BytesIO(b'{"message":{"content":"Offline fallback"}}')
            def __exit__(self,*args): return False
        with patch.dict(os.environ,{"RILEY_PROVIDER":"auto","ANTHROPIC_API_KEY":"fake","RILEY_LOCAL_MODEL":"test-model"}):
            with patch.object(c.urllib.request,"urlopen",side_effect=[URLError("offline"),Response()]):
                self.assertEqual(c.model_request([{"role":"user","content":"hello"}]),"Offline fallback")

if __name__=="__main__":
    unittest.main()
