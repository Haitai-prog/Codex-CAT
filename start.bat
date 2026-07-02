@echo off
set DEEPSEEK_API_KEY=YOUR_DEEPSEEK_API_KEY
echo Starting Codex CAT...
start http://localhost:8080
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir "%~dp0backend" --no-browser
pause
