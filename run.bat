@echo off
rem Starts Entity Toolkit in the background (no console window). It stops by itself when Dead by Daylight closes.
rem First launch: it opens the Setup page. Log: data\entity_toolkit.log
rem To see the console instead (useful to debug):  python -m entity_toolkit
cd /d "%~dp0"
start "" pythonw -m entity_toolkit %*
