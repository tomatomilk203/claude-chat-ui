from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
import asyncio
import json
import os
import tempfile
import shutil
import subprocess
import threading
from pathlib import Path
from datetime import datetime

app = FastAPI()

CLAUDE_DIR   = Path.home() / ".claude" / "projects"
BASE_DIR     = Path(__file__).parent
SESSIONS_DIR = BASE_DIR / "sessions"   # named chat folders
UPLOADS_DIR  = BASE_DIR / "uploads"    # image attachments
META_FILE    = BASE_DIR / "meta.json"  # session name/path metadata

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# ── Metadata helpers ────────────────────────────────────────────────────────

def load_meta() -> dict:
    if META_FILE.exists():
        try:
            return json.loads(META_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_meta(meta: dict):
    META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Session parsing ──────────────────────────────────────────────────────────

def extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""

def extract_tools(content):
    if not isinstance(content, list):
        return []
    return [{"name": b.get("name", ""), "input": b.get("input", {})}
            for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]

def is_meta(text: str) -> bool:
    if not text:
        return True
    return any(text.strip().startswith(p) for p in [
        "<local-command", "<command-name", "<system-reminder", "<user-prompt-submit-hook"
    ])

def parse_session(path: Path):
    messages, cwd = [], None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    t = obj.get("type", "")
                    if cwd is None and "cwd" in obj:
                        cwd = obj["cwd"]
                    if t == "user" and not obj.get("isMeta"):
                        text = extract_text(obj.get("message", {}).get("content", ""))
                        if text and not is_meta(text):
                            messages.append({"role": "user", "content": text,
                                             "tools": [], "timestamp": obj.get("timestamp", "")})
                    elif t == "assistant":
                        content = obj.get("message", {}).get("content", [])
                        text = extract_text(content)
                        tools = extract_tools(content)
                        if text or tools:
                            messages.append({"role": "assistant", "content": text,
                                             "tools": tools, "timestamp": obj.get("timestamp", "")})
                except Exception:
                    continue
    except Exception:
        pass
    return messages, cwd

def project_label(raw: str) -> str:
    if raw.startswith("C--Users-uni-"):
        return "~/" + raw[len("C--Users-uni-"):]
    if raw == "C--Users-uni":
        return "~"
    return raw

def all_sessions():
    meta = load_meta()
    sessions = []
    if not CLAUDE_DIR.exists():
        return sessions

    for proj_dir in CLAUDE_DIR.iterdir():
        if not proj_dir.is_dir():
            continue
        for jf in proj_dir.glob("*.jsonl"):
            msgs, cwd = parse_session(jf)
            user_msgs = [m for m in msgs if m["role"] == "user"]
            if not user_msgs:
                continue
            first = user_msgs[0]["content"]
            last  = msgs[-1]
            sid   = jf.stem
            m     = meta.get(sid, {})

            title = m.get("name") or (first[:50] + ("…" if len(first) > 50 else ""))
            sessions.append({
                "id":             sid,
                "project":        project_label(proj_dir.name),
                "title":          title,
                "custom_name":    m.get("name", ""),
                "folder_path":    m.get("folder_path", ""),
                "last_timestamp": last["timestamp"],
                "last_message":   (last["content"] or "(tool use)")[:60],
                "message_count":  len(msgs),
                "cwd":            m.get("folder_path") or cwd or str(Path.home()),
            })

    sessions.sort(key=lambda x: x["last_timestamp"], reverse=True)
    return sessions


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/api/sessions")
def api_sessions():
    return all_sessions()

@app.get("/api/sessions/{session_id}")
def api_session(session_id: str):
    meta = load_meta()
    m = meta.get(session_id, {})
    for proj_dir in CLAUDE_DIR.iterdir():
        if not proj_dir.is_dir():
            continue
        jf = proj_dir / f"{session_id}.jsonl"
        if jf.exists():
            msgs, cwd = parse_session(jf)
            return {
                "session_id":  session_id,
                "cwd":         m.get("folder_path") or cwd or str(Path.home()),
                "custom_name": m.get("name", ""),
                "folder_path": m.get("folder_path", ""),
                "messages":    msgs,
            }
    return {"session_id": session_id, "cwd": str(Path.home()), "messages": []}


@app.post("/api/new-chat")
async def api_new_chat(request: Request):
    """Create a named chat folder, returns folder_path."""
    body = await request.json()
    name = body.get("name", "").strip()
    if not name:
        return {"folder_path": str(Path.home()), "name": ""}

    # Safe folder name
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip()
    folder = SESSIONS_DIR / safe
    folder.mkdir(parents=True, exist_ok=True)

    # Write a README so it's visible in Explorer
    readme = folder / "README.md"
    if not readme.exists():
        readme.write_text(f"# {name}\n\nClaude Chat セッション\n作成: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
                          encoding="utf-8")

    return {"folder_path": str(folder), "name": name}


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    """Save uploaded image and return its local path."""
    ext  = Path(file.filename).suffix.lower() or ".png"
    name = f"img_{int(datetime.now().timestamp()*1000)}{ext}"
    dest = UPLOADS_DIR / name
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"path": str(dest), "name": name}


