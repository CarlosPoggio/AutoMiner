"""
Escribe el fichero config.md a partir de lo elegido en el formulario, con
el mismo formato de líneas 'clave: valor' que ya entiende src/minar.py.
"""

from pathlib import Path

from monedas import TODAS_LAS_MONEDAS


def guardar_config(ruta: Path, wallet: str, simbolo: str, fecha: str) -> None:
    datos = TODAS_LAS_MONEDAS[simbolo]

    if not datos["soportado_por_minar_hoy"]:
        aviso = (
            "# Aviso: src/minar.py todavía no sabe arrancar esta moneda de forma\n"
            "# automática (le falta el programa de minado adecuado). El fichero es\n"
            "# válido igualmente; pide que se añada soporte cuando quieras usarla.\n"
        )
    elif datos["tipo"] == "gpu":
        aviso = (
            "# Aviso: el comando para esta moneda está implementado y probado con\n"
            "# un ejecutable de prueba, pero nunca contra una tarjeta gráfica real\n"
            "# (se desarrolló en un entorno sin GPU). Pruébalo y, si algo falla,\n"
            "# dilo para ajustarlo.\n"
        )
    else:
        aviso = ""

    contenido = (
        f"# Generado por el formulario (src/formulario.py) el {fecha}\n"
        f"# Moneda elegida: {datos['nombre']} ({simbolo}) — algoritmo {datos['algoritmo']} "
        f"— tipo {datos['tipo'].upper()}\n"
        f"{aviso}"
        f"wallet: {wallet}\n"
        f"moneda: {simbolo}\n"
    )
    ruta.write_text(contenido, encoding="utf-8")
