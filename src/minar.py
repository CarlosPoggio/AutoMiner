#!/usr/bin/env python3
"""
Script principal para iniciar el minado de criptomonedas.

Cómo funciona (en palabras simples):
1. Lee un fichero de texto (por defecto config.md) donde escribes tu
   wallet y la moneda que quieres minar.
2. Comprueba que los datos tengan sentido.
3. Busca en tu ordenador el programa que hace el minado de verdad (el
   "motor"; distinto según la moneda, ver src/motores.py).
4. Lo arranca con los datos que escribiste.

Este script NO reinventa el minado desde cero: usa motores de minado ya
existentes y de confianza (ver src/motores.py). Para las monedas de CPU
usa XMRig (RandomX y GhostRider). Para las de GPU usa kawpowminer
(gratuito, código abierto) o lolMiner (gratuito, con una pequeña
comisión del 0,75% — ver docs/DECISIONS.md sobre por qué no se programó
un motor propio). Ver docs/DECISIONS.md para las fuentes de cada pool
por defecto.
"""

import argparse
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable

import motores

# Monedas soportadas en esta primera versión.
# "pool" es el servidor compartido al que se conecta tu ordenador para
# minar en grupo con otras personas (minar en solitario casi nunca
# compensa). "algo" es el nombre técnico del algoritmo de minado, en el
# formato que espera el motor concreto. "motor" indica qué programa (de
# src/motores.py) arranca de verdad el minado.
MONEDAS_SOPORTADAS = {
    "XMR": {
        "nombre": "Monero",
        "algo": "rx/0",
        "motor": "xmrig",
        "pool_por_defecto": "pool.supportxmr.com:3333",
        "wallet_regex": r"^[48][0-9A-Za-z]{94}$",
    },
    "MONERO": {  # alias
        "alias_de": "XMR",
    },
    "WOW": {
        "nombre": "Wownero",
        "algo": "rx/wow",
        "motor": "xmrig",
        "pool_por_defecto": "wownero.ingest.cryptoknight.cc:50901",
        # Prefijo de dirección de Wownero: "Wo3...". Es orientativo: si tu
        # wallet es correcta pero distinta, el script solo avisa, no bloquea.
        "wallet_regex": r"^Wo3[1-9A-HJ-NP-Za-km-z]{85,100}$",
    },
    "ZEPH": {
        "nombre": "Zephyr Protocol",
        "algo": "rx/0",
        "motor": "xmrig",
        "pool_por_defecto": "stratum.ravenminer.com:4000",
        "wallet_regex": r"^ZEPHYR[1-9A-HJ-NP-Za-km-z]{90,105}$",
    },
    "SAL": {
        "nombre": "Salvium",
        "algo": "rx/0",
        "motor": "xmrig",
        "pool_por_defecto": "de.salvium.herominers.com:1228",
        # No se encontró un prefijo fiable documentado; se acepta un rango
        # amplio de longitud en vez de arriesgar un aviso incorrecto.
        "wallet_regex": r"^[1-9A-HJ-NP-Za-km-z]{80,110}$",
    },
    "RTM": {
        "nombre": "Raptoreum",
        "algo": "gr",
        "motor": "xmrig",
        "pool_por_defecto": "rtm.suprnova.cc:4273",
        "extra_args": ["--tls"],
        "wallet_regex": r"^R[1-9A-HJ-NP-Za-km-z]{33}$",
    },
    "RVN": {
        "nombre": "Ravencoin",
        "algo": "kawpow",
        "motor": "kawpowminer",
        "pool_por_defecto": "stratum.ravenminer.com:3838",
        "wallet_regex": r"^R[1-9A-HJ-NP-Za-km-z]{33}$",
        "gpu": True,
    },
    "KAS": {
        "nombre": "Kaspa",
        "algo": "KASPA",
        "motor": "lolminer",
        "pool_por_defecto": "de.kaspa.herominers.com:1206",
        "wallet_regex": r"^kaspa:[a-z0-9]{50,80}$",
        "gpu": True,
    },
    "ALPH": {
        "nombre": "Alephium",
        "algo": "ALEPH",
        "motor": "lolminer",
        "pool_por_defecto": "de.alephium.herominers.com:1199",
        "wallet_regex": r"^[1-9A-HJ-NP-Za-km-z]{44,58}$",
        "gpu": True,
    },
}


