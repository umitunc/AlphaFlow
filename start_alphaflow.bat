@echo off
chcp 65001 >nul
title AlphaFlow Studio - AI Video Alpha Masking Tool
cd /d "%~dp0"
echo [AlphaFlow Studio] Baslatiliyor...
python main.py
if errorlevel 1 (
    echo.
    echo Bir hata olustu. Cikmak icin bir tusa basin...
    pause >nul
)
