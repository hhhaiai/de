@echo off
:loop
cls
echo [Claude Code Status Monitor]
echo ===========================
call claude-statusbar
echo ===========================
echo Press Ctrl+C to exit
timeout /t 5 >nul
goto loop