def resolver_moneda(codigo: str) -> str:
    codigo = codigo.strip().upper()
    datos = MONEDAS_SOPORTADAS.get(codigo)
    if datos is None:
        return None
    if "alias_de" in datos:
        return datos["alias_de"]
    return codigo


def parsear_config(ruta: Path) -> dict:
    """Lee el fichero .md/.txt con líneas tipo 'clave: valor'."""
    if not ruta.exists():
        raise FileNotFoundError(
            f"No encuentro el fichero de configuración: {ruta}\n"
            f"Copia config.example.md a config.md y rellena tus datos."
        )
    datos = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if ":" not in linea:
            continue
        clave, valor = linea.split(":", 1)
        datos[clave.strip().lower()] = valor.strip()
    return datos


def _subdatos_bloque(bloque: str, datos: dict) -> dict:
    """Extrae las claves de un bloque quitándoles el prefijo. Por ejemplo,
    para bloque='cpu': 'cpu_pool' -> 'pool', 'cpu_hilos' -> 'hilos'. Así
    motores.construir_comando recibe las claves que ya entiende."""
    prefijo = bloque + "_"
    return {k[len(prefijo):]: v for k, v in datos.items() if k.startswith(prefijo)}


def _validar_bloque(bloque: str, datos: dict) -> tuple[str, str, dict] | None:
    """Valida un bloque ('cpu' o 'gpu'). Devuelve (wallet, moneda, subdatos)
    si el bloque está presente y completo; None si no está presente. Lanza
    ValueError si está a medias o la moneda no encaja con el bloque."""
    moneda_raw = datos.get(f"{bloque}_moneda", "")
    wallet = datos.get(f"{bloque}_wallet", "")

    if not moneda_raw and not wallet:
        return None  # bloque ausente: es válido no usar la CPU o la GPU
    if not wallet:
        raise ValueError(f"Falta la línea '{bloque}_wallet:' en el fichero de configuración.")
    if not moneda_raw:
        raise ValueError(f"Falta la línea '{bloque}_moneda:' en el fichero de configuración.")

    moneda = resolver_moneda(moneda_raw)
    if moneda is None:
        soportadas = ", ".join(
            c for c, v in MONEDAS_SOPORTADAS.items() if "alias_de" not in v
        )
        raise ValueError(
            f"La moneda '{moneda_raw}' no está soportada todavía. "
            f"Monedas soportadas: {soportadas}"
        )

    info = MONEDAS_SOPORTADAS[moneda]
    es_gpu = bool(info.get("gpu"))
    if bloque == "cpu" and es_gpu:
        raise ValueError(f"La moneda '{moneda}' es de GPU; no puede ir en el bloque de CPU.")
    if bloque == "gpu" and not es_gpu:
        raise ValueError(f"La moneda '{moneda}' es de CPU; no puede ir en el bloque de GPU.")

    patron = info["wallet_regex"]
    if not re.match(patron, wallet):
        print(
            f"Aviso: la wallet no tiene el formato típico de {info['nombre']}. "
            f"Revisa que la hayas copiado bien (sigo adelante, pero podría fallar).",
            file=sys.stderr,
        )

    return wallet, moneda, _subdatos_bloque(bloque, datos)


def validar(datos: dict) -> dict:
    """Valida el fichero completo. Devuelve un diccionario
    {bloque: (wallet, moneda, subdatos)} con los bloques presentes (uno o
    los dos). Lanza ValueError si no hay ningún bloque completo."""
    bloques = {}
    for bloque in ("cpu", "gpu"):
        resultado = _validar_bloque(bloque, datos)
        if resultado is not None:
            bloques[bloque] = resultado

    if not bloques:
        raise ValueError(
            "El fichero de configuración no tiene ningún bloque completo. "
            "Hace falta al menos cpu_moneda + cpu_wallet o gpu_moneda + gpu_wallet."
        )
    return bloques


