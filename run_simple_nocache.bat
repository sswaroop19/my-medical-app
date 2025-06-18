@echo off
echo Clearing browser cache files...
echo Starting Simple Medical Assistant...

REM Kill any running Python processes
taskkill /F /IM python.exe /T 2>nul

REM Clear Flask cache
if exist "__pycache__" (
    rmdir /S /Q "__pycache__"
)

REM Start the application
python app_simple.py