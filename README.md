# Claude Session Browser

[日本語](README.ja.md)

> **The simplest way to browse your Claude Code history.**
> No Electron. No React. No config files. Just `python server.py`.

A minimal web UI for browsing and resuming **Claude Code CLI** conversations — read-only, local-only, zero bloat.

---

## Why this over the alternatives?

There are many Claude Code UI projects out there. Most are full IDEs with terminals, file explorers, and plugin systems. This is not that.

**Claude Session Browser does one thing:** lets you find and resume past conversations, fast.

- 2 files (`server.py` + `index.html`)
- No build step, no Node.js, no database
- Opens automatically when you type `claude`
- Never touches your session files

---

## Features

- **Session list** — grouped by project, sorted by recency
- **Full message viewer** — Markdown, code blocks, tables rendered
- **Resume in terminal** — one click launches Windows Terminal with `claude --resume`
- **New session** — start Claude in a named project folder
- **Project aliases** — rename cryptic paths to readable labels
- **Keyboard shortcuts** — `/` search, `↑↓` navigate, `Enter` resume

## Requirements

- [Claude Code CLI](https://claude.ai/code) installed
- Python 3.8+
- Windows Terminal (`wt.exe`) — for resume feature

## Install

```bash
git clone https://github.com/tomatomilk203/claude-chat-ui.git
cd claude-chat-ui
pip install -r requirements.txt
python server.py
```

Open [http://127.0.0.1:8766](http://127.0.0.1:8766).

## Auto-open when you type `claude` (Windows)

Add to `~/.bashrc`:

```bash
_start_claude_ui() {
  if ! netstat -ano 2>/dev/null | grep -q ":8766 "; then
    cd /path/to/claude-chat-ui && python server.py &>/dev/null &
    disown
    cd - &>/dev/null
    sleep 2
  fi
  powershell.exe -Command "Start-Process 'http://127.0.0.1:8766'" &>/dev/null &
  disown
}
claude() { _start_claude_ui; command claude "$@"; }
```

Or add the repo folder to your PATH — the included `claude.bat` wraps the command automatically.

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `/` or `Ctrl+K` | Search |
| `↑` / `↓` | Navigate sessions |
| `Enter` | Resume in terminal |
| `Esc` | Close / cancel |

## Notes

- **Read-only** — never modifies your session files
- **Local only** — no data leaves your machine
- Auto-refreshes every 30 seconds

## License

MIT
