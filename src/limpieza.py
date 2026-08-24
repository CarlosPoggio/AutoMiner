#!/usr/bin/env python3
"""
Borra de este ordenador cualquier rastro de que aquí se ha minado
criptomoneda con esta app. Lo llama "limpieza.bat" (con doble click,
pidiendo permiso de administrador), pero también se puede ejecutar a
mano: `python3 src/limpieza.py` (o `--dry-run` para ver qué haría sin
tocar nada de verdad).

Qué borra o revierte, y por qué cada cosa cuenta como "rastro de
minado" (criterio: si es específico de minar, se borra; si es de
propósito general —como el propio Python— se deja, porque tenerlo
instalado no es una pista de haber minado):

- `config.md`: la moneda y la wallet que se eligieron para minar.
- Todo lo descargado en `bin/` (los motores xmrig/kawpowminer/lolMiner,
  sus carpetas descomprimidas, las DLLs/controladores que traen, y
  `bin/_descargas/`) — salvo `bin/LEEME.md`, que es parte del propio
  repositorio, no algo que se haya generado al minar.
- Cualquier `.log` suelto en la raíz del proyecto (por si algún motor
  dejó uno).
- Las dos protecciones de seguridad de Windows que esta misma app
  puede haber desactivado para el "MSR mod" de xmrig (Aislamiento del
  núcleo, lista de controladores vulnerables bloqueados) — solo si hay
  constancia de que fue esta app quien las tocó (ver
  `aislamiento_nucleo.RUTA_MARCA` / `lista_controladores_vulnerables.RUTA_MARCA`);
  si el usuario las había cambiado por su cuenta, no se tocan.
- El permiso de rendimiento "huge pages" (SeLockMemoryPrivilege)
  concedido para minar CPU más rápido.
- Reglas de cortafuegos y excepción de antivirus creadas (si las hay)
  para los motores de minado.
- El controlador WinRing0 (que usa el "MSR mod"), por si quedó
  instalado como servicio de Windows tras un cierre brusco.

Qué NO toca, a propósito: rastros de ejecución a nivel de sistema
operativo (Prefetch, Amcache, registro de sucesos de Windows...) —
eso ya no es "limpiar una app", es borrar el historial del propio
sistema, y queda fuera del propósito de esta herramienta.

Solo librería estándar (argparse, subprocess, shutil, tkinter para la
confirmación), igual que el resto del proyecto.
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aislamiento_nucleo  # noqa: E402
import lista_controladores_vulnerables  # noqa: E402
import rendimiento_windows  # noqa: E402

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

_FICHEROS_BIN_A_CONSERVAR = {"LEEME.md"}
_MOTORES_CONOCIDOS = ("xmrig.exe", "kawpowminer.exe", "lolMiner.exe")
# Nombre con el que xmrig registra el servicio de Windows del controlador
# WinRing0 al usar el "MSR mod". Si algún día cambia de nombre, este paso
# simplemente no encuentra nada que borrar (no falla).
_SERVICIO_WINRING0 = "WinRing0_1_2_0"


def elementos_bin_a_borrar(raiz: Path) -> "list[Path]":
    """Todo lo que hay dentro de bin/, salvo lo que es parte del propio
    repositorio (ver _FICHEROS_BIN_A_CONSERVAR)."""
    carpeta_bin = raiz / "bin"
    if not carpeta_bin.is_dir():
        return []
    return sorted(p for p in carpeta_bin.iterdir() if p.name not in _FICHEROS_BIN_A_CONSERVAR)


def borrar_bin(raiz: Path, dry_run: bool) -> "list[Path]":
    elementos = elementos_bin_a_borrar(raiz)
    if not dry_run:
        for p in elementos:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
    return elementos


def borrar_config(raiz: Path, dry_run: bool) -> "Path | None":
    config = raiz / "config.md"
    if not config.is_file():
        return None
    if not dry_run:
        config.unlink(missing_ok=True)
    return config


def buscar_logs_sueltos(raiz: Path) -> "list[Path]":
    """Con la configuración que usa este proyecto, los motores no
    escriben log a fichero por defecto (van todos a la consola/al log
    en pantalla de formulario.py) — esto es una red de seguridad por si
    alguno lo hizo de todos modos. No mira dentro de bin/ porque esa
    carpeta se borra entera de todas formas."""
    return sorted(raiz.glob("*.log"))


def borrar_logs_sueltos(raiz: Path, dry_run: bool) -> "list[Path]":
    logs = buscar_logs_sueltos(raiz)
    if not dry_run:
        for p in logs:
            p.unlink(missing_ok=True)
    return logs


def revertir_protecciones_seguridad(raiz: Path, dry_run: bool) -> "list[tuple[str, bool, str]]":
    """Reactiva las protecciones de seguridad de Windows que la propia
    app haya desactivado — solo si hay una marca suya (ver docstring del
    módulo). Si el usuario las desactivó por su cuenta, no se tocan."""
    resultados = []
    protecciones = (
        ("Aislamiento del núcleo / Integridad de memoria", aislamiento_nucleo),
        ("Lista de controladores vulnerables bloqueados", lista_controladores_vulnerables),
    )
    for nombre, modulo in protecciones:
        marca = modulo.RUTA_MARCA
        if not marca.is_file():
            continue
        if dry_run:
            resultados.append((nombre, True, "se reactivaría (simulación)"))
            continue
        ok, mensaje = modulo.reactivar()
        if ok:
            marca.unlink(missing_ok=True)
        resultados.append((nombre, ok, mensaje))
    return resultados


def revocar_huge_pages(dry_run: bool) -> "tuple[bool, str]":
    if dry_run:
        return True, "se quitaría el permiso de rendimiento (simulación)"
    return rendimiento_windows.revocar_privilegio_huge_pages()


def _ejecutar_mejor_esfuerzo(cmd: "list[str]", timeout: float = 15.0) -> bool:
    """Ejecuta un comando externo sin lanzar excepción si falla o si no
    encuentra nada que hacer — todo lo de esta función es "mejor
    esfuerzo": nunca debe impedir que el resto de la limpieza siga."""
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def quitar_reglas_firewall(raiz: Path, dry_run: bool) -> "tuple[bool, str]":
    if platform.system() != "Windows":
        return True, "no aplica en este sistema"
    if dry_run:
        return True, "se quitarían (simulación)"
    ok = True
    for nombre in _MOTORES_CONOCIDOS:
        ruta = raiz / "bin" / nombre
        ok = _ejecutar_mejor_esfuerzo(
            ["netsh", "advfirewall", "firewall", "delete", "rule", "name=all", f"program={ruta}"]
        ) and ok
    return ok, "hecho (mejor esfuerzo: no falla si no había ninguna)" if ok else "no se pudo ejecutar netsh"


