@echo off
cd /d "%~dp0"

rem Borra de este ordenador cualquier rastro de que aqui se ha minado
rem criptomoneda: motores descargados, configuracion con la wallet,
rem ajustes de seguridad de Windows tocados para minar mas rapido, y
rem por ultimo esta misma carpeta del proyecto (el codigo sigue a
rem salvo en GitHub). Pide permiso de administrador porque hace falta
rem para deshacer esos ajustes de seguridad. Ver src/limpieza.py.

net session >nul 2>nul
if not %errorlevel%==0 (
    echo Este programa pide permiso de administrador de Windows una vez,
    echo para poder deshacer los ajustes que se hayan cambiado al minar.
    echo Acepta el aviso que va a aparecer...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -WorkingDirectory '%~dp0' -Verb RunAs"
    exit /b 0
)

set "PYEXE="
py --version >nul 2>nul && set "PYEXE=py"
if not defined PYEXE (python --version >nul 2>nul && set "PYEXE=python")

if defined PYEXE goto :con_python
goto :sin_python

:con_python
rem src\limpieza.py pregunta primero (con una ventana) si se quiere
rem seguir, porque esto no se puede deshacer. Si el usuario dice que no,
rem devuelve un codigo distinto de 0 y aqui se cancela sin borrar nada.
"%PYEXE%" src\limpieza.py
if errorlevel 1 goto :cancelado
goto :borrar_carpeta

:sin_python
echo No se ha encontrado Python en este ordenador: se puede borrar lo
echo descargado y la configuracion, pero no se podran deshacer los
echo ajustes de seguridad de Windows que se hayan tocado para minar mas
echo rapido (hace falta Python para eso). Instala Python o usa antes
echo "Iniciar minado.bat" si quieres la limpieza completa.
echo.
set /p CONFIRMA="Escribe SI y pulsa Intro para borrar lo que se pueda sin Python: "
if /I not "%CONFIRMA%"=="SI" goto :cancelado

if exist "bin" (
    for /d %%D in ("bin\*") do rmdir /s /q "%%D" >nul 2>nul
    for %%F in ("bin\*") do (
        if /I not "%%~nxF"=="LEEME.md" del /f /q "%%F" >nul 2>nul
    )
)
if exist "config.md" del /f /q "config.md" >nul 2>nul
goto :borrar_carpeta

:cancelado
echo.
echo Cancelado. No se ha borrado ni cambiado nada.
pause
exit /b 1

:borrar_carpeta
set "PROYECTO=%~dp0"
if "%PROYECTO:~-1%"=="\" set "PROYECTO=%PROYECTO:~0,-1%"
rem Se genera un pequeno .cmd aparte (en TEMP) en vez de meter varios
rem comandos en una sola linea "cmd /c ...": con una carpeta que
rem pudiera tener espacios en el nombre, las comillas anidadas de una
rem sola linea son muy fragiles. Este .cmd espera 2 segundos (a que
rem esta ventana suelte la carpeta), la borra entera, y se borra el
rem solo al final.
set "BORRADOR=%TEMP%\autominer_borrado_%RANDOM%.cmd"
> "%BORRADOR%" echo @echo off
>> "%BORRADOR%" echo timeout /t 2 /nobreak ^>nul
>> "%BORRADOR%" echo rmdir /s /q "%PROYECTO%"
>> "%BORRADOR%" echo del "%BORRADOR%"

echo.
echo Borrando esta carpeta del proyecto (%PROYECTO%)...
cd /d "%TEMP%"
start "" /min cmd /c "%BORRADOR%"

echo.
echo Listo. Esta ventana se puede cerrar; la carpeta del proyecto
echo terminara de borrarse sola en un par de segundos.
pause
exit /b 0
