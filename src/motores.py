"""
Registro de "motores" de minado (los programas externos que hacen el
trabajo real). Cada moneda de MONEDAS_SOPORTADAS (en minar.py) indica
qué motor usa; este fichero sabe cómo encontrar el ejecutable de cada
motor y cómo construir el comando exacto para arrancarlo.

Añadir una moneda nueva que use un motor YA registrado aquí es sencillo:
solo hace falta añadir su entrada en minar.py. Añadir una moneda que
necesite un motor distinto implica añadir ese motor aquí primero.
"""

import shutil
from pathlib import Path


def _buscar_binario(nombres: list[str], raiz_proyecto: Path) -> str | None:
    """Busca el ejecutable en el PATH del sistema o en bin/, probando
    varios nombres posibles (con y sin .exe)."""
    for nombre in nombres:
        en_path = shutil.which(nombre)
        if en_path:
            return en_path
    for nombre in nombres:
        candidato = raiz_proyecto / "bin" / nombre
        if candidato.exists():
            return str(candidato)
    return None


def _cmd_xmrig(bin_path: str, wallet: str, pool: str, algo: str, datos: dict) -> list[str]:
    cmd = [bin_path, "-o", pool, "-u", wallet, "-p", "x", "--algo", algo]
    hilos = datos.get("hilos") or datos.get("threads")
    if hilos:
        cmd += ["-t", str(hilos)]
    # XMRig reserva, por defecto, un 1% del tiempo de minado para su propio
    # desarrollador ("--donate-level", 1 de cada 100 minutos). Se puede
    # ajustar añadiendo una línea "donate_level: N" en config.md.
    nivel_donacion = datos.get("donate_level")
    if nivel_donacion is not None:
        cmd += ["--donate-level", str(nivel_donacion)]
    return cmd


def _cmd_kawpowminer(bin_path: str, wallet: str, pool: str, algo: str, datos: dict) -> list[str]:
    worker = datos.get("worker", "rig1")
    return [bin_path, "-P", f"stratum+tcp://{wallet}.{worker}@{pool}"]


def _cmd_lolminer(bin_path: str, wallet: str, pool: str, algo: str, datos: dict) -> list[str]:
    worker = datos.get("worker", "rig1")
    return [bin_path, "--algo", algo, "--pool", pool, "--user", f"{wallet}.{worker}"]


MOTORES = {
    "xmrig": {
        "nombres_binario": ["xmrig", "xmrig.exe"],
        "construir_comando": _cmd_xmrig,
        # Comisión por defecto (--donate-level 1 = 1%). Es código abierto y
        # tú puedes cambiarla en config.md con "donate_level: N".
        "comision_pct": 1.0,
        "codigo_abierto": True,
    },
    "kawpowminer": {
        "nombres_binario": ["kawpowminer", "kawpowminer.exe"],
        "construir_comando": _cmd_kawpowminer,
        "comision_pct": 0.0,
        "codigo_abierto": True,
    },
    "lolminer": {
        "nombres_binario": ["lolMiner", "lolMiner.exe"],
        "construir_comando": _cmd_lolminer,
        "comision_pct": 0.75,
        "codigo_abierto": False,
    },
}


def encontrar_motor(nombre_motor: str, raiz_proyecto: Path) -> str | None:
    info = MOTORES.get(nombre_motor)
    if info is None:
        return None
    return _buscar_binario(info["nombres_binario"], raiz_proyecto)


def construir_comando(nombre_motor: str, bin_path: str, wallet: str, pool: str, algo: str, datos: dict) -> list[str]:
    return MOTORES[nombre_motor]["construir_comando"](bin_path, wallet, pool, algo, datos)
