#!/usr/bin/env python3
"""
Script principal para iniciar el minado de criptomonedas.

Cómo funciona (en palabras simples):
1. Lee un fichero de texto (por defecto config.md) donde escribes tu
   wallet y la moneda que quieres minar.
2. Comprueba que los datos tengan sentido.
3. Busca el programa que hace el minado de verdad (XMRig) en tu ordenador.
4. Lo arranca con los datos que escribiste.

Este script NO reinventa el minado desde cero: usa XMRig por debajo,
que es el programa estándar y de confianza que usa la comunidad para
minar monedas de la familia RandomX (la más conocida es Monero / XMR) y,
desde esta versión, también GhostRider (Raptoreum), que XMRig soporta de
forma oficial. Ver docs/DECISIONS.md para la explicación de por qué se
eligió así, y para las fuentes de cada pool por defecto.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Monedas soportadas en esta primera versión.
# "pool" es el servidor compartido al que se conecta tu ordenador para
# minar en grupo con otras personas (minar en solitario casi nunca
# compensa). "algo" es el nombre técnico del algoritmo de minado.
MONEDAS_SOPORTADAS = {
    "XMR": {
        "nombre": "Monero",
        "algo": "rx/0",
        "pool_por_defecto": "pool.supportxmr.com:3333",
        "wallet_regex": r"^[48][0-9A-Za-z]{94}$",
    },
    "MONERO": {  # alias
        "alias_de": "XMR",
    },
    "WOW": {
        "nombre": "Wownero",
        "algo": "rx/wow",
        "pool_por_defecto": "wownero.ingest.cryptoknight.cc:50901",
        # Prefijo de dirección de Wownero: "Wo3...". Es orientativo: si tu
        # wallet es correcta pero distinta, el script solo avisa, no bloquea.
        "wallet_regex": r"^Wo3[1-9A-HJ-NP-Za-km-z]{85,100}$",
    },
    "ZEPH": {
        "nombre": "Zephyr Protocol",
        "algo": "rx/0",
        "pool_por_defecto": "stratum.ravenminer.com:4000",
        "wallet_regex": r"^ZEPHYR[1-9A-HJ-NP-Za-km-z]{90,105}$",
    },
    "SAL": {
        "nombre": "Salvium",
        "algo": "rx/0",
        "pool_por_defecto": "de.salvium.herominers.com:1228",
        # No se encontró un prefijo fiable documentado; se acepta un rango
        # amplio de longitud en vez de arriesgar un aviso incorrecto.
        "wallet_regex": r"^[1-9A-HJ-NP-Za-km-z]{80,110}$",
    },
    "RTM": {
        "nombre": "Raptoreum",
        "algo": "gr",
        "pool_por_defecto": "rtm.suprnova.cc:4273",
        "extra_args": ["--tls"],
        "wallet_regex": r"^R[1-9A-HJ-NP-Za-km-z]{33}$",
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


def validar(datos: dict) -> tuple[str, str, dict]:
    wallet = datos.get("wallet", "")
    moneda_raw = datos.get("moneda", "")

    if not wallet:
        raise ValueError("Falta la línea 'wallet:' en el fichero de configuración.")
    if not moneda_raw:
        raise ValueError("Falta la línea 'moneda:' en el fichero de configuración.")

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
    patron = info["wallet_regex"]
    if not re.match(patron, wallet):
        print(
            f"Aviso: la wallet no tiene el formato típico de {info['nombre']}. "
            f"Revisa que la hayas copiado bien (sigo adelante, pero podría fallar).",
            file=sys.stderr,
        )

    return wallet, moneda, datos


def encontrar_xmrig(raiz_proyecto: Path) -> str | None:
    """Busca xmrig instalado en el sistema o en la carpeta bin/ del proyecto."""
    en_path = shutil.which("xmrig")
    if en_path:
        return en_path
    local = raiz_proyecto / "bin" / "xmrig"
    if local.exists():
        return str(local)
    local_exe = raiz_proyecto / "bin" / "xmrig.exe"
    if local_exe.exists():
        return str(local_exe)
    return None


def construir_comando(xmrig_path: str, wallet: str, moneda: str, datos: dict) -> list[str]:
    info = MONEDAS_SOPORTADAS[moneda]
    pool = datos.get("pool", info["pool_por_defecto"])
    cmd = [
        xmrig_path,
        "-o", pool,
        "-u", wallet,
        "-p", "x",
        "--algo", info["algo"],
    ]
    hilos = datos.get("hilos") or datos.get("threads")
    if hilos:
        cmd += ["-t", str(hilos)]
    cmd += info.get("extra_args", [])
    return cmd


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
        wallet, moneda, datos = validar(datos)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    xmrig_path = encontrar_xmrig(raiz_proyecto)
    if xmrig_path is None:
        print(
            "No encuentro XMRig instalado. Sigue las instrucciones de "
            "docs/GLOSSARY.md / README para instalarlo y vuelve a intentarlo.",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = construir_comando(xmrig_path, wallet, moneda, datos)

    wallet_oculta = f"{wallet[:6]}...{wallet[-4:]}" if len(wallet) > 12 else wallet
    print(f"Moneda: {MONEDAS_SOPORTADAS[moneda]['nombre']} ({moneda})")
    print(f"Wallet: {wallet_oculta}")
    print(f"Comando: {' '.join(cmd)}")

    if args.dry_run:
        print("\n[dry-run] No se ha iniciado ningún proceso de minado real.")
        return

    print("\nIniciando minado... (Ctrl+C para detener)")
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
