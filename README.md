# Claude Session Browser

[日本語版 README はこちら](README.ja.md)

A lightweight web UI for browsing and resuming your **Claude Code CLI** conversation history — right from the browser.

![screenshot placeholder](https://via.placeholder.com/800x450?text=Claude+Session+Browser)

## What it does

Claude Code stores every conversation as a `.jsonl` file in `~/.claude/projects/`. This tool reads those files and gives you:

- **Session history browser** — all conversations grouped by project folder
- **Full message viewer** — rendered Markdown, code blocks, tables
- **Resume in terminal** — one click opens Windows Terminal and runs `claude --resume <id>`
- **New session launcher** — start Claude in a named project folder
- **Project aliases** — rename cryptic folder names to readable labels
- **Keyboard shortcuts** — `/` to search, `↑↓` to navigate, `Enter` to resume

## Requirements

- [Claude Code CLI](https://claude.ai/code) installed and authenticated
- Python 3.8+
- Windows Terminal (`wt.exe`) — for the "Resume in Terminal" feature

## Install

```bash
git clone https://github.com/tomatomilk203/claude-chat-ui.git
cd claude-chat-ui
pip install -r requirements.txt
```

## Run

```bash
python server.py
```

Then open [http://127.0.0.1:8766](http://127.0.0.1:8766) in your browser.

## Auto-launch on terminal open (Windows)

To have the server start and browser open automatically whenever you open a terminal, add this to your `~/.bashrc`:

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

claude() {
  _start_claude_ui
  command claude "$@"
}
```

Or use the included `claude.bat` — add the repo folder to your PATH and it wraps the `claude` command automatically.

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `/` or `Cmd+K` | Focus search |
| `↑` / `↓` | Navigate sessions |
| `Enter` | Resume selected session in terminal |
| `Esc` | Close modal / blur |

## Notes

- Read-only — this tool never modifies your Claude sessions
- Local only — no data leaves your machine
- The "Resume in Terminal" button requires Windows Terminal (`wt.exe`)
- Sessions are auto-refreshed every 30 seconds

## License

MIT
