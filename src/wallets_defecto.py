"""
Lee `wallets.md`: tus wallets por defecto, una por moneda, para que el
formulario rellene el campo de wallet solo al elegir esa moneda.

A diferencia de `config.md`, este fichero SÍ se sube a git (ver
docs/DECISIONS.md): una dirección de wallet es la que RECIBE el dinero
minado, así que es pública por diseño (cualquiera puede verla en la
cadena de bloques en cuanto llega un pago). Lo que nunca debe ir aquí
(ni en ningún fichero de este repositorio) es una clave privada o una
frase semilla, eso sí es secreto.
"""

from pathlib import Path


def cargar_wallets_por_defecto(ruta: Path) -> dict[str, str]:
    """
    Devuelve {simbolo: wallet} a partir de líneas 'SIMBOLO: direccion' en
    `ruta`. Si el fichero no existe, o una moneda no aparece en él,
    simplemente no está en el diccionario devuelto (el campo se queda
    vacío en el formulario).
    """
    if not ruta.exists():
        return {}

    wallets = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if ":" not in linea:
            continue
        simbolo, wallet = linea.split(":", 1)
        simbolo = simbolo.strip().upper()
        wallet = wallet.strip()
        if simbolo and wallet:
            wallets[simbolo] = wallet
    return wallets
