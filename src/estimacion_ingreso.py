"""
Estimación de ingreso de referencia por moneda.

Idea en palabras simples: para la moneda elegida en el formulario, damos
una idea de cuánto se ganaría por hora. NO medimos el hardware real del
usuario: calculamos cuánto rendiría una velocidad de minado FIJA y
redonda (una "referencia"), distinta según el algoritmo, para que se
pueda comparar una moneda con otra y hacerse una idea de escala. Si tu
tarjeta rinde el doble que la referencia, multiplica por dos.

Fórmula estándar de minería, válida para cualquier moneda cuya
"dificultad" esté en número real de hashes esperados por bloque (es el
caso de las monedas tipo CryptoNote como Monero/Salvium/Zephyr y de
KawPow como Ravencoin):

    moneda_por_hora = hashrate_referencia * recompensa_bloque * 3600 / dificultad

En esa forma el tiempo de bloque se cancela y NO hace falta convertir
dificultad→hashrate (una conversión que es distinta y delicada en cada
algoritmo). Cuando la fuente nos da directamente el "hashrate de red" ya
calculado (Ravencoin vía 2miners, Kaspa vía api.kaspa.org), usamos la
forma equivalente con hashrate y tiempo de bloque, para no arriesgar esa
conversión nosotros.

El precio en dólares sale de CoinGecko (gratis, sin registro), cacheado
unos minutos en memoria para no golpear su API en cada cambio de menú.

Monedas SIN estimación a día de hoy (devuelven None a propósito, nunca un
número inventado; ver el informe de la sesión que añadió este módulo):
- WOW (Wownero): no cotiza en CoinGecko (el id "wow-2" es otra moneda
  distinta, un token meme en Base), así que no hay precio fiable.
- RTM (Raptoreum): no se encontró una API pública, gratuita y verificable
  con dificultad/recompensa en vivo.

ALPH (Alephium) SÍ tiene estimación desde el 2026-08-24: el pool HeroMiners
que ya usamos por defecto (alephium.herominers.com) da la dificultad de
red y la recompensa por bloque en vivo, y CoinGecko sí tiene su precio
(id "alephium", verificado que es la moneda correcta y no otro token con
el mismo símbolo). La fórmula de dificultad→hashrate se contrastó contra
los pagos diarios reales del pool antes de usarla, no se dio por buena a
ciegas (ver docs/DECISIONS.md). A diferencia de xmr/sal/zeph, el formato
de bloque de este pool para ALPH no se puede parsear con el mismo
ayudante genérico (_reward_de_bloques_herominers): trae un campo
hexadecimal extra que a veces "parece" una dirección y confundiría al
parser; en su lugar se busca el campo que de verdad tiene forma de
dirección real de Alephium (misma regex que src/minar.py). El campo
pool.stats.averageReward, que en teoría daría la recompensa ya calculada
sin parsear nada, se descartó por no ser fiable: en pruebas reales viene
vacío (null) parte del tiempo.

IRON (Iron Fish), ERG (Ergo) y BEAM (Beam) tienen estimación desde el
2026-08-24: las tres se investigaron como candidatas de mejor ingreso
real que RVN/KAS/ALPH (ver docs/DECISIONS.md), y las tres tienen pool
HeroMiners con dificultad de red en vivo y precio verificado en
CoinGecko ("iron-fish", "ergo", "beam-2"). A diferencia de ALPH, sus
bloques SÍ se pueden parsear con el ayudante genérico
(_reward_de_bloques_herominers): no traen ningún campo extra que se
confunda con la dirección del minero (comprobado bloque a bloque antes
de usarlo, no asumido).

Todo usa solo la librería estándar (urllib, json, re), sin dependencias.
"""

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

import red

TIMEOUT_SEGUNDOS = 8
_UA = "autominer-estimacion/1.0"

# Cuánto vale, para cada moneda, la velocidad de minado de referencia:
# (hashes_por_segundo, texto_para_mostrar). Cifras redondas y fáciles de
# razonar, adecuadas al orden de magnitud típico de cada algoritmo.
REFERENCIA_HASHRATE = {
    "XMR": (1000.0, "1 kH/s"),   # RandomX (rx/0)
    "SAL": (1000.0, "1 kH/s"),   # RandomX (rx/0)
    "ZEPH": (1000.0, "1 kH/s"),  # RandomX (rx/0)
    "RVN": (1e7, "10 MH/s"),     # KawPow
    "KAS": (1e9, "1 GH/s"),      # kHeavyHash
    "ALPH": (1e9, "1 GH/s"),     # Blake3 — orden de magnitud real, visto en GPU
    "IRON": (1e7, "10 MH/s"),    # FishHash — parecido en orden de magnitud a KawPow
    "ERG": (1e8, "100 MH/s"),    # Autolykos2 — algoritmo rápido, orden de magnitud mayor
    "BEAM": (30.0, "30 Sol/s"),  # BeamHash III (familia Equihash) — se mide en soluciones/s, no en H/s
}

