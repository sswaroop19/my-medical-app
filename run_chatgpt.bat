@echo off
echo Starting ChatGPT-style Medical Assistant...

REM Kill any running Python processes
taskkill /F /IM python.exe /T 2>nul

REM Clear Flask cache
if exist "__pycache__" (
    rmdir /S /Q "__pycache__"
)

REM Start the application
python app_chatgpt.py