def quitar_exclusion_defender(raiz: Path, dry_run: bool) -> "tuple[bool, str]":
    if platform.system() != "Windows":
        return True, "no aplica en este sistema"
    if dry_run:
        return True, "se quitaría (simulación)"
    ruta_bin = raiz / "bin"
    ok = _ejecutar_mejor_esfuerzo([
        "powershell", "-NoProfile", "-Command",
        f"Remove-MpPreference -ExclusionPath '{ruta_bin}' -ErrorAction SilentlyContinue",
    ])
    return ok, (
        "hecho (mejor esfuerzo: no falla si no había excepción, o si no hay Windows Defender)"
        if ok else "no se pudo ejecutar PowerShell"
    )


def quitar_servicio_winring0(dry_run: bool) -> "tuple[bool, str]":
    if platform.system() != "Windows":
        return True, "no aplica en este sistema"
    if dry_run:
        return True, "se quitaría si quedó instalado (simulación)"
    _ejecutar_mejor_esfuerzo(["sc.exe", "stop", _SERVICIO_WINRING0])
    ok = _ejecutar_mejor_esfuerzo(["sc.exe", "delete", _SERVICIO_WINRING0])
    return ok, "hecho (mejor esfuerzo: no falla si no estaba instalado)" if ok else "no se pudo ejecutar sc.exe"


def _confirmar() -> bool:
    import tkinter as tk
    from tkinter import messagebox

    raiz_tk = tk.Tk()
    raiz_tk.withdraw()
    respuesta = messagebox.askyesno(
        "Limpieza de minado",
        "Esto va a borrar de este ordenador, sin poder deshacerlo:\n\n"
        "- Los motores de minado descargados (xmrig, kawpowminer, lolMiner)\n"
        "- Tu configuración guardada (config.md), incluida la wallet\n"
        "- Los ajustes de seguridad de Windows que esta app haya "
        "desactivado para minar más rápido (si los tocó)\n"
        "- El permiso de rendimiento, las reglas de cortafuegos y la "
        "excepción de antivirus creadas para minar\n"
        "- Al terminar, esta misma carpeta del proyecto (el código sigue "
        "a salvo en GitHub; para volver a usarlo habría que descargarlo "
        "de nuevo)\n\n"
        "¿Seguro que quieres continuar?",
    )
    raiz_tk.destroy()
    return bool(respuesta)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Borra de este ordenador cualquier rastro de que aquí se ha minado criptomoneda."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Muestra qué se borraría o cambiaría, sin tocar nada de verdad.",
    )
    args = parser.parse_args(argv)
    dry_run = args.dry_run
    raiz = RAIZ_PROYECTO

    if not dry_run and not _confirmar():
        print("Cancelado. No se ha borrado ni cambiado nada.")
        return 1

    print("=== Limpieza de rastros de minado ===")
    if dry_run:
        print("(simulación: no se va a borrar ni cambiar nada de verdad)")
    print()

    for nombre, ok, mensaje in revertir_protecciones_seguridad(raiz, dry_run):
        print(f"[{'OK' if ok else 'AVISO'}] {nombre}: {mensaje}")

    ok, mensaje = revocar_huge_pages(dry_run)
    print(f"[{'OK' if ok else 'AVISO'}] Permiso de rendimiento (huge pages): {mensaje}")

    ok, mensaje = quitar_reglas_firewall(raiz, dry_run)
    print(f"[{'OK' if ok else 'AVISO'}] Reglas de cortafuegos: {mensaje}")

    ok, mensaje = quitar_exclusion_defender(raiz, dry_run)
    print(f"[{'OK' if ok else 'AVISO'}] Excepción de antivirus: {mensaje}")

    ok, mensaje = quitar_servicio_winring0(dry_run)
    print(f"[{'OK' if ok else 'AVISO'}] Controlador WinRing0: {mensaje}")

    config = borrar_config(raiz, dry_run)
    print(f"[OK] {'Configuración borrada: ' + config.name if config else 'No había configuración guardada'}")

    logs = borrar_logs_sueltos(raiz, dry_run)
    print(f"[OK] Temporales sueltos borrados: {len(logs)}")

    elementos = borrar_bin(raiz, dry_run)
    print(f"[OK] Motores de minado y ficheros descargados borrados: {len(elementos)}")

    if not dry_run:
        restantes = elementos_bin_a_borrar(raiz)
        if restantes:
            print(
                "[AVISO] No se pudieron borrar: " + ", ".join(p.name for p in restantes) +
                " — puede que un motor de minado siga en marcha; ciérralo y repite la limpieza."
            )

    print()
    print("Fin de la simulación." if dry_run else "Listo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
