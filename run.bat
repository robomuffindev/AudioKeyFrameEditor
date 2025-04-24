@echo off
echo Activating virtual environment...
call .\venv\Scripts\activate.bat
if not exist ".\venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

echo Starting Audio Keyframe Editor...
python main.py
if errorlevel 1 (
    echo Error: Application exited with an error.
    pause
    exit /b 1
)

echo Application closed.
exit /b 0