# ids de CoinGecko (verificados en vivo). Solo los de monedas que sí
# estimamos; Wownero no está en CoinGecko a propósito (ver cabecera).
COINGECKO_IDS = {
    "XMR": "monero",
    "SAL": "salvium",
    "ZEPH": "zephyr-protocol",
    "RVN": "ravencoin",
    "KAS": "kaspa",
    "ALPH": "alephium",
    "IRON": "iron-fish",
    "ERG": "ergo",
    "BEAM": "beam-2",
}
URL_COINGECKO = "https://api.coingecko.com/api/v3/simple/price"

# Kaspa produce 10 bloques por segundo desde el hardfork "Crescendo"
# (mayo 2025). Es una constante del protocolo, corroborada por el tamaño
# de la recompensa por bloque que devuelve su propia API.
KAS_BLOQUES_POR_SEGUNDO = 10


@dataclass
class EstimacionReferencia:
    simbolo: str
    hashrate_referencia: str   # ej. "1 kH/s" — velocidad fija usada para normalizar
    moneda_por_hora: float     # moneda ganada en 1 hora a esa velocidad de referencia
    usd_por_hora: float        # lo mismo en dólares, al precio actual
    fuente: str                # de dónde salió el dato (para depurar/auditar)


# --------------------------------------------------------------------------
# Utilidades de red (todo pasa por aquí para poder mockear en los tests)
# --------------------------------------------------------------------------

def _http_json(url: str):
    peticion = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(peticion, timeout=TIMEOUT_SEGUNDOS, context=red.contexto_https()) as respuesta:
        return json.load(respuesta)


# --------------------------------------------------------------------------
# Precios (CoinGecko) con caché en memoria
# --------------------------------------------------------------------------

_cache_precios = {"ts": 0.0, "datos": {}}
_TTL_PRECIOS_SEG = 300


def _precios_usd() -> dict:
    """Devuelve {simbolo: precio_usd} para las monedas con id de CoinGecko.
    Cacheado unos minutos. Devuelve {} si no se pudo consultar."""
    ahora = time.time()
    if _cache_precios["datos"] and (ahora - _cache_precios["ts"] < _TTL_PRECIOS_SEG):
        return _cache_precios["datos"]

    ids = ",".join(COINGECKO_IDS.values())
    url = f"{URL_COINGECKO}?ids={ids}&vs_currencies=usd"
    try:
        datos = _http_json(url)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return _cache_precios["datos"]  # lo último que se pudo cachear, o {}

    precios = {}
    for simbolo, cg_id in COINGECKO_IDS.items():
        try:
            precios[simbolo] = float(datos[cg_id]["usd"])
        except (KeyError, TypeError, ValueError):
            continue
    if precios:
        _cache_precios["ts"] = ahora
        _cache_precios["datos"] = precios
    return precios


# --------------------------------------------------------------------------
# Fuentes de dificultad / hashrate / recompensa por moneda
# Cada fetcher devuelve (moneda_por_hora, fuente_str) o lanza/─devuelve None.
# --------------------------------------------------------------------------

def _reward_de_bloques_herominers(bloques, coin_units: int):
    """En las APIs tipo HeroMiners, cada bloque es una cadena separada por
    ':' donde la recompensa (en unidades atómicas) es el campo justo antes
    de la dirección del minero (el único token largo tipo dirección).
    Devuelve la recompensa del primer bloque válido, en unidades de moneda."""
    for entrada in bloques:
        if not isinstance(entrada, str):
            continue
        partes = entrada.split(":")
        for i, p in enumerate(partes):
            if len(p) > 40 and p.isalnum() and i > 0:
                try:
                    atomicas = int(partes[i - 1])
                except ValueError:
                    break
                if atomicas > 0:
                    return atomicas / coin_units
                break
    return None


def _fetch_cryptonote_herominers(host: str):
    """XMR-like (CryptoNote) vía un pool HeroMiners: dificultad + recompensa.
    hashrate_ref * recompensa * 3600 / dificultad."""
    datos = _http_json(f"https://{host}/api/stats")
    dif = float(datos["network"]["difficulty"])
    coin_units = int(datos["config"]["coinUnits"])
    recompensa = _reward_de_bloques_herominers(datos.get("pool", {}).get("blocks", []), coin_units)
    if not dif or recompensa is None:
        return None
    return dif, recompensa, f"herominers ({host})"


