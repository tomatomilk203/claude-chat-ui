@echo off
C:\Windows\System32\netstat.exe -ano | C:\Windows\System32\findstr.exe ":8766 " >nul 2>&1
if errorlevel 1 (
    start /b "" python "C:\Users\uni\claude-ui\server.py" >nul 2>&1
    C:\Windows\System32\timeout.exe /t 2 /nobreak >nul
)
powershell -Command "Start-Process 'http://127.0.0.1:8766'"
claude %*
