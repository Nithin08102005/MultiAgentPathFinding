@echo off
title MAPF Web Simulator
cd /d "%~dp0"
echo.
echo  ============================================
echo   MAPF Warehouse Simulator - IIT Indore BTP
echo  ============================================
echo   Opening http://localhost:5000
echo   Press Ctrl+C to stop the server
echo  ============================================
echo.
start "" http://localhost:5000
python web_app\app.py
pause
