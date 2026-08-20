"""
Detección de hardware (CPU y tarjetas gráficas) del ordenador donde se
ejecuta este script.

Es una detección "a mejor esfuerzo": usa comandos que ya vienen instalados
en Windows, Mac y Linux (no instala nada nuevo). Si algo no se puede
detectar automáticamente, se indica claramente en vez de inventar un dato.
"""

import platform
import re
import subprocess
from dataclasses import dataclass, field


@dataclass
class InfoCPU:
    modelo: str
    nucleos_logicos: int


@dataclass
class InfoGPU:
    modelo: str
    vram_gb: float | None  # None = no se pudo determinar la VRAM
    fabricante: str  # "NVIDIA", "AMD", "Intel" o "Desconocido"


def _ejecutar(cmd: list[str], timeout: float = 5.0) -> str | None:
    """Ejecuta un comando externo y devuelve su salida, o None si falla."""
    try:
        resultado = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        if resultado.returncode == 0 and resultado.stdout.strip():
            return resultado.stdout
        return None
    except (OSError, subprocess.SubprocessError):
        return None


def detectar_cpu() -> InfoCPU:
    import os

    modelo = None
    sistema = platform.system()

    if sistema == "Linux":
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                for linea in f:
                    if linea.lower().startswith("model name"):
                        modelo = linea.split(":", 1)[1].strip()
                        break
        except OSError:
            pass
    elif sistema == "Darwin":  # macOS
        salida = _ejecutar(["sysctl", "-n", "machdep.cpu.brand_string"])
        if salida:
            modelo = salida.strip()
    elif sistema == "Windows":
        salida = _ejecutar(["wmic", "cpu", "get", "name"])
        if salida:
            lineas = [l.strip() for l in salida.splitlines() if l.strip()]
            if len(lineas) >= 2:
                modelo = lineas[1]

    if not modelo:
        modelo = platform.processor() or platform.machine() or "Desconocido"

    return InfoCPU(modelo=modelo, nucleos_logicos=os.cpu_count() or 1)


def _detectar_gpus_nvidia() -> list[InfoGPU]:
    salida = _ejecutar([
        "nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits",
    ])
    if not salida:
        return []
    gpus = []
    for linea in salida.strip().splitlines():
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) != 2:
            continue
        nombre, vram_mib = partes
        try:
            vram_gb = round(float(vram_mib) / 1024, 1)
        except ValueError:
            vram_gb = None
        gpus.append(InfoGPU(modelo=nombre, vram_gb=vram_gb, fabricante="NVIDIA"))
    return gpus


def _detectar_gpus_amd_linux() -> list[InfoGPU]:
    salida = _ejecutar(["rocm-smi", "--showproductname", "--showmeminfo", "vram"])
    if not salida:
        return []
    # Salida variable según versión de rocm-smi: buscamos nombre y VRAM total.
    gpus = []
    nombre = None
    for linea in salida.splitlines():
        m_nombre = re.search(r"Card series:\s*(.+)", linea, re.IGNORECASE)
        if m_nombre:
            nombre = m_nombre.group(1).strip()
        m_vram = re.search(r"VRAM Total Memory.*?:\s*(\d+)", linea, re.IGNORECASE)
        if m_vram and nombre:
            vram_gb = round(int(m_vram.group(1)) / (1024 ** 3), 1)
            gpus.append(InfoGPU(modelo=nombre, vram_gb=vram_gb, fabricante="AMD"))
            nombre = None
    return gpus