def _fetch_xmr():
    """Monero vía supportxmr (el pool por defecto de XMR en minar.py)."""
    datos = _http_json("https://www.supportxmr.com/api/network/stats")
    dif = float(datos["difficulty"])
    recompensa = float(datos["value"]) / 1e12  # XMR tiene 12 decimales
    if not dif or not recompensa:
        return None
    return dif, recompensa, "supportxmr.com/api/network/stats"


def _fetch_sal():
    return _fetch_cryptonote_herominers("salvium.herominers.com")


def _fetch_zeph():
    return _fetch_cryptonote_herominers("zephyr.herominers.com")


# Regex de una dirección real de Alephium (misma que
# minar.MONEDAS_SOPORTADAS["ALPH"]["wallet_regex"], repetida aquí para no
# depender de minar.py desde este módulo). Los bloques de
# alephium.herominers.com traen un campo hexadecimal extra (lleno de
# ceros) que el parser genérico de HeroMiners confundiría con una
# dirección; una dirección real de Alephium nunca contiene "0", así que
# esta regex sí distingue bien los dos casos.
_RE_DIRECCION_ALPH = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{44,58}$")


def _reward_alph_de_bloques(bloques, coin_units: int):
    """Como _reward_de_bloques_herominers, pero buscando específicamente
    un campo con forma de dirección real de Alephium en vez de "cualquier
    token largo alfanumérico" — ver _RE_DIRECCION_ALPH."""
    for entrada in bloques:
        if not isinstance(entrada, str):
            continue
        partes = entrada.split(":")
        for i, p in enumerate(partes):
            if i > 0 and _RE_DIRECCION_ALPH.match(p):
                try:
                    atomicas = int(partes[i - 1])
                except ValueError:
                    break
                if atomicas > 0:
                    return atomicas / coin_units
                break
    return None


def _fetch_alph():
    """Alephium (Blake3) vía el pool HeroMiners que ya usamos por defecto
    (alephium.herominers.com): dificultad de red y recompensa por bloque,
    las dos en vivo. pool.stats.averageReward (la recompensa ya calculada
    por el propio pool, sin parsear nada) se probó primero pero resultó
    no ser fiable — en pruebas reales viene vacía parte del tiempo — así
    que se usa _reward_alph_de_bloques en su lugar."""
    datos = _http_json("https://alephium.herominers.com/api/stats")
    dif = float(datos["network"]["difficulty"])
    coin_units = int(datos["config"]["coinUnits"])
    recompensa = _reward_alph_de_bloques(datos.get("pool", {}).get("blocks", []), coin_units)
    if not dif or recompensa is None:
        return None
    return dif, recompensa, "alephium.herominers.com/api/stats"


def _fetch_iron():
    """Iron Fish (FishHash) vía el pool HeroMiners que ya usamos por
    defecto. Bloque verificado a mano antes de usar el parser genérico:
    no trae ningún campo extra que se confunda con la dirección (a
    diferencia de ALPH) — ver docs/DECISIONS.md."""
    return _fetch_cryptonote_herominers("ironfish.herominers.com")


def _fetch_erg():
    """Ergo (Autolykos2) vía el pool HeroMiners que ya usamos por
    defecto. Mismo motivo que Iron Fish: bloque verificado, el parser
    genérico funciona bien aquí."""
    return _fetch_cryptonote_herominers("ergo.herominers.com")


def _fetch_beam():
    """Beam (BeamHash III) vía el pool HeroMiners que ya usamos por
    defecto. Mismo motivo que Iron Fish/Ergo."""
    return _fetch_cryptonote_herominers("beam.herominers.com")


def _estimacion_por_dificultad(simbolo: str):
    """Para monedas cuya dificultad es 'hashes esperados por bloque'
    (CryptoNote y, verificado, también Alephium/Blake3, Iron Fish/FishHash,
    Ergo/Autolykos2 y Beam/BeamHash III — ver docs/DECISIONS.md):
    moneda/hora = ref * recompensa * 3600 / dificultad."""
    fetch = {
        "XMR": _fetch_xmr, "SAL": _fetch_sal, "ZEPH": _fetch_zeph, "ALPH": _fetch_alph,
        "IRON": _fetch_iron, "ERG": _fetch_erg, "BEAM": _fetch_beam,
    }[simbolo]
    resultado = fetch()
    if resultado is None:
        return None
    dif, recompensa, fuente = resultado
    ref_hr, _ = REFERENCIA_HASHRATE[simbolo]
    moneda_por_hora = ref_hr * recompensa * 3600 / dif
    return moneda_por_hora, fuente


