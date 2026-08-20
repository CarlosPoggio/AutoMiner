"""
Combina el hardware detectado con el catálogo de monedas para decidir:
- qué monedas son técnicamente posibles de minar con ese hardware.
- cuál de ellas recomendar por defecto (la de mayor ingreso estimado).

"Técnicamente posible" es solo eso: una comprobación de si el hardware
cumple lo mínimo para el algoritmo (por ejemplo, memoria de vídeo
suficiente). No tiene en cuenta si merece la pena económicamente.
"""

from dataclasses import dataclass

from hardware import InfoCPU, InfoGPU
from ingresos import clasificar_por_ingreso
from monedas import MONEDAS_CPU, MONEDAS_GPU, TODAS_LAS_MONEDAS


@dataclass
class OpcionMoneda:
    simbolo: str
    nombre: str
    algoritmo: str
    tipo: str  # "cpu" o "gpu"
    soportado_por_minar_hoy: bool
    riesgo: str | None = None


def monedas_cpu_posibles(cpu: InfoCPU | None) -> list[str]:
    """Con cualquier CPU normal, todas las monedas de CPU son posibles."""
    if cpu is None:
        return []
    return list(MONEDAS_CPU.keys())


def monedas_gpu_posibles(gpus: list[InfoGPU]) -> list[str]:
    """
    Una moneda de GPU es técnicamente posible si al menos una tarjeta
    detectada cumple la VRAM mínima. Si no se pudo saber la VRAM de
    ninguna tarjeta, se muestran todas igualmente (no podemos descartar
    por falta de dato), avisando de que es sin confirmar.
    """
    if not gpus:
        return []

    vram_conocida = [g.vram_gb for g in gpus if g.vram_gb is not None]
    if not vram_conocida:
        return list(MONEDAS_GPU.keys())

    vram_maxima = max(vram_conocida)
    return [
        simbolo
        for simbolo, datos in MONEDAS_GPU.items()
        if vram_maxima >= datos["vram_min_gb"]
    ]


def construir_opciones(simbolos: list[str]) -> list[OpcionMoneda]:
    opciones = []
    for simbolo in simbolos:
        datos = TODAS_LAS_MONEDAS[simbolo]
        opciones.append(
            OpcionMoneda(
                simbolo=simbolo,
                nombre=datos["nombre"],
                algoritmo=datos["algoritmo"],
                tipo=datos["tipo"],
                soportado_por_minar_hoy=datos["soportado_por_minar_hoy"],
                riesgo=datos.get("riesgo"),
            )
        )
    return opciones


def recomendar(cpu: InfoCPU | None, gpus: list[InfoGPU]) -> tuple[list[OpcionMoneda], str | None]:
    """
    Devuelve (lista_de_opciones_posibles, simbolo_recomendado).
    simbolo_recomendado es None si no hay ninguna opción posible.
    """
    simbolos_posibles = monedas_cpu_posibles(cpu) + monedas_gpu_posibles(gpus)
    if not simbolos_posibles:
        return [], None

    ordenados = clasificar_por_ingreso(simbolos_posibles, TODAS_LAS_MONEDAS)
    return construir_opciones(simbolos_posibles), ordenados[0]
