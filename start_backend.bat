@echo off
echo Starting Super Manager Backend...
echo.
echo Make sure you have:
echo 1. Installed dependencies: pip install -r requirements.txt
echo 2. Created .env file with OPENAI_API_KEY
echo.
python -m uvicorn backend.main:app --reload --port 8000

