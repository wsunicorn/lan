@echo off
cd /d "%~dp0"
powershell -Command "Start-Process cmd -ArgumentList '/c %~dp0setup.bat' -Verb RunAs" 