def _estimacion_rvn():
    """Ravencoin (KawPow) vía 2miners: usa el hashrate de red YA calculado
    y el tiempo de bloque en vivo, más la recompensa de un bloque madurado."""
    stats = _http_json("https://rvn.2miners.com/api/stats")
    nodos = stats.get("nodes") or []
    if not nodos:
        return None
    net_hr = float(nodos[0]["networkhashps"])
    tiempo_bloque = float(nodos[0]["avgBlockTime"])
    if not net_hr or not tiempo_bloque:
        return None

    bloques = _http_json("https://rvn.2miners.com/api/blocks")
    recompensa = None
    for b in bloques.get("matured", []):
        if not b.get("orphan"):
            recompensa = float(b["reward"]) / 1e8  # RVN tiene 8 decimales
            break
    if recompensa is None:
        return None

    ref_hr, _ = REFERENCIA_HASHRATE["RVN"]
    bloques_por_hora = 3600 / tiempo_bloque
    moneda_por_hora = (ref_hr / net_hr) * recompensa * bloques_por_hora
    return moneda_por_hora, "rvn.2miners.com/api"


def _estimacion_kas():
    """Kaspa (kHeavyHash) vía api.kaspa.org: hashrate de red YA calculado
    (en TH/s) y recompensa por bloque, ambos en vivo."""
    hr = _http_json("https://api.kaspa.org/info/hashrate?stringOnly=false")
    net_hr = float(hr["hashrate"]) * 1e12  # la API da TH/s
    br = _http_json("https://api.kaspa.org/info/blockreward?stringOnly=false")
    recompensa = float(br["blockreward"])  # ya viene en KAS
    if not net_hr or not recompensa:
        return None

    ref_hr, _ = REFERENCIA_HASHRATE["KAS"]
    bloques_por_hora = KAS_BLOQUES_POR_SEGUNDO * 3600
    moneda_por_hora = (ref_hr / net_hr) * recompensa * bloques_por_hora
    return moneda_por_hora, "api.kaspa.org (hashrate+blockreward, 10 bps)"


_ESTIMADORES = {
    "XMR": lambda: _estimacion_por_dificultad("XMR"),
    "SAL": lambda: _estimacion_por_dificultad("SAL"),
    "ZEPH": lambda: _estimacion_por_dificultad("ZEPH"),
    "RVN": _estimacion_rvn,
    "KAS": _estimacion_kas,
    "ALPH": lambda: _estimacion_por_dificultad("ALPH"),
    "IRON": lambda: _estimacion_por_dificultad("IRON"),
    "ERG": lambda: _estimacion_por_dificultad("ERG"),
    "BEAM": lambda: _estimacion_por_dificultad("BEAM"),
}


# --------------------------------------------------------------------------
# API pública
# --------------------------------------------------------------------------

def estimar_referencia(simbolo: str) -> "EstimacionReferencia | None":
    """
    Devuelve una estimación de referencia (NO es el hardware real del
    usuario, es un cálculo normalizado a una velocidad de minado fija y
    razonable para ese algoritmo, para dar una idea de escala). Devuelve
    None si no se pudo obtener un dato fiable ahora mismo (sin conexión,
    fuente caída, o moneda sin fuente verificada).
    """
    if simbolo is None:
        return None
    simbolo = simbolo.strip().upper()

    estimador = _ESTIMADORES.get(simbolo)
    if estimador is None:
        return None  # moneda sin fuente verificada (WOW, RTM)

    try:
        resultado = estimador()
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError,
            KeyError, ValueError, TypeError, IndexError):
        return None
    if resultado is None:
        return None
    moneda_por_hora, fuente = resultado

    precio = _precios_usd().get(simbolo)
    if precio is None:
        return None

    _, texto_ref = REFERENCIA_HASHRATE[simbolo]
    return EstimacionReferencia(
        simbolo=simbolo,
        hashrate_referencia=texto_ref,
        moneda_por_hora=moneda_por_hora,
        usd_por_hora=moneda_por_hora * precio,
        fuente=fuente,
    )


def escalar_a_hashrate(estimacion: "EstimacionReferencia", hashrate_real_hz: float) -> tuple[float, float]:
    """
    Reescala una EstimacionReferencia (calculada para la velocidad fija de
    REFERENCIA_HASHRATE) a un hashrate real medido, en hercios. No hace
    ninguna consulta de red: la proporción es aritmética local, así que se
    puede llamar en cada línea de log nueva sin golpear ninguna API.
    Devuelve (moneda_por_hora, usd_por_hora) para ese hashrate real.
    """
    ref_hz, _ = REFERENCIA_HASHRATE[estimacion.simbolo]
    factor = hashrate_real_hz / ref_hz
    return estimacion.moneda_por_hora * factor, estimacion.usd_por_hora * factor
