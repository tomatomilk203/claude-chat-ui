@echo off
echo Claude Chat UI を起動中...
echo ブラウザで http://127.0.0.1:8765 を開いてください
echo 終了するには Ctrl+C を押してください
cd /d %~dp0
python server.py
