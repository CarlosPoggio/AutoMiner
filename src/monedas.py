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
- soportado_por_minar_hoy: si `src/minar.py` ya sabe construir el comando
  para arrancar esta moneda. Hoy: Monero, Wownero, Zephyr, Salvium y
  Raptoreum (CPU, motor xmrig) y Ravencoin, Alephium, Iron Fish, Ergo y
  Beam (GPU, motores kawpowminer/lolMiner — ver tabla completa en
  README.md). Kaspa se quitó de aquí el 2026-08-24: lolMiner retiró el
  algoritmo que usaba (ver "riesgo" en su entrada, más abajo, y
  docs/DECISIONS.md). El resto de monedas del catálogo necesitaría
  instalar y controlar otro programa de minado distinto: un paso futuro
  a propósito, no de esta versión.
- comision_pct: comisión aproximada del motor de minado (0 si es
  gratuito de verdad, como xmrig con --donate-level 0 o kawpowminer).
  Solo está rellena para las monedas ya soportadas.
- orden_respaldo: posición en un ranking de ingresos aproximado, por si
  no hay conexión a internet para consultar datos en vivo (cuanto más
  bajo el número, mejor posición). Investigado el 2026-08-20 para el
  catálogo completo; las monedas de GPU ya soportadas se reordenaron el
  2026-08-24 con datos reales de whattomine.com (ver docs/DECISIONS.md,
  entrada 20) — más fiable que el ranking original a ciegas.
- riesgo: nota opcional si es una moneda pequeña/poco líquida, o con
  algún problema real conocido (ver entradas de RVN y KAS más abajo).
- confirmado_en_hardware_real: solo presente (y en True) en las monedas
  de GPU que alguien ya minó de verdad, de principio a fin, contra un
  pool real (leído por `OpcionMoneda.confirmado_en_hardware_real` en
  `recomendador.py`; se ve en el formulario como ✅ en vez de 🧪). Hoy:
  Alephium e Iron Fish. Las de CPU no necesitan esta marca porque ya se
  consideran confirmadas en cuanto están soportadas (se probaron en un
  entorno con procesador real desde el principio del proyecto).

