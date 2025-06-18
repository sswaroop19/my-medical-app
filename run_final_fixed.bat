@echo off
echo Starting Final Fixed ChatGPT-style Medical Assistant...

REM Kill any running Python processes
taskkill /F /IM python.exe /T 2>nul

REM Clear Flask cache
if exist "__pycache__" (
    rmdir /S /Q "__pycache__"
)

REM Clear browser cache by deleting static files cache
echo Clearing static file cache...
if exist "static\__pycache__" (
    rmdir /S /Q "static\__pycache__"
)

REM Start the application
python app_final.py