@app.get("/api/test")
async def api_test():
    import subprocess, shutil, tempfile, os
    claude_path = shutil.which("claude") or r"C:\Users\uni\AppData\Roaming\npm\claude.cmd"

    # テンポラリファイルにメッセージを書いてclaudeに渡す
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    tmp.write("say hi in one word")
    tmp.close()

    try:
        cmd = f'"{claude_path}" -p --output-format json --dangerously-skip-permissions'
        with open(tmp.name, "rb") as f:
            result = subprocess.run(
                cmd, shell=True, stdin=f,
                capture_output=True, timeout=60
            )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.decode("utf-8", errors="replace")[:500],
            "stderr": result.stderr.decode("utf-8", errors="replace")[:500],
            "returncode": result.returncode,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        os.unlink(tmp.name)


@app.post("/api/send")
async def api_send(request: Request):
    body       = await request.json()
    message    = body.get("message", "")
    session_id = body.get("session_id")
    cwd        = body.get("cwd", str(Path.home()))
    chat_name  = body.get("chat_name", "")

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    tmp.write(message)
    tmp.close()

    claude_path = shutil.which("claude") or r"C:\Users\uni\AppData\Roaming\npm\claude.cmd"
    flags = "--output-format stream-json --include-partial-messages --dangerously-skip-permissions"
    cmd = f'"{claude_path}" -p {flags}'
    if session_id:
        cmd += f" --resume {session_id}"
    if chat_name:
        cmd += f' -n "{chat_name.replace(chr(34), chr(39))}"'

    cwd_path = cwd if cwd and Path(cwd).exists() else str(Path.home())

    queue = asyncio.Queue()
    loop  = asyncio.get_event_loop()

    def run_claude():
        try:
            with open(tmp.name, "rb") as f:
                proc = subprocess.Popen(
                    cmd, shell=True, stdin=f,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    cwd=cwd_path,
                )
                for line in iter(proc.stdout.readline, b""):
                    loop.call_soon_threadsafe(queue.put_nowait, line)
                proc.wait()
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, json.dumps({"type":"error","msg":str(e)}).encode())
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    threading.Thread(target=run_claude, daemon=True).start()

    async def stream():
        new_sid   = session_id
        prev_text = ""

        while True:
            raw = await queue.get()
            if raw is None:
                break
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                t   = obj.get("type", "")

                if t == "system" and obj.get("subtype") == "init":
                    new_sid = obj.get("session_id", session_id)
                    if chat_name and new_sid:
                        meta = load_meta()
                        meta[new_sid] = {
                            "name": chat_name,
                            "folder_path": cwd_path if cwd_path != str(Path.home()) else "",
                            "created": datetime.now().isoformat(),
                        }
                        save_meta(meta)
                    yield f"data: {json.dumps({'type':'init','session_id':new_sid})}\n\n"

                elif t == "assistant":
                    content = obj.get("message", {}).get("content", [])
                    text    = extract_text(content)
                    tools   = extract_tools(content)
                    if text and text != prev_text:
                        prev_text = text
                        yield f"data: {json.dumps({'type':'text','content':text,'tools':tools})}\n\n"
                    elif tools and not text:
                        yield f"data: {json.dumps({'type':'tools','tools':tools})}\n\n"

                elif t == "result":
                    yield f"data: {json.dumps({'type':'done','session_id':new_sid})}\n\n"

                elif t == "error":
                    yield f"data: {json.dumps({'type':'done','session_id':new_sid,'error':obj.get('msg','')})}\n\n"

            except Exception:
                continue

        yield f"data: {json.dumps({'type':'done','session_id':new_sid})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream", headers={
        "Cache-Control":     "no-cache",
        "Connection":        "keep-alive",
        "X-Accel-Buffering": "no",
    })



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8766, log_level="warning")
