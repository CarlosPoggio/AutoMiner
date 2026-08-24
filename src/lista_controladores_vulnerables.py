"""
"Lista de controladores vulnerables bloqueados" de Microsoft (Vulnerable
Driver Blocklist): una protección de seguridad de Windows, activada por
defecto desde la actualización de 2022 de Windows 11, que impide cargar
controladores con vulnerabilidades conocidas y documentadas — entre
ellos WinRing0x64.sys (CVE-2020-14979: un proceso sin privilegios puede
leer/escribir memoria del sistema y llegar a tener control total), que
es justo el controlador que necesita el "MSR mod" de xmrig. Es
INDEPENDIENTE de "Aislamiento del núcleo / Integridad de memoria" (ver
aislamiento_nucleo.py): desactivar una no desactiva la otra, y en este
proyecto se ha comprobado que ambas pueden estar bloqueando el MSR mod
a la vez — ver docs/DECISIONS.md.

Esto es una decisión real de seguridad, no un simple interruptor de
rendimiento, así que este módulo NUNCA la cambia por su cuenta: solo
ofrece leer el estado actual y cambiarlo cuando se le pide
explícitamente (el que pregunta al usuario y decide es
src/comprobar_seguridad_rendimiento.py / src/formulario.py).

Se lee y se cambia con el valor de registro que la propia Microsoft
documenta para esto (ver
support.microsoft.com/kb/5020779): HKLM\\SYSTEM\\CurrentControlSet\\
Control\\CI\\Config, valor VulnerableDriverBlocklistEnable (0/1). Con
librería estándar (winreg), sin ningún paquete externo.
"""

import platform
from pathlib import Path

_CLAVE_REGISTRO = r"SYSTEM\CurrentControlSet\Control\CI\Config"
_VALOR = "VulnerableDriverBlocklistEnable"

# Marca que dejamos si NOSOTROS desactivamos la protección, para poder
# preguntar más tarde (al detener el minado, o al cerrar la app) si el
# usuario quiere volver a activarla. Vive en bin/ (no se sube a git),
# igual que el resto de estado descargado/generado en marcha.
RUTA_MARCA = Path(__file__).resolve().parent.parent / "bin" / "_lista_bloqueo_desactivada_por_app"


def esta_activo() -> "bool | None":
    """
    True si la lista de controladores vulnerables bloqueados está activa
    (bloquearía el MSR mod de xmrig). False si no lo está. None si no se
    pudo averiguar (por ejemplo, esto no es Windows, o el valor de
    registro no existe) — en ese caso, mejor no ofrecer tocar nada.
    """
    if platform.system() != "Windows":
        return None

    import winreg  # solo existe en Windows; import tardío a propósito

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _CLAVE_REGISTRO) as clave:
            valor, _tipo = winreg.QueryValueEx(clave, _VALOR)
    except OSError:
        return None

    return bool(valor)


def desactivar() -> "tuple[bool, str]":
    """Desactiva la lista de controladores vulnerables bloqueados.
    Necesita administrador. Hace falta reiniciar el ordenador para que
    se aplique de verdad."""
    return _fijar_activado(0)


def reactivar() -> "tuple[bool, str]":
    """Vuelve a activarla. Necesita administrador. Hace falta reiniciar
    el ordenador para que se aplique de verdad."""
    return _fijar_activado(1)


def _fijar_activado(valor: int) -> "tuple[bool, str]":
    if platform.system() != "Windows":
        return False, "Esto solo aplica en Windows."

    import winreg  # solo existe en Windows; import tardío a propósito

    try:
        with winreg.CreateKeyEx(
            winreg.HKEY_LOCAL_MACHINE, _CLAVE_REGISTRO, 0, winreg.KEY_SET_VALUE
        ) as clave:
            winreg.SetValueEx(clave, _VALOR, 0, winreg.REG_DWORD, valor)
    except OSError as e:
        return False, (
            f"No se pudo cambiar el ajuste de seguridad de Windows ({e}). "
            "¿Se está ejecutando como administrador?"
        )

    return True, "Hecho. Hace falta reiniciar el ordenador para que se aplique de verdad."
