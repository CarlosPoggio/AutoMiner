"""
Optimización de rendimiento en Windows que necesita permisos de
administrador: conceder el permiso "Lock pages in memory"
(SeLockMemoryPrivilege), imprescindible para que xmrig pueda usar
"huge pages" (memoria de página grande) al minar monedas de CPU
(RandomX: XMR, WOW, ZEPH, SAL). Sin esto, xmrig sigue minando, pero
más despacio (documentado hasta un ~20% menos de hashrate).

Importante: a diferencia del "MSR mod" (que xmrig necesita volver a
pedir como administrador CADA VEZ que arranca, porque carga un
controlador), este permiso solo hace falta concederlo UNA VEZ. Una vez
concedido a tu usuario de Windows, xmrig lo usa automáticamente en
todas las ejecuciones futuras, sin necesitar administrador — por eso
tiene sentido automatizarlo como un paso puntual, no cada vez que se
mina (ver docs/DECISIONS.md).

Solo librería estándar: se llama directamente a las funciones de LSA
de Windows con ctypes, sin ningún paquete externo (nada de pywin32).
Cada firma de función y cada estructura se verificó contra la
documentación oficial de Microsoft antes de usarla (no adivinada):
- learn.microsoft.com/windows/win32/secmgmt/managing-account-permissions
- learn.microsoft.com/windows/win32/secmgmt/opening-a-policy-object-handle
- learn.microsoft.com/windows/win32/secmgmt/using-lsa-unicode-strings
- learn.microsoft.com/windows/win32/api/ntsecapi/nf-ntsecapi-lsaaddaccountrights
"""

import ctypes
import os
from ctypes import wintypes

PRIVILEGIO_HUGE_PAGES = "SeLockMemoryPrivilege"

# Ver learn.microsoft.com/windows/win32/secmgmt/policy-object-access-rights.
# Los mínimos que exige LsaAddAccountRights (según su propia documentación).
_POLICY_CREATE_ACCOUNT = 0x00000010
_POLICY_LOOKUP_NAMES = 0x00000800

_ERROR_INSUFFICIENT_BUFFER = 122


class _LsaUnicodeString(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT),
        ("MaximumLength", wintypes.USHORT),
        ("Buffer", wintypes.LPWSTR),
    ]


class _LsaObjectAttributes(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.ULONG),
        ("RootDirectory", wintypes.HANDLE),
        ("ObjectName", ctypes.POINTER(_LsaUnicodeString)),
        ("Attributes", wintypes.ULONG),
        ("SecurityDescriptor", wintypes.LPVOID),
        ("SecurityQualityOfService", wintypes.LPVOID),
    ]


def _preparar_lsa_string(texto: str):
    """Devuelve (estructura, buffer). Hay que conservar el buffer vivo
    mientras se use la estructura: Buffer apunta a su memoria."""
    buffer = ctypes.create_unicode_buffer(texto)
    longitud = len(texto) * ctypes.sizeof(ctypes.c_wchar)
    estructura = _LsaUnicodeString(
        Length=longitud,
        MaximumLength=longitud + ctypes.sizeof(ctypes.c_wchar),
        Buffer=ctypes.cast(buffer, wintypes.LPWSTR),
    )
    return estructura, buffer


def _declarar_funciones(advapi32):
    advapi32.LookupAccountNameW.argtypes = [
        wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPVOID,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
    ]
    advapi32.LookupAccountNameW.restype = wintypes.BOOL

    advapi32.LsaOpenPolicy.argtypes = [
        ctypes.POINTER(_LsaUnicodeString), ctypes.POINTER(_LsaObjectAttributes),
        wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE),
    ]
    advapi32.LsaOpenPolicy.restype = ctypes.c_long

    advapi32.LsaAddAccountRights.argtypes = [
        wintypes.HANDLE, wintypes.LPVOID, ctypes.POINTER(_LsaUnicodeString), wintypes.ULONG,
    ]
    advapi32.LsaAddAccountRights.restype = ctypes.c_long

    advapi32.LsaRemoveAccountRights.argtypes = [
        wintypes.HANDLE, wintypes.LPVOID, wintypes.BOOLEAN,
        ctypes.POINTER(_LsaUnicodeString), wintypes.ULONG,
    ]
    advapi32.LsaRemoveAccountRights.restype = ctypes.c_long

    advapi32.LsaClose.argtypes = [wintypes.HANDLE]
    advapi32.LsaClose.restype = ctypes.c_long

    advapi32.LsaNtStatusToWinError.argtypes = [ctypes.c_long]
    advapi32.LsaNtStatusToWinError.restype = wintypes.ULONG


def _resolver_sid(advapi32, nombre_usuario: str):
    """Devuelve (buffer_del_sid, mensaje_error_o_None)."""
    cb_sid = wintypes.DWORD(0)
    cch_dominio = wintypes.DWORD(0)
    tipo = wintypes.DWORD(0)

    advapi32.LookupAccountNameW(
        None, nombre_usuario, None, ctypes.byref(cb_sid),
        None, ctypes.byref(cch_dominio), ctypes.byref(tipo),
    )
    error = ctypes.get_last_error()
    if cb_sid.value == 0 or error not in (0, _ERROR_INSUFFICIENT_BUFFER):
        return None, f"No se pudo averiguar el tamaño del identificador de '{nombre_usuario}' (error {error})."

    sid_buffer = ctypes.create_string_buffer(cb_sid.value)
    dominio_buffer = ctypes.create_unicode_buffer(cch_dominio.value)
    ok = advapi32.LookupAccountNameW(
        None, nombre_usuario, sid_buffer, ctypes.byref(cb_sid),
        dominio_buffer, ctypes.byref(cch_dominio), ctypes.byref(tipo),
    )
    if not ok:
        return None, f"No se pudo identificar al usuario '{nombre_usuario}' (error {ctypes.get_last_error()})."
    return sid_buffer, None


