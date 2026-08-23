"""
Escribe el fichero config.md a partir de lo elegido en el formulario, con
el mismo formato de líneas 'clave: valor' que ya entiende src/minar.py.

Formato nuevo (dual): un bloque para la CPU y otro para la GPU, cada uno
opcional pero con al menos uno presente:

    cpu_moneda: XMR
    cpu_wallet: ...
    gpu_moneda: RVN
    gpu_wallet: ...
"""

from pathlib import Path

from monedas import TODAS_LAS_MONEDAS


def _aviso(simbolo: str) -> str:
    datos = TODAS_LAS_MONEDAS[simbolo]
    if not datos["soportado_por_minar_hoy"]:
        return (
            "# Aviso: src/minar.py todavía no sabe arrancar esta moneda de forma\n"
            "# automática (le falta el programa de minado adecuado). El fichero es\n"
            "# válido igualmente; pide que se añada soporte cuando quieras usarla.\n"
        )
    if datos["tipo"] == "gpu":
        return (
            "# Aviso: el comando para esta moneda está implementado y probado con\n"
            "# un ejecutable de prueba, pero nunca contra una tarjeta gráfica real\n"
            "# (se desarrolló en un entorno sin GPU). Pruébalo y, si algo falla,\n"
            "# dilo para ajustarlo.\n"
        )
    return ""


def _bloque(prefijo: str, simbolo: str, wallet: str) -> str:
    datos = TODAS_LAS_MONEDAS[simbolo]
    return (
        f"# {prefijo.upper()}: {datos['nombre']} ({simbolo}) — "
        f"algoritmo {datos['algoritmo']} — tipo {datos['tipo'].upper()}\n"
        f"{_aviso(simbolo)}"
        f"{prefijo}_moneda: {simbolo}\n"
        f"{prefijo}_wallet: {wallet}\n"
    )


def guardar_config(ruta: Path, fecha: str, cpu: dict | None, gpu: dict | None) -> None:
    """
    Escribe config.md con hasta dos bloques (CPU y/o GPU).

    `cpu` y `gpu` son None (ese componente no se usa) o un diccionario
    {"simbolo": "XMR", "wallet": "..."}. Si ambos son None, lanza
    ValueError (no debería llamarse así nunca desde la interfaz).
    """
    if cpu is None and gpu is None:
        raise ValueError(
            "Hay que indicar al menos un bloque (CPU o GPU) para generar config.md."
        )

    partes = [
        f"# Generado por el formulario (src/formulario.py) el {fecha}\n",
        "# Se recomienda generar este fichero con: python3 src/formulario.py\n",
    ]
    if cpu is not None:
        partes.append(_bloque("cpu", cpu["simbolo"], cpu["wallet"]))
    if gpu is not None:
        partes.append(_bloque("gpu", gpu["simbolo"], gpu["wallet"]))

    ruta.write_text("".join(partes), encoding="utf-8")
