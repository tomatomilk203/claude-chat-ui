from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import json, subprocess
from pathlib import Path

app = FastAPI()

CLAUDE_DIR = Path.home() / ".claude" / "projects"
BASE_DIR   = Path(__file__).parent


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

def project_label(raw):
    if raw.startswith("C--Users-uni-"): return "~/" + raw[len("C--Users-uni-"):]
    if raw == "C--Users-uni": return "~"
    return raw

def all_sessions():
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
                "project":        project_label(proj_dir.name),
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
def api_new():
    """Windows Terminalで新タブを開いてclaudeを新規起動"""
    try:
        subprocess.Popen(
            'wt.exe new-tab cmd /k "claude"',
            shell=True, cwd=str(Path.home())
        )
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8766, log_level="warning")
