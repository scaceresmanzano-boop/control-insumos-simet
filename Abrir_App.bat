@echo off
title Control de Insumos Criticos - SIMET-USACH
cd /d "%~dp0"
echo Iniciando la app... se abrira sola en tu navegador.
echo No cierres esta ventana mientras uses la app.
python -m streamlit run app.py
pause
