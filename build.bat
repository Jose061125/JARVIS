@echo off
REM ============================================================
REM  Script para construir ECHONEX.exe con PyInstaller
REM  Ejecutar en Windows con: build.bat
REM ============================================================

echo Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Construyendo ECHONEX.exe...
pyinstaller ^
    --onefile ^
    --noconsole ^
    --name "ECHONEX" ^
    --icon "jarvis/assets/icon.ico" ^
    --add-data "jarvis/assets;jarvis/assets" ^
    --hidden-import "customtkinter" ^
    --hidden-import "edge_tts" ^
    --hidden-import "pygame" ^
    --hidden-import "speech_recognition" ^
    --hidden-import "groq" ^
    main.py

echo.
echo Listo! Encuentra ECHONEX.exe en la carpeta dist/
pause
