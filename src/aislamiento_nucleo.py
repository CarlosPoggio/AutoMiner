"""
"Aislamiento del núcleo" / "Integridad de memoria" (Memory Integrity,
también llamado HVCI): una protección de seguridad de Windows que
puede bloquear el "MSR mod" de xmrig, porque necesita cargar un
controlador antiguo (WinRing0x64.sys) que esta protección rechaza —
ver docs/DECISIONS.md.

Esto es una decisión real de seguridad, no un simple interruptor de
rendimiento, así que este módulo NUNCA la cambia por su cuenta: solo
ofrece leer el estado actual y cambiarlo cuando se le pide
explícitamente (el que pregunta al usuario y decide es
src/comprobar_aislamiento.py / src/formulario.py).

Para leer el estado se usa PowerShell sobre la clase WMI oficial de
Microsoft para esto, Win32_DeviceGuard (ver
learn.microsoft.com/windows/security/hardware-security/
enable-virtualization-based-protection-of-code-integrity). Para
cambiarlo, la clave de registro que la misma página documenta
oficialmente. Todo con librería estándar (subprocess, winreg, json),
sin ningún paquete externo.
"""

import json
import platform
import subprocess
from pathlib import Path

_CLAVE_REGISTRO = r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity"
_VALOR_MEMORY_INTEGRITY = 2  # según el WMI Win32_DeviceGuard de Microsoft

# Marca que dejamos si NOSOTROS desactivamos la protección, para poder
# preguntar más tarde (al detener el minado, o al cerrar la app) si el
# usuario quiere volver a activarla. Vive en bin/ (no se sube a git),
# igual que el resto de estado descargado/generado en marcha.
RUTA_MARCA = Path(__file__).resolve().parent.parent / "bin" / "_aislamiento_desactivado_por_app"


def esta_activo() -> "bool | None":
    """
    True si Integridad de memoria está activa Y funcionando ahora mismo
    (bloquearía el MSR mod de xmrig). False si no lo está. None si no
    se pudo averiguar (por ejemplo, esto no es Windows, o algo falla al
    consultarlo) — en ese caso, mejor no ofrecer tocar nada.
    """
    if platform.system() != "Windows":
        return None
    try:
        resultado = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                "Get-CimInstance -ClassName Win32_DeviceGuard "
                "-Namespace root\\Microsoft\\Windows\\DeviceGuard "
                "| Select-Object -ExpandProperty SecurityServicesRunning "
                "| ConvertTo-Json -Compress",
            ],
            capture_output=True, text=True, timeout=15,
        )
    except (subprocess.SubprocessError, OSError):
        return None

    salida = resultado.stdout.strip()
    if resultado.returncode != 0 or not salida:
        return False  # sin datos = no hay ningún servicio corriendo

    try:
        datos = json.loads(salida)
    except json.JSONDecodeError:
        return None

    valores = datos if isinstance(datos, list) else [datos]
    return _VALOR_MEMORY_INTEGRITY in valores


def desactivar() -> "tuple[bool, str]":
    """Desactiva Integridad de memoria. Necesita administrador. Hace
    falta reiniciar el ordenador para que se aplique de verdad."""
    return _fijar_activado(0)


def reactivar() -> "tuple[bool, str]":
    """Vuelve a activar Integridad de memoria. Necesita administrador.
    Hace falta reiniciar el ordenador para que se aplique de verdad."""
    return _fijar_activado(1)


def _fijar_activado(valor: int) -> "tuple[bool, str]":
    if platform.system() != "Windows":
        return False, "Esto solo aplica en Windows."

    import winreg  # solo existe en Windows; import tardío a propósito

    try:
        with winreg.CreateKeyEx(
            winreg.HKEY_LOCAL_MACHINE, _CLAVE_REGISTRO, 0, winreg.KEY_SET_VALUE
        ) as clave:
            winreg.SetValueEx(clave, "Enabled", 0, winreg.REG_DWORD, valor)
    except OSError as e:
        return False, (
            f"No se pudo cambiar el ajuste de seguridad de Windows ({e}). "
            "¿Se está ejecutando como administrador?"
        )

    return True, "Hecho. Hace falta reiniciar el ordenador para que se aplique de verdad."
