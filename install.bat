@echo off
echo Checking for Python...
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH. Please install Python 3.8+ and add it to your PATH.
    pause
    exit /b 1
)

echo Creating virtual environment (venv)...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b 1
)

echo Activating virtual environment and installing dependencies...
call .\venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies. Check requirements.txt and your internet connection.
    pause
    exit /b 1
)

echo Installation complete!
echo You can now run the application using run.bat
pause
exit /b 0
