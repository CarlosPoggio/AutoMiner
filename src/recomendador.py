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
    comision_pct: float | None = None
    # Solo se pone a True a mano en monedas.py, moneda por moneda, cuando
    # alguien confirma un minado real de verdad contra esa GPU (ver
    # docs/DECISIONS.md). Por defecto, ninguna de GPU está confirmada.
    confirmado_gpu: bool = False

    @property
    def confirmado_en_hardware_real(self) -> bool:
        """
        Las monedas de CPU soportadas se han podido probar en un entorno
        con procesador real. Las de GPU, por defecto, solo se probaron
        con un ejecutable de prueba, no contra una tarjeta real — salvo
        que monedas.py la marque explícitamente como confirmada tras un
        minado real con éxito (ver `confirmado_gpu` arriba).
        """
        if self.tipo == "cpu":
            return self.soportado_por_minar_hoy
        return self.confirmado_gpu


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
                comision_pct=datos.get("comision_pct"),
                confirmado_gpu=datos.get("confirmado_en_hardware_real", False),
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


def recomendar_cpu(cpu: InfoCPU | None) -> tuple[list[OpcionMoneda], str | None]:
    """
    Como recomendar(), pero solo para el procesador. Devuelve las opciones
    de CPU posibles (ordenadas de mayor a menor ingreso estimado) y el
    símbolo recomendado (el primero del ranking), o ([], None) si no hay
    CPU o ninguna opción.
    """
    simbolos = monedas_cpu_posibles(cpu)
    if not simbolos:
        return [], None
    ordenados = clasificar_por_ingreso(simbolos, TODAS_LAS_MONEDAS)
    return construir_opciones(ordenados), ordenados[0]


def recomendar_gpu(gpus: list[InfoGPU]) -> tuple[list[OpcionMoneda], str | None]:
    """
    Como recomendar(), pero solo para la tarjeta gráfica. Devuelve las
    opciones de GPU posibles (ordenadas de mayor a menor ingreso estimado)
    y el símbolo recomendado, o ([], None) si no hay GPU detectada o
    ninguna con VRAM suficiente.
    """
    simbolos = monedas_gpu_posibles(gpus)
    if not simbolos:
        return [], None
    ordenados = clasificar_por_ingreso(simbolos, TODAS_LAS_MONEDAS)
    return construir_opciones(ordenados), ordenados[0]
