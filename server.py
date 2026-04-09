from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import json, subprocess
from pathlib import Path

app = FastAPI()

CLAUDE_DIR   = Path.home() / ".claude" / "projects"
BASE_DIR     = Path(__file__).parent
ALIASES_FILE = BASE_DIR / "aliases.json"   # project raw_name → display name
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

def load_aliases():
    if ALIASES_FILE.exists():
        try: return json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
        except: pass
    return {}

def save_aliases(d):
    ALIASES_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_text(content):
    if isinstance(content, str): return content
    if isinstance(content, list):
        return "\n".join(b.get("text","") for b in content
                         if isinstance(b,dict) and b.get("type")=="text")
    return ""

def is_meta(text):
    if not text: return True
    return any(text.strip().startswith(p) for p in [
        "<local-command","<command-name","<system-reminder","<user-prompt-submit-hook"])

def parse_session(path: Path):
    messages, cwd = [], None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    obj = json.loads(line)
                    if cwd is None and "cwd" in obj:
                        cwd = obj["cwd"]
                    t = obj.get("type","")
                    if t == "user" and not obj.get("isMeta"):
                        text = extract_text(obj.get("message",{}).get("content",""))
                        if text and not is_meta(text):
                            messages.append({"role":"user","content":text,"timestamp":obj.get("timestamp","")})
                    elif t == "assistant":
                        text = extract_text(obj.get("message",{}).get("content",[]))
                        if text:
                            messages.append({"role":"assistant","content":text,"timestamp":obj.get("timestamp","")})
                except: continue
    except: pass
    return messages, cwd

def project_label(raw, aliases=None):
    if aliases and raw in aliases:
        return aliases[raw]
    if raw.startswith("C--Users-uni-"): return "~/" + raw[len("C--Users-uni-"):]
    if raw == "C--Users-uni": return "~"
    return raw

def all_sessions():
    aliases  = load_aliases()
    sessions = []
    if not CLAUDE_DIR.exists(): return sessions
    for proj_dir in CLAUDE_DIR.iterdir():
        if not proj_dir.is_dir(): continue
        for jf in proj_dir.glob("*.jsonl"):
            msgs, cwd = parse_session(jf)
            user_msgs = [m for m in msgs if m["role"]=="user"]
            if not user_msgs: continue
            first = user_msgs[0]["content"]
            last  = msgs[-1]
            title = first[:60] + ("…" if len(first)>60 else "")
            sessions.append({
                "id":             jf.stem,
                "project":        project_label(proj_dir.name, aliases),
                "project_raw":    proj_dir.name,
                "title":          title,
                "last_timestamp": last["timestamp"],
                "last_message":   last["content"][:80],
                "message_count":  len(msgs),
                "cwd":            cwd or str(Path.home()),
            })
    sessions.sort(key=lambda x: x["last_timestamp"], reverse=True)
    return sessions


@app.get("/")
def index(): return FileResponse(BASE_DIR / "index.html")

@app.get("/api/sessions")
def api_sessions(): return all_sessions()

@app.get("/api/sessions/{session_id}")
def api_session(session_id: str):
    for proj_dir in CLAUDE_DIR.iterdir():
        if not proj_dir.is_dir(): continue
        jf = proj_dir / f"{session_id}.jsonl"
        if jf.exists():
            msgs, cwd = parse_session(jf)
            return {"session_id": session_id, "cwd": cwd, "messages": msgs}
    return {"session_id": session_id, "messages": []}

@app.post("/api/resume/{session_id}")
def api_resume(session_id: str):
    """Windows Terminalで新タブを開いてclaudeを再開する"""
    cmd = f'claude --resume {session_id}'
    try:
        # Windows Terminal (wt.exe) で新タブ起動
        subprocess.Popen(
            f'wt.exe new-tab cmd /k "{cmd}"',
            shell=True, cwd=str(Path.home())
        )
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.post("/api/new")
async def api_new(request: Request):
    """プロジェクト名を指定してWindows Terminalで新規起動"""
    body    = await request.json()
    name    = body.get("name", "").strip()
    safe    = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip() if name else ""
    work_dir = str(Path.home())

    if safe:
        folder = SESSIONS_DIR / safe
        folder.mkdir(parents=True, exist_ok=True)
        work_dir = str(folder)

    try:
        subprocess.Popen(
            f'wt.exe new-tab --title "{name or "claude"}" cmd /k "claude"',
            shell=True, cwd=work_dir
        )
        return {"ok": True, "cwd": work_dir}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e), "cwd": work_dir}, status_code=500)

@app.post("/api/alias")
async def api_alias(request: Request):
    """プロジェクトの表示名を保存"""
    body    = await request.json()
    raw     = body.get("raw", "")
    display = body.get("display", "").strip()
    if not raw:
        return JSONResponse({"ok": False}, status_code=400)
    aliases = load_aliases()
    if display:
        aliases[raw] = display
    else:
        aliases.pop(raw, None)   # 空なら削除（デフォルト名に戻す）
    save_aliases(aliases)
    return {"ok": True}

@app.get("/api/aliases")
def api_get_aliases():
    return load_aliases()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8766, log_level="warning")
