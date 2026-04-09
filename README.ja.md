# Claude Session Browser

[English](README.md)

> **Claude Code の会話履歴を見るための、いちばんシンプルなツール。**
> Electron なし。React なし。設定ファイルなし。`python server.py` だけ。

Claude Code CLI の会話履歴をブラウザで閲覧・再開できる最小構成の Web UI です。
読み取り専用・ローカル完結・余計な機能一切なし。

---

## なぜこれを使うのか

Claude Code の UI ツールは他にも多くあります。ターミナル内蔵・ファイルエクスプローラー・プラグインシステムを備えたフル IDE 的なものが多いです。これはそういうツールではありません。

**Claude Session Browser はひとつのことだけやります：** 過去の会話を素早く見つけて再開すること。

- ファイル 2 つだけ（`server.py` + `index.html`）
- ビルド不要・Node.js 不要・データベース不要
- `claude` と打つだけで自動起動
- セッションファイルには一切触れない

---

## できること

- **セッション一覧** — プロジェクト別にグループ化・更新順にソート
- **全文ビューアー** — Markdown・コードブロック・テーブルをレンダリング
- **ターミナルで再開** — ワンクリックで Windows Terminal が開き `claude --resume` を実行
- **新規セッション** — プロジェクト名を指定して起動
- **プロジェクト別名** — 長いフォルダ名をわかりやすい名前に変更
- **キーボードショートカット** — `/` 検索・`↑↓` 移動・`Enter` 再開

## 必要なもの

- [Claude Code CLI](https://claude.ai/code) インストール済み
- Python 3.8 以上
- Windows Terminal（`wt.exe`）— 再開機能に必要

## インストール

```bash
git clone https://github.com/tomatomilk203/claude-chat-ui.git
cd claude-chat-ui
pip install -r requirements.txt
python server.py
```

[http://127.0.0.1:8766](http://127.0.0.1:8766) を開く。

## `claude` と打つだけで自動起動する設定（Windows）

`~/.bashrc` に追加：

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

または、リポジトリフォルダを PATH の先頭に追加するだけで、付属の `claude.bat` が自動的にラップします。

## キーボードショートカット

| キー | 操作 |
|------|------|
| `/` または `Ctrl+K` | 検索 |
| `↑` / `↓` | セッション移動 |
| `Enter` | ターミナルで再開 |
| `Esc` | 閉じる・キャンセル |

## 注意事項

- **読み取り専用** — セッションファイルを変更しません
- **ローカル完結** — データは外部に送信されません
- 30 秒ごとに自動更新

## ライセンス

MIT