def encontrar_motor(moneda: str, raiz_proyecto: Path) -> str | None:
    """Busca el ejecutable del motor que necesita esta moneda (en el
    sistema o en la carpeta bin/ del proyecto)."""
    info = MONEDAS_SOPORTADAS[moneda]
    return motores.encontrar_motor(info["motor"], raiz_proyecto)


def construir_comando(bin_path: str, wallet: str, moneda: str, datos: dict) -> list[str]:
    info = MONEDAS_SOPORTADAS[moneda]
    pool = datos.get("pool", info["pool_por_defecto"])
    cmd = motores.construir_comando(info["motor"], bin_path, wallet, pool, info["algo"], datos)
    cmd += info.get("extra_args", [])
    return cmd


class SesionMinado:
    """Envuelve un proceso de minado en marcha (un Popen) más el hilo que
    lee su salida línea a línea. Permite detenerlo de forma limpia."""

    def __init__(self, proceso: subprocess.Popen, hilo_lector: threading.Thread | None, bloque: str):
        self.proceso = proceso
        self.hilo_lector = hilo_lector
        self.bloque = bloque

    def detener(self, timeout: float = 5.0) -> None:
        """Pide al proceso que termine; si no lo hace en `timeout` segundos,
        lo mata a la fuerza."""
        if self.proceso.poll() is None:
            self.proceso.terminate()
            try:
                self.proceso.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.proceso.kill()
                self.proceso.wait()
        if self.hilo_lector is not None:
            self.hilo_lector.join(timeout=timeout)

    def esperar(self) -> None:
        """Bloquea hasta que el proceso termina por sí solo."""
        self.proceso.wait()
        if self.hilo_lector is not None:
            self.hilo_lector.join()


def iniciar_minado(
    bloque: str,
    moneda_info: dict,
    wallet: str,
    datos: dict,
    raiz_proyecto: Path,
    bin_path: str,
    dry_run: bool,
    on_linea: Callable[[str, str], None],
) -> SesionMinado | None:
    """Arranca el minado de un bloque ('cpu' o 'gpu').

    En dry_run no arranca ningún proceso: solo llama una vez a on_linea con
    el comando que se ejecutaría y devuelve None. En modo real arranca el
    proceso, lanza un hilo que lee su salida y llama a on_linea(bloque,
    linea_cruda) por cada línea, y devuelve la SesionMinado."""
    nombre_motor = moneda_info["motor"]
    pool = datos.get("pool", moneda_info["pool_por_defecto"])
    cmd = motores.construir_comando(nombre_motor, bin_path, wallet, pool, moneda_info["algo"], datos)
    cmd += moneda_info.get("extra_args", [])

    if dry_run:
        on_linea(bloque, f"[dry-run] Comando que se ejecutaría: {' '.join(cmd)}")
        return None

    proceso = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )

    def leer():
        try:
            for linea in proceso.stdout:
                on_linea(bloque, linea.rstrip("\n"))
        finally:
            if proceso.stdout is not None:
                proceso.stdout.close()

    hilo = threading.Thread(target=leer, daemon=True)
    hilo.start()
    return SesionMinado(proceso, hilo, bloque)


def interpretar_linea(linea_cruda: str) -> str | None:
    """Traduce una línea de salida cruda de xmrig/kawpowminer/lolMiner a un
    mensaje legible en español. Devuelve None si la línea es "ruido" que no
    merece mostrarse en el log sencillo (sí seguirá en el log completo)."""
    l = linea_cruda.lower()
    if "accepted" in l:
        return "✅ Comparto aceptado por el pool"
    if "rejected" in l:
        return "⚠️ Comparto rechazado por el pool"
    if "new job" in l:
        return "📥 Nuevo trabajo recibido del pool"
    if "speed" in l:
        idx = l.index("speed")
        resto = linea_cruda[idx:].strip()
        return f"⚡ Velocidad: {resto}" if resto else f"⚡ Velocidad: {linea_cruda.strip()}"
    # Los errores se comprueban antes que "connect" porque una línea de
    # "connection error" contiene ambas palabras y debe salir como error.
    if "error" in l or "fail" in l:
        return "❌ " + linea_cruda
    if "connect" in l:
        return "🔌 Conectado al pool"
    return None