IMPORTANTE sobre las monedas de GPU soportadas pero SIN confirmar
todavía (RVN, ERG, BEAM): el comando que genera minar.py para ellas
está probado (con un ejecutable de prueba o una conexión real de
diagnóstico, ver docs/DECISIONS.md), pero no se ha completado un
minado real de principio a fin con una wallet real. RVN, en concreto,
SÍ se probó a fondo contra dos GPUs NVIDIA reales (RTX 4060 Laptop y
RTX 5060, ambas modernas) y en las dos falla por una limitación del
propio kawpowminer (ver su "riesgo" más abajo y docs/DECISIONS.md,
entradas 17-18) — no es previsible que llegue a confirmarse sin un
motor de minado distinto o una GPU más antigua.
"""

MONEDAS_CPU = {
    "XMR": {
        "nombre": "Monero",
        "algoritmo": "RandomX",
        "tipo": "cpu",
        "motor": "xmrig",
        "soportado_por_minar_hoy": True,
        "comision_pct": 1.0,
        "orden_respaldo": 1,
    },
    "WOW": {
        "nombre": "Wownero",
        "algoritmo": "RandomX (variante rx/wow)",
        "tipo": "cpu",
        "motor": "xmrig",
        "soportado_por_minar_hoy": True,
        "comision_pct": 1.0,
        "orden_respaldo": 4,
    },
    "ZEPH": {
        "nombre": "Zephyr Protocol",
        "algoritmo": "RandomX (fork)",
        "tipo": "cpu",
        "motor": "xmrig",
        "soportado_por_minar_hoy": True,
        "comision_pct": 1.0,
        "orden_respaldo": 3,
    },
    "SAL": {
        "nombre": "Salvium",
        "algoritmo": "RandomX (fork)",
        "tipo": "cpu",
        "motor": "xmrig",
        "soportado_por_minar_hoy": True,
        "comision_pct": 1.0,
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
        "comision_pct": 1.0,
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
    "KAS": {
        "nombre": "Kaspa", "algoritmo": "kHeavyHash", "vram_min_gb": 2, "motor": "lolMiner",
        "soportado_por_minar_hoy": False, "orden_respaldo": 6,
        "riesgo": (
            "Ya no se puede minar con GPU: lolMiner retiró el algoritmo "
            "kHeavyHash de sus versiones recientes (la red de Kaspa está "
            "dominada por ASICs desde 2023-2024). Confirmado con "
            "--list-algos el 2026-08-24; ver docs/DECISIONS.md."
        ),
    },
    "RVN": {
        "nombre": "Ravencoin", "algoritmo": "KawPow", "vram_min_gb": 4, "motor": "kawpowminer",
        "soportado_por_minar_hoy": True, "comision_pct": 0.0, "orden_respaldo": 5,
        "riesgo": (
            "Probado de verdad en dos GPUs NVIDIA distintas (2026-08-24) y "
            "ninguna consigue minar todavía: en una RTX 5060 (Blackwell) "
            "falla al generar el DAG (\"invalid device symbol\"); en una "
            "RTX 4060 Laptop (Ada Lovelace) genera el DAG bien pero "
            "kawpowminer se cierra solo justo al empezar a minar de "
            "verdad (código de salida 0xC0000409). Los dos son fallos del "
            "propio kawpowminer (un binario de terceros con un CUDA "
            "interno anticuado), no de esta app — ver docs/DECISIONS.md."
        ),
    },
    "ERG": {
        "nombre": "Ergo", "algoritmo": "Autolykos2", "vram_min_gb": 6, "motor": "lolMiner",
        "soportado_por_minar_hoy": True, "comision_pct": 1.5, "orden_respaldo": 3,
    },
    "ETC": {"nombre": "Ethereum Classic", "algoritmo": "Etchash", "vram_min_gb": 6, "motor": "T-Rex / gminer", "orden_respaldo": 17},
    "FLUX": {"nombre": "Flux", "algoritmo": "ZelHash (Equihash 125,4)", "vram_min_gb": 4, "motor": "miniZ / lolMiner", "orden_respaldo": 8},
    "ZEC": {"nombre": "Zcash", "algoritmo": "Equihash (200,9)", "vram_min_gb": 2, "motor": "miniZ / lolMiner", "orden_respaldo": 9},
    "BTG": {"nombre": "Bitcoin Gold", "algoritmo": "Equihash (144,5)", "vram_min_gb": 4, "motor": "miniZ / lolMiner", "orden_respaldo": 11},
    "BEAM": {
        "nombre": "Beam", "algoritmo": "BeamHash III", "vram_min_gb": 4, "motor": "lolMiner",
        "soportado_por_minar_hoy": True, "comision_pct": 1.0, "orden_respaldo": 2,
    },
    "FIRO": {"nombre": "Firo", "algoritmo": "FiroPow", "vram_min_gb": 5, "motor": "T-Rex / gminer", "orden_respaldo": 7},
    "CFX": {"nombre": "Conflux", "algoritmo": "Octopus", "vram_min_gb": 6, "motor": "lolMiner / gminer", "orden_respaldo": 16},
    "ALPH": {
        "nombre": "Alephium", "algoritmo": "Blake3", "vram_min_gb": 2, "motor": "lolMiner",
        "soportado_por_minar_hoy": True, "comision_pct": 0.75, "orden_respaldo": 4,
        # Confirmado por Carlos minando de verdad el 2026-08-24 (RTX 4060
        # Laptop): conecta, calcula y envía comparios al pool sin problema.
        # El ingreso real es minúsculo hoy (ver estimacion_ingreso.py y
        # docs/DECISIONS.md) — esto solo confirma que FUNCIONA, no que
        # compense.
        "confirmado_en_hardware_real": True,
    },
    "IRON": {
        "nombre": "Iron Fish", "algoritmo": "FishHash", "vram_min_gb": 4, "motor": "lolMiner",
        "soportado_por_minar_hoy": True, "comision_pct": 1.0, "orden_respaldo": 1,
        # Confirmado el 2026-08-24: minado real con la wallet real de
        # Carlos, ~157s vigilados, velocidad estable ~16-17 Mh/s y dos
        # comparios aceptados por el pool de verdad. Ver docs/DECISIONS.md
        # (incluye por qué el Administrador de tareas de Windows puede
        # parecer que la GPU está a 0% aunque esté minando de verdad).
        "confirmado_en_hardware_real": True,
    },
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
