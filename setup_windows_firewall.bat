@echo off
:: Sound Catcher Firewall Setup Batch Wrapper
:: Automatically requests Administrator privileges and runs setup_windows_firewall.ps1

TITLE Sound Catcher Firewall Setup

:: Check for Administrative privileges
NET SESSION >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [!] Requesting Administrative privileges to configure Windows Firewall...
    powershell -Command "Start-Process '%~0' -Verb RunAs"
    exit /b
)

:: Run PowerShell script with bypass execution policy
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows_firewall.ps1"
