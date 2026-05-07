#!/bin/bash
# Script para construir ECHONEX.exe con PyInstaller (desde Linux/Mac hacia Windows)
# O para correr en Linux/Mac directamente

echo "Instalando dependencias..."
pip install -r requirements.txt
pip install pyinstaller

echo ""
echo "Construyendo ejecutable..."
pyinstaller \
    --onefile \
    --noconsole \
    --name "ECHONEX" \
    --add-data "jarvis/assets:jarvis/assets" \
    --hidden-import "customtkinter" \
    --hidden-import "edge_tts" \
    --hidden-import "pygame" \
    --hidden-import "speech_recognition" \
    --hidden-import "groq" \
    main.py

echo ""
echo "Listo! Encuentra ECHONEX en la carpeta dist/"
