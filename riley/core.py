"""Local-only Riley prototype. Standard library; Python 3.10+."""
import json
import os
import sqlite3
import secrets
import time
import threading
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv("RILEY_DATA", str(Path.home()/".riley"))).resolve()
WORKSPACE = Path(os.getenv("RILEY_WORKSPACE", str(DATA/"workspace"))).resolve()
PERSONA = (ROOT/"PERSONA.md").read_text(encoding="utf-8")
PENDING_WRITES = {}
PENDING_LOCK = threading.Lock()
SESSION_SECRET = secrets.token_urlsafe(32)

def init():
    DATA.mkdir(parents=True, exist_ok=True)
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATA/"riley.sqlite3") as db:
        db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, role TEXT, content TEXT)")
        db.execute("CREATE TABLE IF NOT EXISTS memories (key TEXT PRIMARY KEY, value TEXT)")
        db.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, action TEXT, target TEXT)")

def connect():
    return sqlite3.connect(DATA/"riley.sqlite3")

def history(limit=30):
    with connect() as db:
        rows=db.execute("SELECT role,content FROM (SELECT id,role,content FROM messages ORDER BY id DESC LIMIT ?) ORDER BY id",(limit,)).fetchall()
    return [{"role":r,"content":c} for r,c in rows]

def memories():
    with connect() as db:
        return dict(db.execute("SELECT key,value FROM memories"))

def remember(key,value):
    if not isinstance(key,str) or not key.strip() or len(key)>100 or not isinstance(value,str) or len(value)>5000:
        raise ValueError("Invalid memory")
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO memories VALUES (?,?)",(key,value))

def add_message(role,content):
    if role not in ("user","assistant") or not isinstance(content,str) or len(content)>50000:
        raise ValueError("Invalid message")
    with connect() as db:
        db.execute("INSERT INTO messages(role,content) VALUES (?,?)",(role,content))

def safe_path(relative):
    if not isinstance(relative,str) or not relative or "\\" in relative or "\x00" in relative:
        raise ValueError("Invalid path")
    p=(WORKSPACE/relative).resolve()
    if p==WORKSPACE or not p.is_relative_to(WORKSPACE):
        raise ValueError("Outside workspace")
    return p

def read_file(relative):
    p=safe_path(relative)
    if not p.is_file() or p.stat().st_size>1000000:
        raise ValueError("Missing or oversized file")
    return p.read_text(encoding="utf-8")

def write_file(relative,content,approved=False,token=None):
    p=safe_path(relative)
    if not isinstance(content,str) or len(content.encode("utf-8"))>1000000:
        raise ValueError("Oversized file")
    if not approved:
        ticket=secrets.token_urlsafe(32)
        with PENDING_LOCK:
            now=time.monotonic()
            for old,(expiry,_,_) in list(PENDING_WRITES.items()):
                if expiry<now: del PENDING_WRITES[old]
            PENDING_WRITES[ticket]=(now+120,relative,content)
        return {"requires_approval":True,"path":relative,"preview":content[:2000],"token":ticket}
    if not isinstance(token,str): raise ValueError("Valid preview token required")
    with PENDING_LOCK:
        saved=PENDING_WRITES.pop(token,None)
    if saved is None or saved[0]<time.monotonic() or saved[1]!=relative or saved[2]!=content:
        raise ValueError("Write preview expired or changed")
    # Recheck path immediately before the approved write.
    p=safe_path(relative)
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.is_symlink(): raise ValueError("Symlink targets are not writable")
    p.write_text(content,encoding="utf-8")
    with connect() as db:
        db.execute("INSERT INTO audit(action,target) VALUES (?,?)",("write",relative))
    return {"written":True,"path":relative}