def _preparar_bin(bloque: str, moneda: str, raiz_proyecto: Path, dry_run: bool, on_linea) -> str | None:
    """Localiza (o descarga) el ejecutable del motor de este bloque.
    Devuelve la ruta, o None si no se pudo preparar (ya avisado)."""
    nombre_motor = MONEDAS_SOPORTADAS[moneda]["motor"]
    bin_path = encontrar_motor(moneda, raiz_proyecto)
    if bin_path is not None:
        return bin_path
    if dry_run:
        # En dry-run no descargamos nada: mostramos el comando con un
        # marcador de posición en lugar de la ruta real.
        return f"<{nombre_motor}>"
    try:
        import instalador

        return instalador.asegurar_motor(
            nombre_motor, raiz_proyecto,
            on_progreso=lambda m: on_linea(bloque, m),
        )
    except Exception as e:  # incluye InstaladorError
        print(f"[{bloque.upper()}] No pude preparar el motor '{nombre_motor}': {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="Inicia el minado leyendo un fichero de configuración simple.")
    parser.add_argument(
        "--config", default="config.md",
        help="Ruta al fichero de configuración (por defecto: config.md)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Muestra qué haría, sin conectarse a ningún pool ni minar de verdad.",
    )
    args = parser.parse_args()

    raiz_proyecto = Path(__file__).resolve().parent.parent
    ruta_config = Path(args.config)

    try:
        datos = parsear_config(ruta_config)
        bloques = validar(datos)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    def on_linea(bloque: str, linea: str) -> None:
        print(f"[{bloque.upper()}] {linea}")

    sesiones = []
    for bloque, (wallet, moneda, sub) in bloques.items():
        info = MONEDAS_SOPORTADAS[moneda]
        nombre_motor = info["motor"]

        bin_path = _preparar_bin(bloque, moneda, raiz_proyecto, args.dry_run, on_linea)
        if bin_path is None:
            continue

        comision = motores.MOTORES[nombre_motor]["comision_pct"]
        wallet_oculta = f"{wallet[:6]}...{wallet[-4:]}" if len(wallet) > 12 else wallet
        print(f"[{bloque.upper()}] Moneda: {info['nombre']} ({moneda})")
        print(f"[{bloque.upper()}] Motor: {nombre_motor}" + (f" (comisión del {comision}%)" if comision else " (sin comisión)"))
        print(f"[{bloque.upper()}] Wallet: {wallet_oculta}")

        try:
            sesion = iniciar_minado(bloque, info, wallet, sub, raiz_proyecto, bin_path, args.dry_run, on_linea)
        except PermissionError as e:
            print(
                f"[{bloque.upper()}] No se pudo arrancar el motor de minado (permiso "
                f"denegado: {e}). Es muy probable que el antivirus (Windows Defender u "
                "otro) haya bloqueado o puesto en cuarentena el programa recién "
                "descargado — es habitual, porque los antivirus marcan los mineros como "
                "sospechosos aunque sean legítimos. Añade una excepción para la carpeta "
                "'bin' de este proyecto en tu antivirus y vuelve a intentarlo.",
                file=sys.stderr,
            )
            continue
        except OSError as e:
            print(f"[{bloque.upper()}] No se pudo arrancar el motor de minado: {e}", file=sys.stderr)
            continue
        if sesion is not None:
            sesiones.append(sesion)

    if args.dry_run:
        print("\n[dry-run] No se ha iniciado ningún proceso de minado real.")
        return

    if not sesiones:
        print("No se pudo arrancar ningún motor de minado.", file=sys.stderr)
        sys.exit(1)

    print("\nMinando... (Ctrl+C para detener)")
    try:
        for sesion in sesiones:
            sesion.esperar()
    except KeyboardInterrupt:
        print("\nDeteniendo el minado...")
        for sesion in sesiones:
            sesion.detener()


if __name__ == "__main__":
    main()