def conceder_privilegio_huge_pages(nombre_usuario: "str | None" = None) -> "tuple[bool, str]":
    """
    Concede el permiso "Lock pages in memory" (SeLockMemoryPrivilege) al
    usuario indicado (por defecto, el que está ejecutando este proceso).
    Necesita permisos de administrador para funcionar. Es seguro llamarlo
    aunque el permiso ya estuviera concedido (Windows no da error).
    Devuelve (ok, mensaje) — el mensaje es para mostrar al usuario, tanto
    si sale bien como si sale mal.
    """
    if os.name != "nt":
        return False, "Esta optimización solo aplica en Windows."
    if nombre_usuario is None:
        nombre_usuario = os.environ.get("USERNAME", "")
    if not nombre_usuario:
        return False, "No se pudo determinar el usuario actual de Windows."

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    _declarar_funciones(advapi32)

    sid_buffer, error = _resolver_sid(advapi32, nombre_usuario)
    if error:
        return False, error

    atributos = _LsaObjectAttributes()
    ctypes.memset(ctypes.byref(atributos), 0, ctypes.sizeof(atributos))
    atributos.Length = ctypes.sizeof(atributos)

    handle_politica = wintypes.HANDLE()
    estado = advapi32.LsaOpenPolicy(
        None, ctypes.byref(atributos),
        _POLICY_CREATE_ACCOUNT | _POLICY_LOOKUP_NAMES,
        ctypes.byref(handle_politica),
    )
    if estado != 0:
        codigo = advapi32.LsaNtStatusToWinError(estado)
        return False, (
            f"No se pudo abrir la política de seguridad de Windows (código {codigo}). "
            "¿Se está ejecutando como administrador?"
        )

    try:
        privilegio, _buffer_privilegio = _preparar_lsa_string(PRIVILEGIO_HUGE_PAGES)
        estado = advapi32.LsaAddAccountRights(
            handle_politica, sid_buffer, ctypes.byref(privilegio), 1,
        )
        if estado != 0:
            codigo = advapi32.LsaNtStatusToWinError(estado)
            return False, f"No se pudo conceder el permiso de rendimiento (código {codigo})."
        return True, (
            f"Permiso de rendimiento concedido a '{nombre_usuario}'. Hace falta cerrar "
            "sesión en Windows (o reiniciar) una vez para que xmrig empiece a usarlo."
        )
    finally:
        advapi32.LsaClose(handle_politica)


def revocar_privilegio_huge_pages(nombre_usuario: "str | None" = None) -> "tuple[bool, str]":
    """
    Quita el permiso "Lock pages in memory" (SeLockMemoryPrivilege) al
    usuario indicado (por defecto, el que está ejecutando este proceso) —
    lo contrario de conceder_privilegio_huge_pages(), para dejar el
    ordenador tal y como estaba antes de minar (ver src/limpieza.py).
    Necesita permisos de administrador. Es seguro llamarlo aunque el
    permiso no estuviera concedido (Windows no da error, LsaRemoveAccountRights
    documenta que no falla si no había nada que quitar). Devuelve (ok,
    mensaje) — el mensaje es para mostrar al usuario, tanto si sale bien
    como si sale mal.
    """
    if os.name != "nt":
        return False, "Esta optimización solo aplica en Windows."
    if nombre_usuario is None:
        nombre_usuario = os.environ.get("USERNAME", "")
    if not nombre_usuario:
        return False, "No se pudo determinar el usuario actual de Windows."

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    _declarar_funciones(advapi32)

    sid_buffer, error = _resolver_sid(advapi32, nombre_usuario)
    if error:
        return False, error

    atributos = _LsaObjectAttributes()
    ctypes.memset(ctypes.byref(atributos), 0, ctypes.sizeof(atributos))
    atributos.Length = ctypes.sizeof(atributos)

    handle_politica = wintypes.HANDLE()
    estado = advapi32.LsaOpenPolicy(
        None, ctypes.byref(atributos),
        _POLICY_CREATE_ACCOUNT | _POLICY_LOOKUP_NAMES,
        ctypes.byref(handle_politica),
    )
    if estado != 0:
        codigo = advapi32.LsaNtStatusToWinError(estado)
        return False, (
            f"No se pudo abrir la política de seguridad de Windows (código {codigo}). "
            "¿Se está ejecutando como administrador?"
        )

    try:
        privilegio, _buffer_privilegio = _preparar_lsa_string(PRIVILEGIO_HUGE_PAGES)
        estado = advapi32.LsaRemoveAccountRights(
            handle_politica, sid_buffer, False, ctypes.byref(privilegio), 1,
        )
        if estado != 0:
            codigo = advapi32.LsaNtStatusToWinError(estado)
            return False, f"No se pudo quitar el permiso de rendimiento (código {codigo})."
        return True, f"Permiso de rendimiento quitado a '{nombre_usuario}'."
    finally:
        advapi32.LsaClose(handle_politica)