def model_request(messages):
    mode=os.getenv("RILEY_PROVIDER","auto")
    key=os.getenv("ANTHROPIC_API_KEY","")
    if mode not in ("auto","cloud","local"):
        raise ValueError("Invalid provider")
    system=PERSONA+"\nMemories:\n"+"\n".join(f"{k}: {v}" for k,v in memories().items())
    if mode=="cloud" or (mode=="auto" and key):
        if not key: raise RuntimeError("Missing cloud API key")
        payload={"model":os.getenv("RILEY_CLOUD_MODEL","claude-sonnet-4-5"),"max_tokens":1024,"system":system,"messages":messages}
        req=urllib.request.Request("https://api.anthropic.com/v1/messages",json.dumps(payload).encode(),{"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=45) as response: data=json.load(response)
            return "".join(x.get("text","") for x in data.get("content",[]) if x.get("type")=="text")
        except Exception:
            if mode=="cloud": raise RuntimeError("Cloud provider unavailable")
    model=os.getenv("RILEY_LOCAL_MODEL","")
    if not model: raise RuntimeError("No available model; configure cloud or local")
    base=os.getenv("RILEY_OLLAMA_URL","http://127.0.0.1:11434")
    if base not in ("http://127.0.0.1:11434","http://localhost:11434"):
        raise ValueError("Ollama must use loopback")
    payload={"model":model,"stream":False,"messages":[{"role":"system","content":system}]+messages}
    req=urllib.request.Request(base+"/api/chat",json.dumps(payload).encode(),{"content-type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=90) as response: data=json.load(response)
    return data["message"]["content"]

class Handler(BaseHTTPRequestHandler):
    def authorized(self):
        import http.cookies
        cookie=http.cookies.SimpleCookie()
        try: cookie.load(self.headers.get("Cookie",""))
        except http.cookies.CookieError: return False
        value=cookie.get("riley_session")
        return value is not None and secrets.compare_digest(value.value,SESSION_SECRET)
    def send_json(self,status,data):
        raw=json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def do_GET(self):
        route=urlparse(self.path).path
        if route.startswith("/api/") and not self.authorized():
            return self.send_json(403,{"error":"Open Riley from the local home page first"})
        if route.startswith("/api/") and self.headers.get("Host") not in ("127.0.0.1:8765","localhost:8765"):
            return self.send_json(400,{"error":"Invalid host"})
        if route.startswith("/api/") and self.headers.get("Sec-Fetch-Site") not in (None,"same-origin","none"):
            return self.send_json(403,{"error":"Cross-site requests are blocked"})
        if route=="/api/history": return self.send_json(200,{"messages":history(100)})
        if route=="/api/memory": return self.send_json(200,{"memories":memories()})
        if route=="/api/status": return self.send_json(200,{"ok":True,"provider":os.getenv("RILEY_PROVIDER","auto")})
        if route=="/prototype":
            raw=(ROOT/"web"/"index.html").read_bytes()
            self.send_response(200)
            self.send_header("Set-Cookie",f"riley_session={SESSION_SECRET}; HttpOnly; SameSite=Strict; Path=/")
            self.send_header("Cache-Control","no-store")
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers()
            return self.wfile.write(raw)
        if route in ("/","/index.html","/core"):
            raw=(ROOT/"index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers()
            return self.wfile.write(raw)
        self.send_json(404,{"error":"Not found"})
    def do_POST(self):
        try:
            if not self.authorized(): raise ValueError("Session not authorized; open Riley home page first")
            origin=self.headers.get("Origin")
            if origin not in ("http://127.0.0.1:8765","http://localhost:8765"):
                raise ValueError("Requests must originate from the local Riley interface")
            if self.headers.get("Host") not in ("127.0.0.1:8765","localhost:8765"):
                raise ValueError("Invalid host")
            size=int(self.headers.get("Content-Length","0"))
            if not 0<size<=1100000: raise ValueError("Invalid request size")
            data=json.loads(self.rfile.read(size))
            route=urlparse(self.path).path
            if route=="/api/chat":
                message=data.get("message")
                if not isinstance(message,str) or not message.strip() or len(message)>10000: raise ValueError("Invalid message")
                answer=model_request(history(29)+[{"role":"user","content":message}])
                add_message("user",message);add_message("assistant",answer)
                result={"reply":answer}
            elif route=="/api/remember":
                remember(data.get("key"),data.get("value"));result={"saved":True}
            elif route=="/api/file/read":
                result={"content":read_file(data.get("path"))}
            elif route=="/api/file/preview":
                result=write_file(data.get("path"),data.get("content"))
            elif route=="/api/file/write":
                if data.get("approve") is not True: raise ValueError("Approval required")
                result=write_file(data.get("path"),data.get("content"),True,data.get("token"))
            else: return self.send_json(404,{"error":"Not found"})
            self.send_json(200,result)
        except (ValueError,UnicodeError,KeyError) as e: self.send_json(400,{"error":str(e)})
        except Exception as e: self.send_json(503,{"error":str(e)})

def main():
    init()
    print("Riley Core: http://127.0.0.1:8765/",flush=True)
    ThreadingHTTPServer(("127.0.0.1",8765),Handler).serve_forever()

if __name__=="__main__": main()
