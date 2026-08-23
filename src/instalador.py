#!/usr/bin/env python3
"""
Descarga automática de los motores de minado (xmrig, kawpowminer,
lolMiner) desde la última release oficial de GitHub, para que el usuario
final no tenga que instalar nada a mano.

Idea general:
- `asegurar_motor(nombre_motor, raiz_proyecto, ...)` te devuelve la ruta a
  un ejecutable listo para usar. Si ya está instalado (en el PATH o en la
  carpeta bin/ del proyecto), no descarga nada. Si no está, consulta la
  API pública de GitHub, elige el archivo (.zip/.tar.gz) correcto para tu
  sistema operativo (y, para kawpowminer, para el fabricante de tu GPU),
  lo descarga, lo descomprime y deja el ejecutable en bin/ para que
  `motores.encontrar_motor` lo encuentre sin cambios.

Solo usa librería estándar (urllib, zipfile, tarfile): el usuario no
tiene que instalar dependencias de Python.
"""

import json
import os
import platform
import shutil
import stat
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Optional

import motores
import red


class InstaladorError(Exception):
    """Error claro y en español cuando no se puede preparar un motor."""


# Repositorio oficial de GitHub de cada motor (clave = nombre del motor tal
# y como aparece en motores.MOTORES).
_REPOS = {
    "xmrig": "xmrig/xmrig",
    "kawpowminer": "RavenCommunity/kawpowminer",
    "lolminer": "Lolliedieb/lolMiner-releases",
}

_USER_AGENT = "autominer-instalador/1.0"
_TIMEOUT = 15


def _noop(_mensaje: str) -> None:
    pass


def _match(assets: list[dict], incluye=(), excluye=(), termina: Optional[str] = None) -> Optional[dict]:
    """Devuelve el primer asset cuyo nombre (en minúsculas) contiene todos
    los tokens de `incluye`, ninguno de `excluye`, y (si se indica) termina
    en `termina`. Todos los tokens deben darse ya en minúsculas."""
    for asset in assets:
        nombre = asset.get("name", "").lower()
        if not nombre:
            continue
        if all(tok in nombre for tok in incluye) and not any(tok in nombre for tok in excluye):
            if termina is None or nombre.endswith(termina):
                return asset
    return None


def seleccionar_asset(
    nombre_motor: str,
    sistema: str,
    assets: list[dict],
    fabricante_gpu: Optional[str] = None,
    arch: Optional[str] = None,
) -> dict:
    """Elige el asset de la release adecuado para este motor + sistema
    operativo (+ fabricante de GPU, para kawpowminer). Lanza
    InstaladorError si no hay ninguno válido o si ese sistema no tiene
    build de ese motor.

    `sistema` es lo que devuelve platform.system() ("Windows"/"Linux"/
    "Darwin"). `arch` es lo que devuelve platform.machine() (para elegir
    entre las builds macOS Intel/Apple Silicon de xmrig)."""
    arch = (arch or "").lower()
    es_arm = arch in ("arm64", "aarch64")

    if nombre_motor == "xmrig":
        if sistema == "Windows":
            asset = _match(assets, incluye=("windows",), excluye=("gcc", "arm64"), termina=".zip")
        elif sistema == "Linux":
            asset = _match(assets, incluye=("linux-static",), termina=".tar.gz")
        elif sistema == "Darwin":
            if es_arm:
                asset = _match(assets, incluye=("macos-arm64",))
            else:
                asset = _match(assets, incluye=("macos-x64",))
        else:
            asset = None

    elif nombre_motor == "kawpowminer":
        if sistema == "Darwin":
            raise InstaladorError(
                "kawpowminer no tiene una versión para macOS. Instálalo a mano "
                "o elige una moneda de GPU que use otro motor."
            )
        variante = "cuda11" if (fabricante_gpu or "").upper() == "NVIDIA" else "opencl"
        if sistema == "Windows":
            asset = _match(assets, incluye=("windows", variante), termina=".zip")
        elif sistema == "Linux":
            asset = _match(assets, incluye=("ubuntu20", variante), excluye=("ubuntu18",), termina=".tar.gz")
        else:
            asset = None

    elif nombre_motor == "lolminer":
        if sistema == "Darwin":
            raise InstaladorError(
                "lolMiner no tiene una versión para macOS. Instálalo a mano "
                "o elige una moneda de GPU que use otro motor."
            )
        if sistema == "Windows":
            asset = _match(assets, incluye=("win64",), excluye=("cln",), termina=".zip")
        elif sistema == "Linux":
            asset = _match(assets, incluye=("lin64",), termina=".tar.gz")
        else:
            asset = None

    else:
        raise InstaladorError(f"No sé descargar el motor '{nombre_motor}'.")

    if asset is None:
        raise InstaladorError(
            f"No encontré un archivo de descarga de '{nombre_motor}' para tu "
            f"sistema ({sistema or 'desconocido'}). Puede que no haya una "
            f"versión para tu sistema operativo; instálalo a mano."
        )
    return asset


