# Claude Session Browser

**Claude Code CLI** の会話履歴をブラウザで快適に閲覧・再開できる軽量 Web UI です。

## できること

- **会話履歴の一覧表示** — プロジェクトフォルダごとにグループ化して表示
- **全文ビューアー** — Markdown・コードブロック・テーブルをレンダリング表示
- **ターミナルで再開** — ワンクリックで Windows Terminal が開き `claude --resume <id>` を実行
- **新規セッション起動** — プロジェクト名を指定して Claude を起動
- **プロジェクト別名** — 長いフォルダ名をわかりやすい名前に変更
- **キーボードショートカット** — `/` で検索、`↑↓` で移動、`Enter` で再開

## 必要なもの

- [Claude Code CLI](https://claude.ai/code) インストール済み・認証済み
- Python 3.8 以上
- Windows Terminal（`wt.exe`）— 「ターミナルで再開」機能に必要

## インストール

```bash
git clone https://github.com/tomatomilk203/claude-chat-ui.git
cd claude-chat-ui
pip install -r requirements.txt
```

## 起動

```bash
python server.py
```

ブラウザで [http://127.0.0.1:8766](http://127.0.0.1:8766) を開いてください。

## ターミナルを開いたら自動起動する（Windows）

ターミナルを開くたびにサーバーが立ち上がり、ブラウザも自動で開くようにするには、`~/.bashrc` に以下を追加します：

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

または付属の `claude.bat` を使う方法もあります。リポジトリフォルダを PATH の先頭に追加するだけで、`claude` コマンドに自動的にラップされます。

```
# PATH に追加（PowerShell）
$env:PATH = "C:\path\to\claude-chat-ui;" + $env:PATH
```

## キーボードショートカット

| キー | 操作 |
|------|------|
| `/` または `Cmd+K` | 検索ボックスにフォーカス |
| `↑` / `↓` | セッションを上下に移動 |
| `Enter` | 選択中のセッションをターミナルで再開 |
| `Esc` | モーダルを閉じる / フォーカス解除 |

## 注意事項

- 読み取り専用 — このツールは Claude のセッションファイルを一切変更しません
- ローカル完結 — データは外部に送信されません
- 「ターミナルで再開」は Windows Terminal（`wt.exe`）が必要です
- セッション一覧は 30 秒ごとに自動更新されます

## ライセンス

MIT
