@echo off
cd /d "%~dp0"

set "PY_VERSION=3.13.15"
set "PYEXE="

where py >nul 2>nul && set "PYEXE=py"
if not defined PYEXE (where python >nul 2>nul && set "PYEXE=python")
if not defined PYEXE call :instalar_python

if not defined PYEXE (
    echo.
    echo No he podido instalar Python automaticamente en este ordenador.
    echo Instalalo tu a mano desde https://python.org y vuelve a hacer
    echo doble click en este fichero.
    pause
    exit /b 1
)

"%PYEXE%" src\formulario.py
if errorlevel 1 pause
exit /b 0

:instalar_python
echo No se ha encontrado Python en este ordenador.
echo Instalando una copia solo para tu usuario, sin hacer falta ser
echo administrador. Esto tarda uno o dos minutos la primera vez...
echo.

set "PY_INSTALADOR=%TEMP%\python-instalador-autominer.exe"
set "PY_URL=https://www.python.org/ftp/python/%PY_VERSION%/python-%PY_VERSION%-amd64.exe"

where curl >nul 2>nul
if errorlevel 1 (
    powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%PY_INSTALADOR%' -UseBasicParsing } catch { exit 1 }"
) else (
    curl.exe -L --fail -o "%PY_INSTALADOR%" "%PY_URL%"
)

if not exist "%PY_INSTALADOR%" (
    echo No se pudo descargar el instalador de Python. Comprueba tu conexion
    echo a internet e intentalo de nuevo.
    exit /b 0
)

echo Instalando Python %PY_VERSION%...
"%PY_INSTALADOR%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_tcltk=1 Include_test=0
del "%PY_INSTALADOR%" >nul 2>nul

set "PY_HOME=%LocalAppData%\Programs\Python\Python313"
if exist "%PY_HOME%\python.exe" (
    set "PYEXE=%PY_HOME%\python.exe"
    echo Python instalado correctamente.
) else (
    where py >nul 2>nul && set "PYEXE=py"
)
exit /b 0
