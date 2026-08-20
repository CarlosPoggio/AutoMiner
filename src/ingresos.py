"""
Consulta de ingresos aproximados por moneda, para poder recomendar "la de
mayor ingreso" entre las opciones técnicamente posibles.

Importante (ver docs/DECISIONS.md): esto es ingreso, no beneficio. No se
tiene en cuenta el coste de la luz porque no lo preguntamos ni lo sabemos.
Y es una comparación aproximada: asume que tu hardware rendiría, en
términos relativos a cada red, de forma parecida en todos los algoritmos
posibles, lo cual no es exactamente así en la práctica.

Se intenta obtener datos en vivo desde whattomine.com (una web pública de
referencia en minería, sin necesidad de clave de acceso). Si no hay
conexión a internet en el momento de ejecutar el formulario, se usa un
ranking aproximado guardado en el propio código (ver monedas.py,
"orden_respaldo"), obtenido durante la investigación del 2026-08-20.
"""

import json
import urllib.error
import urllib.request

URL_WHATTOMINE = "https://whattomine.com/coins.json"
TIMEOUT_SEGUNDOS = 6


def obtener_ingresos_en_vivo() -> dict[str, float] | None:
    """
    Devuelve {simbolo: ingreso_estimado_relativo} usando datos en vivo, o
    None si no se pudo consultar (sin internet, web caída, etc.).
    """
    try:
        peticion = urllib.request.Request(
            URL_WHATTOMINE, headers={"User-Agent": "minero-cripto-formulario/1.0"}
        )
        with urllib.request.urlopen(peticion, timeout=TIMEOUT_SEGUNDOS) as respuesta:
            datos = json.load(respuesta)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None

    monedas = datos.get("coins", datos)  # algunas versiones anidan bajo "coins"
    if not isinstance(monedas, dict):
        return None

    ingresos = {}
    for info in monedas.values():
        if not isinstance(info, dict):
            continue
        simbolo = info.get("tag")
        recompensa = info.get("estimated_rewards")
        precio_btc = info.get("exchange_rate")
        if not simbolo or recompensa is None or precio_btc is None:
            continue
        try:
            ingresos[simbolo.upper()] = float(recompensa) * float(precio_btc)
        except (TypeError, ValueError):
            continue
    return ingresos or None


def clasificar_por_ingreso(simbolos: list[str], catalogo: dict) -> list[str]:
    """
    Ordena una lista de símbolos de moneda de mayor a menor ingreso
    estimado. Usa datos en vivo si están disponibles; si no, usa el orden
    de reserva guardado en el catálogo.
    """
    ingresos_en_vivo = obtener_ingresos_en_vivo()

    if ingresos_en_vivo and any(s in ingresos_en_vivo for s in simbolos):
        return sorted(
            simbolos,
            key=lambda s: ingresos_en_vivo.get(s, float("-inf")),
            reverse=True,
        )

    return sorted(
        simbolos,
        key=lambda s: catalogo.get(s, {}).get("orden_respaldo", 999),
    )
