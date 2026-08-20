"""
Catálogo de criptomonedas minables con CPU y con GPU.

Investigado el 2026-08-20 (ver docs/DECISIONS.md para las fuentes y para
la explicación de por qué la lista de CPU tiene menos de 15 monedas: hoy
en día casi no quedan monedas viables para minar solo con el procesador,
así que se listan las que de verdad tienen sentido en vez de rellenar con
monedas poco fiables.

Cada moneda incluye:
- algoritmo: el algoritmo de minado que usa.
- tipo: "cpu" o "gpu" (hardware para el que tiene sentido técnico).
- vram_min_gb: solo para GPU. Memoria de vídeo aproximada necesaria.
  Es orientativo: en varios algoritmos este requisito sube poco a poco
  con el tiempo (crece un "libro de datos" llamado DAG).
- motor: el programa externo que haría el minado de verdad.
- soportado_por_minar_hoy: si `src/minar.py` ya sabe arrancar esta moneda
  hoy. Hoy: Monero, Wownero, Zephyr, Salvium y Raptoreum (las 5 que usan
  xmrig, ya sea con RandomX o con GhostRider). Las de otros
  algoritmos necesitarían instalar y controlar otro programa de minado,
  lo cual es un paso futuro a propósito, no de esta primera versión.
- orden_respaldo: posición en un ranking de ingresos aproximado, por si
  no hay conexión a internet para consultar datos en vivo (cuanto más
  bajo el número, mejor posición tenía el 2026-08-20).
- riesgo: nota opcional si es una moneda pequeña/poco líquida.
"""

MONEDAS_CPU = {
    "XMR": {
        "nombre": "Monero",
        "algoritmo": "RandomX",
        "tipo": "cpu",
        "motor": "xmrig",
        "soportado_por_minar_hoy": True,
        "orden_respaldo": 1,
    },
    "WOW": {
        "nombre": "Wownero",
        "algoritmo": "RandomX (variante rx/wow)",
        "tipo": "cpu",
        "motor": "xmrig",
        "soportado_por_minar_hoy": True,
        "orden_respaldo": 4,
    },
    "ZEPH": {
        "nombre": "Zephyr Protocol",
        "algoritmo": "RandomX (fork)",
        "tipo": "cpu",
        "motor": "xmrig",
        "soportado_por_minar_hoy": True,
        "orden_respaldo": 3,
    },
    "SAL": {
        "nombre": "Salvium",
        "algoritmo": "RandomX (fork)",
        "tipo": "cpu",
        "motor": "xmrig",
        "soportado_por_minar_hoy": True,
        "orden_respaldo": 5,
    },
    "TALE": {
        "nombre": "Talecoin",
        "algoritmo": "RandomX (fork)",
        "tipo": "cpu",
        "motor": "xmrig",
        "soportado_por_minar_hoy": False,
        "orden_respaldo": 8,
        "riesgo": "Moneda muy pequeña, con poca liquidez.",
    },
    "RTM": {
        "nombre": "Raptoreum",
        "algoritmo": "GhostRider",
        "tipo": "cpu",
        "motor": "xmrig (soporte GhostRider)",
        "soportado_por_minar_hoy": True,
        "orden_respaldo": 2,
    },
    "DERO": {
        "nombre": "Dero",
        "algoritmo": "AstroBWT v3",
        "tipo": "cpu",
        "motor": "dero-miner",
        "soportado_por_minar_hoy": False,
        "orden_respaldo": 6,
    },
    "VRSC": {
        "nombre": "Verus Coin",
        "algoritmo": "VerusHash 2.2",
        "tipo": "cpu",
        "motor": "verusminer / ccminer",
        "soportado_por_minar_hoy": False,
        "orden_respaldo": 7,
    },
    "XEL": {
        "nombre": "Xelis",
        "algoritmo": "XelisHash",
        "tipo": "cpu",
        "motor": "xelis-miner",
        "soportado_por_minar_hoy": False,
        "orden_respaldo": 9,
        "riesgo": "También se puede minar con GPU; moneda joven.",
    },
}

MONEDAS_GPU = {
    "KAS": {"nombre": "Kaspa", "algoritmo": "kHeavyHash", "vram_min_gb": 2, "motor": "bzminer / lolMiner", "orden_respaldo": 1},
    "RVN": {"nombre": "Ravencoin", "algoritmo": "KawPow", "vram_min_gb": 4, "motor": "T-Rex / gminer", "orden_respaldo": 3},
    "ERG": {"nombre": "Ergo", "algoritmo": "Autolykos2", "vram_min_gb": 6, "motor": "lolMiner / T-Rex", "orden_respaldo": 4},
    "ETC": {"nombre": "Ethereum Classic", "algoritmo": "Etchash", "vram_min_gb": 6, "motor": "T-Rex / gminer", "orden_respaldo": 5},
    "FLUX": {"nombre": "Flux", "algoritmo": "ZelHash (Equihash 125,4)", "vram_min_gb": 4, "motor": "miniZ / lolMiner", "orden_respaldo": 8},
    "ZEC": {"nombre": "Zcash", "algoritmo": "Equihash (200,9)", "vram_min_gb": 2, "motor": "miniZ / lolMiner", "orden_respaldo": 9},
    "BTG": {"nombre": "Bitcoin Gold", "algoritmo": "Equihash (144,5)", "vram_min_gb": 4, "motor": "miniZ / lolMiner", "orden_respaldo": 11},
    "BEAM": {"nombre": "Beam", "algoritmo": "BeamHash III", "vram_min_gb": 4, "motor": "lolMiner / gminer", "orden_respaldo": 10},
    "FIRO": {"nombre": "Firo", "algoritmo": "FiroPow", "vram_min_gb": 5, "motor": "T-Rex / gminer", "orden_respaldo": 7},
    "CFX": {"nombre": "Conflux", "algoritmo": "Octopus", "vram_min_gb": 6, "motor": "lolMiner / gminer", "orden_respaldo": 6},
    "ALPH": {"nombre": "Alephium", "algoritmo": "Blake3", "vram_min_gb": 2, "motor": "bzminer / lolMiner", "orden_respaldo": 2},
    "ZANO": {"nombre": "Zano", "algoritmo": "ProgPowZ", "vram_min_gb": 4, "motor": "gminer", "orden_respaldo": 12},
    "NEXA": {"nombre": "Nexa", "algoritmo": "NexaPow", "vram_min_gb": 2, "motor": "bzminer", "orden_respaldo": 13},
    "RXD": {"nombre": "Radiant", "algoritmo": "SHA512256d", "vram_min_gb": 2, "motor": "bzminer", "orden_respaldo": 14},
    "NEOX": {
        "nombre": "Neoxa", "algoritmo": "KawPow", "vram_min_gb": 4, "motor": "T-Rex / gminer",
        "orden_respaldo": 15, "riesgo": "Moneda pequeña, con poca liquidez.",
    },
}

for _clave, _datos in MONEDAS_GPU.items():
    _datos.setdefault("tipo", "gpu")
    _datos.setdefault("soportado_por_minar_hoy", False)

TODAS_LAS_MONEDAS = {**MONEDAS_CPU, **MONEDAS_GPU}
