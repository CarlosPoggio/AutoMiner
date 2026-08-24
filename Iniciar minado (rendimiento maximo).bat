@echo off
cd /d "%~dp0"

rem Este acceso arranca la app pidiendo permiso de administrador una
rem sola vez, para dos cosas: (1) concede el permiso de "huge pages" de
rem Windows a tu usuario (solo hace falta una vez; luego xmrig lo usa
rem solo, sin admin, en todas las ejecuciones futuras) y (2) al minar
rem con la CPU, deja que xmrig aplique el "MSR mod" (necesita admin
rem CADA vez que arranca, por eso hace falta este acceso separado en
rem vez de pedirlo siempre). Ambas cosas suben el hashrate de Monero y
rem monedas similares. Si prefieres no dar permisos de administrador,
rem usa "Iniciar minado.bat" en su lugar: sigue funcionando igual, solo
rem que un poco mas despacio en esas monedas.

net session >nul 2>nul
if not %errorlevel%==0 (
    echo Este acceso pide permiso de administrador de Windows una vez,
    echo para minar mas rapido. Acepta el aviso que va a aparecer...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -WorkingDirectory '%~dp0' -Verb RunAs"
    exit /b 0
)

rem Ya estamos como administrador: concede el permiso de rendimiento
rem (si Python todavia no esta instalado, se omite este paso por ahora
rem y "Iniciar minado.bat" lo instalara a continuacion; puedes volver a
rem usar este mismo acceso otra vez despues para concederlo).
set "PYEXE="
py --version >nul 2>nul && set "PYEXE=py"
if not defined PYEXE (python --version >nul 2>nul && set "PYEXE=python")

if defined PYEXE (
    "%PYEXE%" src\conceder_rendimiento.py

    rem Si "Aislamiento del nucleo / Integridad de memoria" y/o la lista
    rem de controladores vulnerables bloqueados de Windows estan activos,
    rem este script pregunta (con una ventana) si se quieren desactivar
    rem para el MSR mod. Si el usuario dice que si, deja el ordenador
    rem pidiendo un reinicio y NO abrimos la app todavia (salida 2).
    "%PYEXE%" src\comprobar_seguridad_rendimiento.py
    if errorlevel 2 exit /b 0
)

call "Iniciar minado.bat"
