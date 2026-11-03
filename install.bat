@echo off
rem Installs the Python dependencies (once). Needs Python 3.10+ on Windows 10/11.
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Done. Start the toolkit with run.bat, then follow the Setup page that opens.
pause
