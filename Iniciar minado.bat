@echo off
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py src\formulario.py
    goto fin
)

where python >nul 2>nul
if %errorlevel%==0 (
    python src\formulario.py
    goto fin
)

echo No he encontrado Python instalado en este ordenador.
echo Instalalo desde https://python.org (marca la casilla "Add to PATH"
echo durante la instalacion) y vuelve a hacer doble click en este fichero.
pause
exit /b 1

:fin
if errorlevel 1 pause