def _detectar_gpus_windows() -> list[InfoGPU]:
    salida = _ejecutar(["wmic", "path", "win32_VideoController", "get", "name,AdapterRAM"])
    if not salida:
        return []
    gpus = []
    lineas = [l.strip() for l in salida.splitlines() if l.strip()]
    for linea in lineas[1:]:  # la primera línea es la cabecera
        partes = linea.rsplit(None, 1)
        if len(partes) != 2:
            gpus.append(InfoGPU(modelo=linea, vram_gb=None, fabricante="Desconocido"))
            continue
        nombre, ram_bytes = partes
        vram_gb = None
        try:
            valor = int(ram_bytes)
            # AdapterRAM es un campo de 32 bits: en tarjetas modernas con más
            # de 4 GB, Windows suele devolver un número incorrecto. Si pasa
            # eso, mejor no mostrar un dato erróneo.
            if 0 < valor < 4 * 1024 ** 3:
                vram_gb = round(valor / (1024 ** 3), 1)
        except ValueError:
            pass
        fabricante = "Desconocido"
        nombre_bajo = nombre.lower()
        if "nvidia" in nombre_bajo:
            fabricante = "NVIDIA"
        elif "amd" in nombre_bajo or "radeon" in nombre_bajo:
            fabricante = "AMD"
        elif "intel" in nombre_bajo:
            fabricante = "Intel"
        gpus.append(InfoGPU(modelo=nombre, vram_gb=vram_gb, fabricante=fabricante))
    return gpus


def _detectar_gpus_mac() -> list[InfoGPU]:
    salida = _ejecutar(["system_profiler", "SPDisplaysDataType"])
    if not salida:
        return []
    gpus = []
    nombre = None
    for linea in salida.splitlines():
        linea = linea.strip()
        m_nombre = re.match(r"Chipset Model:\s*(.+)", linea)
        if m_nombre:
            nombre = m_nombre.group(1).strip()
            continue
        m_vram = re.match(r"VRAM \(Total\):\s*([\d.]+)\s*(GB|MB)", linea)
        if m_vram and nombre:
            valor = float(m_vram.group(1))
            vram_gb = valor if m_vram.group(2) == "GB" else round(valor / 1024, 1)
            fabricante = "Desconocido"
            nombre_bajo = nombre.lower()
            if "nvidia" in nombre_bajo:
                fabricante = "NVIDIA"
            elif "amd" in nombre_bajo or "radeon" in nombre_bajo:
                fabricante = "AMD"
            elif "apple" in nombre_bajo or "intel" in nombre_bajo:
                fabricante = "Integrada"
            gpus.append(InfoGPU(modelo=nombre, vram_gb=vram_gb, fabricante=fabricante))
            nombre = None
    return gpus


def _detectar_gpus_lspci() -> list[InfoGPU]:
    """Último recurso en Linux: da el nombre pero no la VRAM."""
    salida = _ejecutar(["lspci"])
    if not salida:
        return []
    gpus = []
    for linea in salida.splitlines():
        if re.search(r"VGA compatible controller|3D controller", linea, re.IGNORECASE):
            nombre = linea.split(":", 2)[-1].strip()
            fabricante = "Desconocido"
            nombre_bajo = nombre.lower()
            if "nvidia" in nombre_bajo:
                fabricante = "NVIDIA"
            elif "amd" in nombre_bajo or "radeon" in nombre_bajo:
                fabricante = "AMD"
            elif "intel" in nombre_bajo:
                fabricante = "Intel"
            gpus.append(InfoGPU(modelo=nombre, vram_gb=None, fabricante=fabricante))
    return gpus


def detectar_gpus() -> list[InfoGPU]:
    """
    Intenta varias estrategias, de más a menos precisa, y se queda con la
    primera que dé resultado. No junta resultados de varias estrategias
    para evitar listar la misma tarjeta dos veces.
    """
    sistema = platform.system()

    estrategias = [_detectar_gpus_nvidia]  # nvidia-smi funciona en los 3 SO
    if sistema == "Linux":
        estrategias += [_detectar_gpus_amd_linux, _detectar_gpus_lspci]
    elif sistema == "Windows":
        estrategias += [_detectar_gpus_windows]
    elif sistema == "Darwin":
        estrategias += [_detectar_gpus_mac]

    for estrategia in estrategias:
        gpus = estrategia()
        if gpus:
            return gpus
    return []