def _obtener_release(repo: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    # La API de GitHub exige una cabecera User-Agent; sin ella responde 403.
    peticion = urllib.request.Request(
        url,
        headers={"User-Agent": _USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(peticion, timeout=_TIMEOUT, context=red.contexto_https()) as respuesta:
            return json.load(respuesta)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        raise InstaladorError(
            f"No pude consultar la última versión de {repo} en GitHub "
            f"(¿sin conexión a internet?). Detalle: {e}"
        )


def _descargar(url: str, destino: Path) -> None:
    peticion = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(peticion, timeout=_TIMEOUT, context=red.contexto_https()) as respuesta, open(destino, "wb") as f:
            shutil.copyfileobj(respuesta, f)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise InstaladorError(f"Falló la descarga desde {url}. Detalle: {e}")


def _extraer(archivo: Path, destino: Path) -> None:
    nombre = archivo.name.lower()
    destino.mkdir(parents=True, exist_ok=True)
    try:
        if nombre.endswith(".zip"):
            with zipfile.ZipFile(archivo) as z:
                z.extractall(destino)
        elif nombre.endswith(".tar.gz") or nombre.endswith(".tgz"):
            with tarfile.open(archivo, "r:gz") as t:
                # A partir de Python 3.12 se puede filtrar la extracción por
                # seguridad; en versiones anteriores ese argumento no existe.
                if sys.version_info >= (3, 12):
                    t.extractall(destino, filter="data")
                else:
                    t.extractall(destino)
        else:
            raise InstaladorError(f"No sé descomprimir el archivo '{archivo.name}'.")
    except (zipfile.BadZipFile, tarfile.TarError, OSError) as e:
        raise InstaladorError(f"No pude descomprimir '{archivo.name}'. Detalle: {e}")


def _buscar_binario_extraido(carpeta: Path, nombres: list[str]) -> Optional[Path]:
    """Busca (recursivo) dentro del árbol descomprimido el ejecutable cuyo
    nombre esté en la lista de nombres posibles del motor."""
    nombres_set = set(nombres)
    for p in carpeta.rglob("*"):
        if p.is_file() and p.name in nombres_set:
            return p
    return None


def asegurar_motor(
    nombre_motor: str,
    raiz_proyecto: Path,
    fabricante_gpu: Optional[str] = None,
    on_progreso: Optional[Callable[[str], None]] = None,
) -> str:
    """Devuelve la ruta al ejecutable del motor, descargándolo e
    instalándolo si hace falta. Lanza InstaladorError con un mensaje claro
    en español si no se puede (sin red, sin build para tu sistema, etc.)."""
    avisar = on_progreso or _noop
    raiz_proyecto = Path(raiz_proyecto)

    # (1) Si ya está instalado, no descargamos nada.
    ya = motores.encontrar_motor(nombre_motor, raiz_proyecto)
    if ya:
        avisar(f"{nombre_motor} ya está instalado")
        return ya

    if nombre_motor not in _REPOS:
        raise InstaladorError(f"No sé descargar el motor '{nombre_motor}'.")

    # (2) Resolvemos sistema y arquitectura.
    sistema = platform.system()
    arch = platform.machine()
    repo = _REPOS[nombre_motor]

    # Fallo rápido: motores sin build para macOS. Así no gastamos una
    # llamada de red inútil antes de avisar.
    if sistema == "Darwin" and nombre_motor in ("kawpowminer", "lolminer"):
        raise InstaladorError(
            f"{nombre_motor} no tiene una versión para macOS. Instálalo a mano "
            f"o elige una moneda de GPU que use otro motor."
        )

    # (3) Consultamos la última release y (4) elegimos el asset correcto.
    avisar(f"Buscando la última versión de {nombre_motor}...")
    release = _obtener_release(repo)
    version = release.get("tag_name") or release.get("name") or "desconocida"
    assets = release.get("assets") or []
    asset = seleccionar_asset(nombre_motor, sistema, assets, fabricante_gpu, arch)

    url = asset.get("browser_download_url")
    if not url:
        raise InstaladorError(f"El archivo de {nombre_motor} en GitHub no tiene enlace de descarga.")

    # (5) Descargamos a un temporal dentro de bin/_descargas/.
    dir_descargas = raiz_proyecto / "bin" / "_descargas"
    dir_descargas.mkdir(parents=True, exist_ok=True)
    archivo_descargado = dir_descargas / asset["name"]
    avisar(f"Descargando {nombre_motor} {version}...")
    _descargar(url, archivo_descargado)

    # (6) Descomprimimos en bin/{nombre_motor}/.
    avisar(f"Descomprimiendo {nombre_motor}...")
    dir_extraido = raiz_proyecto / "bin" / nombre_motor
    _extraer(archivo_descargado, dir_extraido)

    # (7) Buscamos el ejecutable y lo copiamos a bin/ (dejamos también la
    #     copia descomprimida). Así motores._buscar_binario lo encuentra.
    nombres_binario = motores.MOTORES[nombre_motor]["nombres_binario"]
    origen = _buscar_binario_extraido(dir_extraido, nombres_binario)
    if origen is None:
        raise InstaladorError(
            f"Descargué {nombre_motor} pero no encontré el ejecutable "
            f"({', '.join(nombres_binario)}) dentro del archivo."
        )

    destino = raiz_proyecto / "bin" / origen.name
    shutil.copy2(origen, destino)

    # En Linux/macOS hay que darle permiso de ejecución.
    if os.name != "nt":
        modo = destino.stat().st_mode
        destino.chmod(modo | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    avisar("Listo")
    return str(destino)
