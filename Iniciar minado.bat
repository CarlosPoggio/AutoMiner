@echo off
cd /d "%~dp0"

set "PY_VERSION=3.13.15"
set "PYEXE="

rem OJO: no usar "where" para detectar Python. Windows trae de serie un
rem "alias de ejecucion" falso para python.exe/python3.exe que aparece
rem en el PATH aunque Python no este instalado (abre la Microsoft Store
rem o da error al ejecutarlo). "where" lo encontraria igualmente. Por
rem eso se intenta ejecutar de verdad y se comprueba el resultado.
py --version >nul 2>nul && set "PYEXE=py"
if not defined PYEXE (python --version >nul 2>nul && set "PYEXE=python")
if not defined PYEXE call :instalar_python

if not defined PYEXE (
    echo.
    echo No he podido instalar Python automaticamente en este ordenador.
    echo Instalalo tu a mano desde https://python.org y vuelve a hacer
    echo doble click en este fichero.
    pause
    exit /b 1
)

if not exist "bin\cacert.pem" call :asegurar_certificados

"%PYEXE%" src\formulario.py
if errorlevel 1 pause
exit /b 0

:asegurar_certificados
rem En un Windows recien instalado (o cualquier equipo donde nunca se
rem ha usado un navegador), el almacen de certificados de Windows puede
rem estar casi vacio: se rellena bajo demanda, y Python nunca dispara
rem esa descarga por su cuenta. curl.exe (a diferencia de Python) si usa
rem el mismo mecanismo que un navegador, asi que de paso "calienta" el
rem almacen. Descargamos ademas un paquete de certificados publicos de
rem confianza (el mismo que usan Mozilla/certifi) como respaldo fijo,
rem para no depender solo de ese almacen.
if not exist "bin" mkdir "bin" >nul 2>nul

where curl >nul 2>nul
if errorlevel 1 (
    powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'https://curl.se/ca/cacert.pem' -OutFile 'bin\cacert.pem' -UseBasicParsing } catch { exit 1 }"
) else (
    curl.exe -L --fail -o "bin\cacert.pem" "https://curl.se/ca/cacert.pem"
)
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
    py --version >nul 2>nul && set "PYEXE=py"
)
exit /b 0
