#!/usr/bin/env python3
"""
Aplicación gráfica (Tkinter) que hace todo el trabajo por el usuario:

1. Analiza el hardware del ordenador (CPU y tarjeta gráfica).
2. Muestra qué criptomonedas se pueden minar técnicamente con la CPU y con
   la GPU, cada una en su bloque, dejando preseleccionada la de mayor
   ingreso estimado.
3. Al pulsar "Comenzar a minar":
   - Guarda config.md (formato dual: bloque de CPU y/o de GPU).
   - Descarga automáticamente el motor de minado que haga falta (si no
     está ya instalado) con src/instalador.py.
   - Arranca el minado (CPU y/o GPU a la vez) y muestra un registro en
     vivo, traducido a lenguaje sencillo, con opción de ver el log técnico.

Este fichero necesita una pantalla (no funciona en un servidor sin
interfaz gráfica). Se ejecuta con:

    python3 src/formulario.py

La lógica que no depende de Tkinter (qué habilita el botón, cómo se arma
la configuración) está extraída en funciones sueltas para poder probarla
con tests sin necesidad de pantalla (ver tests/test_formulario_logica.py).
"""

import ctypes
import queue
import sys
import threading
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk

from hardware import InfoGPU, detectar_cpu, detectar_gpus
from config_writer import guardar_config
from recomendador import recomendar_cpu, recomendar_gpu
from wallets_defecto import cargar_wallets_por_defecto
import aislamiento_nucleo
import instalador
import minar
import estimacion_ingreso
from estimacion_ingreso import EstimacionReferencia
from minar import MONEDAS_SOPORTADAS

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# Lógica NO gráfica (testeable sin pantalla)
# --------------------------------------------------------------------------

def es_administrador() -> bool:
    """
    True si este proceso se está ejecutando con permisos de
    administrador de Windows (por ejemplo, abierto con "Iniciar minado
    (rendimiento máximo).bat"). En Mac/Linux siempre da False: ahí no
    aplica esta distinción (xmrig no necesita nada especial).
    """
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except OSError:
        return False


def texto_modo(admin: bool) -> str:
    if admin:
        return "🚀 Modo rendimiento: activo (permisos de administrador)"
    return "Modo normal (sin permisos de administrador — un poco más lento al minar con CPU)"


def _etiqueta_opcion(opcion) -> str:
    if not opcion.soportado_por_minar_hoy:
        icono = "🚧"  # todavía no implementado en minar.py
    elif opcion.confirmado_en_hardware_real:
        icono = "✅"  # implementado y probado en este tipo de hardware
    else:
        icono = "🧪"  # implementado pero sin confirmar en una GPU real
    return f"{icono} [{opcion.tipo.upper()}] {opcion.nombre} ({opcion.simbolo}) — {opcion.algoritmo}"


def filtrar_solo_soportadas(opciones: list) -> tuple[list, str | None]:
    """
    Se muestran en los desplegables solo las monedas que minar.py ya sabe
    arrancar de verdad (soportado_por_minar_hoy). Enseñar en el desplegable
    una moneda que luego no se puede minar es confuso para alguien que no
    es técnico. `opciones` ya viene ordenada de mayor a menor ingreso
    estimado (ver recomendador.recomendar_cpu/recomendar_gpu), así que la
    recomendación es simplemente la primera que quede tras filtrar.
    """
    filtradas = [o for o in opciones if o.soportado_por_minar_hoy]
    recomendado = filtradas[0].simbolo if filtradas else None
    return filtradas, recomendado


def _formato_moneda(valor: float) -> str:
    """Formatea una cantidad de moneda por hora de forma legible, tanto si
    es grande como si es diminuta (algunas monedas rinden fracciones muy
    pequeñas a la velocidad de referencia)."""
    if valor >= 1:
        return f"{valor:,.4f}"
    if valor >= 0.0001:
        return f"{valor:.6f}"
    return f"{valor:.2e}"


def _formato_usd(valor: float) -> str:
    if valor >= 0.01:
        return f"{valor:.2f} $"
    if valor >= 0.0001:
        return f"{valor:.4f} $"
    return f"{valor:.2e} $"


def texto_estimacion(est: "EstimacionReferencia | None") -> str:
    """Construye el texto que se muestra bajo cada desplegable a partir de
    una estimación (o None). Es una función NO gráfica: no crea ninguna
    ventana, para poder probarla con tests sin pantalla."""
    if est is None:
        return "Estimación no disponible ahora mismo"
    moneda = _formato_moneda(est.moneda_por_hora)
    usd = _formato_usd(est.usd_por_hora)
    return (
        f"≈ {moneda} {est.simbolo}/hora   ≈ {usd}/hora   "
        f"(referencia para {est.hashrate_referencia} — no es la velocidad real "
        f"de tu hardware; sirve para comparar entre monedas)"
    )


def texto_ingreso_real(
    simbolo: str, disponible: bool, hashrate_texto: "str | None" = None,
    moneda_por_hora: "float | None" = None, usd_por_hora: "float | None" = None,
) -> str:
    """
    Construye el texto del ingreso estimado con el hashrate REAL medido
    durante el minado (a diferencia de texto_estimacion, que es siempre a
    una velocidad de referencia fija). `disponible=False` significa que
    esta moneda no tiene fuente de datos verificada (igual que
    estimacion_ingreso.estimar_referencia devolviendo None). Mientras
    `hashrate_texto` sea None (todavía no ha llegado ninguna lectura del
    motor), se muestra "calculando"."""
    if not disponible:
        return f"{simbolo}: estimación no disponible para esta moneda"
    if hashrate_texto is None:
        return f"{simbolo}: calculando tu velocidad real…"
    moneda = _formato_moneda(moneda_por_hora)
    usd = _formato_usd(usd_por_hora)
    return f"{simbolo} a tu velocidad real ({hashrate_texto}): ≈ {moneda} {simbolo}/hora   ≈ {usd}/hora"


def boton_habilitado(cpu_activa: bool, cpu_wallet: str, gpu_activa: bool, gpu_wallet: str) -> bool:
    """El botón de comenzar se activa si al menos un bloque está marcado y
    tiene una wallet no vacía."""
    cpu_ok = bool(cpu_activa) and bool((cpu_wallet or "").strip())
    gpu_ok = bool(gpu_activa) and bool((gpu_wallet or "").strip())
    return cpu_ok or gpu_ok


def construir_bloques_config(
    cpu_activa: bool, cpu_simbolo: str | None, cpu_wallet: str,
    gpu_activa: bool, gpu_simbolo: str | None, gpu_wallet: str,
) -> tuple[dict | None, dict | None]:
    """Arma los diccionarios cpu/gpu que espera config_writer.guardar_config
    a partir del estado de los widgets. Un bloque es None si no está activo,
    le falta moneda o le falta wallet."""
    cpu = None
    gpu = None
    if cpu_activa and cpu_simbolo and (cpu_wallet or "").strip():
        cpu = {"simbolo": cpu_simbolo, "wallet": cpu_wallet.strip()}
    if gpu_activa and gpu_simbolo and (gpu_wallet or "").strip():
        gpu = {"simbolo": gpu_simbolo, "wallet": gpu_wallet.strip()}
    return cpu, gpu


# --------------------------------------------------------------------------
# Interfaz gráfica
# --------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minar criptomonedas")
        self.geometry("680x760")
        self.minsize(600, 600)

        # Estado del minado en marcha.
        self.cola: "queue.Queue" = queue.Queue()
        self.sesiones: list = []
        self.log_lineas: list[tuple[str, str, str | None]] = []  # (bloque, cruda, interpretada)
        self._bucle_activo = False

        # Estimaciones de ingreso (se calculan en segundo plano para no
        # congelar la ventana mientras se consultan las APIs).
        self.cola_est: "queue.Queue" = queue.Queue()
        self._est_activo = False

        # Variables manuales de VRAM (por si la detección de GPU falla).
        self.gpu_manual_vram = tk.DoubleVar(value=0)
        self.gpu_manual_activa = tk.BooleanVar(value=False)

        # Variables de selección.
        self.cpu_activa = tk.BooleanVar(value=False)
        self.gpu_activa = tk.BooleanVar(value=False)

        # Wallets por defecto (wallets.md), para rellenar el campo solo.
        self.wallets_defecto = cargar_wallets_por_defecto(RAIZ_PROYECTO / "wallets.md")
        self._ultima_moneda_cpu = None
        self._ultima_moneda_gpu = None

        self.frame_config = None
        self.frame_logs = None

        self._detectar()
        self._construir_config()

    # ---- detección de hardware y recomendaciones ----

    def _detectar(self):
        self.cpu = detectar_cpu()
        self.gpus = detectar_gpus()
        if self.gpu_manual_activa.get() and self.gpu_manual_vram.get() > 0:
            self.gpus = [InfoGPU(
                modelo="(indicada manualmente)",
                vram_gb=self.gpu_manual_vram.get(),
                fabricante="Desconocido",
            )]

        opciones_cpu, _ = recomendar_cpu(self.cpu)
        opciones_gpu, _ = recomendar_gpu(self.gpus)
        self.opciones_cpu, self.recomendado_cpu = filtrar_solo_soportadas(opciones_cpu)
        self.opciones_gpu, self.recomendado_gpu = filtrar_solo_soportadas(opciones_gpu)

    def _fabricante_gpu(self) -> str | None:
        for g in self.gpus:
            if g.fabricante and g.fabricante != "Desconocido":
                return g.fabricante
        return None

    # ---- pantalla de configuración ----

    def _construir_config(self):
        if self.frame_logs is not None:
            self.frame_logs.destroy()
            self.frame_logs = None

        self.frame_config = ttk.Frame(self, padding=16)
        self.frame_config.pack(fill="both", expand=True)
        marco = self.frame_config

        admin = es_administrador()
        ttk.Label(
            marco, text=texto_modo(admin),
            foreground=("#0a7a3f" if admin else "#777777"),
        ).pack(anchor="w", pady=(0, 8))

        ttk.Label(marco, text="Hardware detectado", font=("", 12, "bold")).pack(anchor="w")
        self.txt_hardware = tk.Text(marco, height=4, width=72, state="disabled", wrap="word")
        self.txt_hardware.pack(anchor="w", pady=(2, 10), fill="x")

        # --- bloque CPU ---
        marco_cpu = ttk.LabelFrame(marco, text="Procesador (CPU)", padding=10)
        marco_cpu.pack(anchor="w", fill="x", pady=(0, 10))
        self.chk_cpu = ttk.Checkbutton(
            marco_cpu, text="Minar con la CPU", variable=self.cpu_activa,
            command=self._on_toggle,
        )
        self.chk_cpu.pack(anchor="w")
        self.combo_cpu = ttk.Combobox(marco_cpu, state="disabled", width=68)
        self.combo_cpu.pack(anchor="w", pady=(6, 2))
        self.combo_cpu.bind("<<ComboboxSelected>>", lambda e: self._on_combo_cpu())
        self.lbl_est_cpu = ttk.Label(marco_cpu, foreground="#0a7a3f", wraplength=620, justify="left")
        self.lbl_est_cpu.pack(anchor="w", pady=(2, 2))
        ttk.Label(marco_cpu, text="Tu wallet para la CPU:").pack(anchor="w", pady=(4, 0))
        self.entry_wallet_cpu = ttk.Entry(marco_cpu, width=70, state="disabled")
        self.entry_wallet_cpu.pack(anchor="w", pady=(2, 0))
        self.entry_wallet_cpu.bind("<KeyRelease>", lambda e: self._actualizar_boton())

        # --- bloque GPU ---
        marco_gpu = ttk.LabelFrame(marco, text="Tarjeta gráfica (GPU)", padding=10)
        marco_gpu.pack(anchor="w", fill="x", pady=(0, 10))
        self.chk_gpu = ttk.Checkbutton(
            marco_gpu, text="Minar con la GPU", variable=self.gpu_activa,
            command=self._on_toggle,
        )
        self.chk_gpu.pack(anchor="w")

        # Ajuste manual de VRAM por si la detección falla.
        marco_manual = ttk.Frame(marco_gpu)
        marco_manual.pack(anchor="w", pady=(4, 4), fill="x")
        ttk.Checkbutton(
            marco_manual,
            text="No se detectó bien mi GPU: tengo una dedicada con al menos (GB):",
            variable=self.gpu_manual_activa, command=self._reanalizar,
        ).pack(side="left")
        ttk.Spinbox(
            marco_manual, from_=1, to=48, textvariable=self.gpu_manual_vram, width=5,
            command=self._reanalizar,
        ).pack(side="left", padx=6)

        self.combo_gpu = ttk.Combobox(marco_gpu, state="disabled", width=68)
        self.combo_gpu.pack(anchor="w", pady=(6, 2))
        self.combo_gpu.bind("<<ComboboxSelected>>", lambda e: self._on_combo_gpu())
        self.lbl_est_gpu = ttk.Label(marco_gpu, foreground="#0a7a3f", wraplength=620, justify="left")
        self.lbl_est_gpu.pack(anchor="w", pady=(2, 2))
        ttk.Label(marco_gpu, text="Tu wallet para la GPU:").pack(anchor="w", pady=(4, 0))
        self.entry_wallet_gpu = ttk.Entry(marco_gpu, width=70, state="disabled")
        self.entry_wallet_gpu.pack(anchor="w", pady=(2, 0))
        self.entry_wallet_gpu.bind("<KeyRelease>", lambda e: self._actualizar_boton())
        self.lbl_gpu_vacia = ttk.Label(marco_gpu, foreground="#b45309", wraplength=600, justify="left")
        self.lbl_gpu_vacia.pack(anchor="w", pady=(4, 0))

        ttk.Label(
            marco,
            text="Solo se muestran monedas que esta app ya sabe minar de verdad. "
            "✅ probada con hardware real   🧪 lista pero sin confirmar en GPU real",
            foreground="#555555", wraplength=620, justify="left",
        ).pack(anchor="w", pady=(2, 6))

        self.btn_comenzar = ttk.Button(marco, text="Comenzar a minar", command=self._comenzar)
        self.btn_comenzar.pack(anchor="w", pady=(6, 0))
        self.btn_comenzar.state(["disabled"])

        self._mostrar_resumen_hardware()
        self._rellenar_combos()
        self._on_toggle()

        # Arranca el sondeo de estimaciones y calcula las de las monedas ya
        # preseleccionadas en cada desplegable.
        self._est_activo = True
        self.after(150, self._procesar_cola_est)
        self._refrescar_estimaciones()

    def _mostrar_resumen_hardware(self):
        self.txt_hardware.configure(state="normal")
        self.txt_hardware.delete("1.0", "end")
        lineas = [f"CPU: {self.cpu.modelo} ({self.cpu.nucleos_logicos} núcleos lógicos)"]
        if self.gpus:
            for g in self.gpus:
                vram = f"{g.vram_gb} GB" if g.vram_gb is not None else "VRAM desconocida"
                lineas.append(f"GPU: {g.modelo} — {vram} ({g.fabricante})")
        else:
            lineas.append("GPU: no se detectó ninguna tarjeta gráfica dedicada automáticamente.")
        self.txt_hardware.insert("1.0", "\n".join(lineas))
        self.txt_hardware.configure(state="disabled")

    def _fijar_combo(self, combo, opciones, recomendado, mapa_por_etiqueta):
        """Rellena los valores del combo. Si la moneda que ya tenía elegida
        el usuario sigue siendo válida, la conserva (para no deshacer su
        elección cada vez que se vuelve a analizar el hardware); si no,
        cae en la recomendada."""
        simbolo_actual = self._simbolo_combo(combo, mapa_por_etiqueta)
        if simbolo_actual and any(o.simbolo == simbolo_actual for o in opciones):
            objetivo = simbolo_actual
        else:
            objetivo = recomendado

        if objetivo:
            obj = next(o for o in opciones if o.simbolo == objetivo)
            combo.set(_etiqueta_opcion(obj))
        elif opciones:
            combo.current(0)
        else:
            combo.set("")

    def _rellenar_combos(self):
        # CPU
        etiquetas_cpu = [_etiqueta_opcion(o) for o in self.opciones_cpu]
        self._opciones_cpu_por_etiqueta = dict(zip(etiquetas_cpu, self.opciones_cpu))
        self.combo_cpu["values"] = etiquetas_cpu
        self._fijar_combo(self.combo_cpu, self.opciones_cpu, self.recomendado_cpu, self._opciones_cpu_por_etiqueta)

        # GPU
        etiquetas_gpu = [_etiqueta_opcion(o) for o in self.opciones_gpu]
        self._opciones_gpu_por_etiqueta = dict(zip(etiquetas_gpu, self.opciones_gpu))
        self.combo_gpu["values"] = etiquetas_gpu
        self._fijar_combo(self.combo_gpu, self.opciones_gpu, self.recomendado_gpu, self._opciones_gpu_por_etiqueta)

        if not self.opciones_gpu:
            self.lbl_gpu_vacia.configure(
                text="No hay ninguna moneda de GPU disponible ahora mismo: puede ser "
                "que no se haya detectado bien tu tarjeta (marca la casilla de "
                "abajo e indica su VRAM), que no tenga memoria suficiente, o que "
                "esta app todavía no sepa minar ninguna moneda compatible con ella."
            )
            self.gpu_activa.set(False)
        else:
            self.lbl_gpu_vacia.configure(text="")

        self._autorrellenar_wallet_si_cambio("cpu", self.combo_cpu, self._opciones_cpu_por_etiqueta, self.entry_wallet_cpu)
        self._autorrellenar_wallet_si_cambio("gpu", self.combo_gpu, self._opciones_gpu_por_etiqueta, self.entry_wallet_gpu)

    def _autorrellenar_wallet_si_cambio(self, bloque: str, combo, mapa_opciones, entry):
        """Si la moneda elegida en `combo` ha cambiado de verdad respecto a
        la última vez, y tiene wallet en wallets.md, la pone en `entry`
        (sustituyendo lo que hubiera antes). Si la moneda es la misma que
        ya estaba, no toca `entry` — así no se borra lo que el usuario
        haya escrito a mano al reanalizar el hardware sin cambiar de
        moneda (por ejemplo, al indicar la VRAM manualmente)."""
        atributo = f"_ultima_moneda_{bloque}"
        simbolo = self._simbolo_combo(combo, mapa_opciones)
        if simbolo == getattr(self, atributo):
            return
        setattr(self, atributo, simbolo)
        wallet = self.wallets_defecto.get(simbolo, "") if simbolo else ""
        entry.delete(0, "end")
        if wallet:
            entry.insert(0, wallet)

    def _on_combo_cpu(self):
        self._autorrellenar_wallet_si_cambio("cpu", self.combo_cpu, self._opciones_cpu_por_etiqueta, self.entry_wallet_cpu)
        self._actualizar_boton()
        self._actualizar_estimacion("cpu")

    def _on_combo_gpu(self):
        self._autorrellenar_wallet_si_cambio("gpu", self.combo_gpu, self._opciones_gpu_por_etiqueta, self.entry_wallet_gpu)
        self._actualizar_boton()
        self._actualizar_estimacion("gpu")

    # ---- estimaciones de ingreso (en segundo plano) ----

    def _widgets_estimacion(self, bloque: str):
        if bloque == "cpu":
            return self.combo_cpu, self._opciones_cpu_por_etiqueta, self.lbl_est_cpu
        return self.combo_gpu, self._opciones_gpu_por_etiqueta, self.lbl_est_gpu

    def _refrescar_estimaciones(self):
        self._actualizar_estimacion("cpu")
        self._actualizar_estimacion("gpu")

    def _actualizar_estimacion(self, bloque: str):
        """Lanza el cálculo de la estimación de la moneda seleccionada en un
        hilo de fondo (la consulta de red puede tardar). El resultado se
        recoge en _procesar_cola_est."""
        combo, mapa, lbl = self._widgets_estimacion(bloque)
        simbolo = self._simbolo_combo(combo, mapa)
        if not simbolo:
            lbl.configure(text="")
            return
        lbl.configure(text="Calculando…")

        def trabajo(s=simbolo, b=bloque):
            try:
                est = estimacion_ingreso.estimar_referencia(s)
            except Exception:
                est = None  # nunca dejar caer la app por la estimación
            self.cola_est.put((b, s, est))

        threading.Thread(target=trabajo, daemon=True).start()

    def _procesar_cola_est(self):
        if not self._est_activo:
            return
        try:
            while True:
                bloque, simbolo, est = self.cola_est.get_nowait()
                combo, mapa, lbl = self._widgets_estimacion(bloque)
                # Solo aplicamos el resultado si la moneda sigue siendo la
                # que se pidió (el usuario pudo cambiar de selección mientras
                # se consultaba la red).
                if self._simbolo_combo(combo, mapa) == simbolo:
                    lbl.configure(text=texto_estimacion(est))
        except queue.Empty:
            pass
        self.after(150, self._procesar_cola_est)

    def _reanalizar(self):
        self._detectar()
        self._mostrar_resumen_hardware()
        self._rellenar_combos()
        self._on_toggle()
        self._refrescar_estimaciones()

    def _on_toggle(self):
        cpu_on = self.cpu_activa.get()
        self.combo_cpu.configure(state=("readonly" if cpu_on else "disabled"))
        self.entry_wallet_cpu.configure(state=("normal" if cpu_on else "disabled"))
        # Mientras el campo estaba deshabilitado, cualquier intento de
        # autorrellenarlo (al abrir la app, o al cambiar de moneda antes
        # de marcar la casilla) no hacía nada: un Entry deshabilitado
        # ignora insert()/delete(). En cuanto se habilita, si sigue vacío,
        # lo intentamos otra vez ahora que sí puede recibir texto.
        if cpu_on and not self.entry_wallet_cpu.get():
            self._ultima_moneda_cpu = None
            self._autorrellenar_wallet_si_cambio(
                "cpu", self.combo_cpu, self._opciones_cpu_por_etiqueta, self.entry_wallet_cpu
            )

        hay_gpu = bool(self.opciones_gpu)
        gpu_on = self.gpu_activa.get() and hay_gpu
        self.combo_gpu.configure(state=("readonly" if gpu_on else "disabled"))
        self.entry_wallet_gpu.configure(state=("normal" if gpu_on else "disabled"))
        if gpu_on and not self.entry_wallet_gpu.get():
            self._ultima_moneda_gpu = None
            self._autorrellenar_wallet_si_cambio(
                "gpu", self.combo_gpu, self._opciones_gpu_por_etiqueta, self.entry_wallet_gpu
            )
        if not hay_gpu:
            self.chk_gpu.state(["disabled"])
        else:
            self.chk_gpu.state(["!disabled"])

        self._actualizar_boton()

    def _actualizar_boton(self):
        habilitado = boton_habilitado(
            self.cpu_activa.get(), self.entry_wallet_cpu.get(),
            self.gpu_activa.get(), self.entry_wallet_gpu.get(),
        )
        if habilitado:
            self.btn_comenzar.state(["!disabled"])
        else:
            self.btn_comenzar.state(["disabled"])

    def _simbolo_combo(self, combo, mapa) -> str | None:
        opcion = mapa.get(combo.get())
        return opcion.simbolo if opcion else None

    # ---- arranque del minado ----

    def _comenzar(self):
        cpu_simbolo = self._simbolo_combo(self.combo_cpu, self._opciones_cpu_por_etiqueta)
        gpu_simbolo = self._simbolo_combo(self.combo_gpu, self._opciones_gpu_por_etiqueta)
        cpu, gpu = construir_bloques_config(
            self.cpu_activa.get(), cpu_simbolo, self.entry_wallet_cpu.get(),
            self.gpu_activa.get(), gpu_simbolo, self.entry_wallet_gpu.get(),
        )
        if cpu is None and gpu is None:
            return

        ruta_config = RAIZ_PROYECTO / "config.md"
        guardar_config(ruta_config, date.today().isoformat(), cpu, gpu)

        self._construir_logs(cpu, gpu)
        self._lanzar_minado(cpu, gpu)

    def _construir_logs(self, cpu, gpu):
        # Dejamos de sondear estimaciones: la pantalla de configuración (con
        # sus etiquetas) va a desaparecer.
        self._est_activo = False
        if self.frame_config is not None:
            self.frame_config.destroy()
            self.frame_config = None

        # Info del bloque activo (símbolo, motor, estimación base) para
        # poder reescalar al hashrate real según van llegando líneas de
        # log. Se rellena desde _lanzar_minado vía la cola.
        self.info_bloque_activo: dict = {}
        self.lbl_real_cpu = None
        self.lbl_real_gpu = None

        self.frame_logs = ttk.Frame(self, padding=16)
        self.frame_logs.pack(fill="both", expand=True)
        marco = self.frame_logs

        ttk.Label(marco, text="Minado en marcha", font=("", 12, "bold")).pack(anchor="w")

        # Ingreso estimado con el hashrate REAL (fijado arriba, se actualiza
        # solo según llegan lecturas del motor de minado).
        if cpu is not None:
            self.lbl_real_cpu = ttk.Label(
                marco, text=texto_ingreso_real(cpu["simbolo"], True),
                foreground="#0a7a3f", wraplength=620, justify="left",
            )
            self.lbl_real_cpu.pack(anchor="w", pady=(4, 0))
        if gpu is not None:
            self.lbl_real_gpu = ttk.Label(
                marco, text=texto_ingreso_real(gpu["simbolo"], True),
                foreground="#0a7a3f", wraplength=620, justify="left",
            )
            self.lbl_real_gpu.pack(anchor="w", pady=(2, 6))

        self.ver_completo = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            marco, text="Ver log técnico completo", variable=self.ver_completo,
        ).pack(anchor="w", pady=(4, 6))

        contenedor = ttk.Frame(marco)
        contenedor.pack(fill="both", expand=True)
        self.txt_log = tk.Text(contenedor, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(contenedor, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.txt_log.pack(side="left", fill="both", expand=True)

        botones = ttk.Frame(marco)
        botones.pack(anchor="w", pady=(8, 0))
        ttk.Button(botones, text="Detener minado", command=self._detener).pack(side="left")
        ttk.Button(botones, text="Volver a la configuración", command=self._volver).pack(side="left", padx=8)

        self._bucle_activo = True
        self.after(200, self._procesar_cola)

    def _lanzar_minado(self, cpu, gpu):
        fabricante = self._fabricante_gpu()

        def trabajo():
            bloques = []
            if cpu is not None:
                bloques.append(("cpu", cpu, None))
            if gpu is not None:
                bloques.append(("gpu", gpu, fabricante))

            for bloque, datos, fab in bloques:
                simbolo = minar.resolver_moneda(datos["simbolo"])
                if simbolo is None or simbolo not in MONEDAS_SOPORTADAS:
                    self.cola.put((
                        "progreso", bloque,
                        f"La moneda {datos['simbolo']} todavía no se puede minar "
                        "automáticamente. Se guardó la configuración, pero no se arranca.",
                    ))
                    continue
                info = MONEDAS_SOPORTADAS[simbolo]
                nombre_motor = info["motor"]

                # Base para reescalar al hashrate real más adelante (puede
                # ser None si esta moneda no tiene fuente de datos
                # verificada — ver estimacion_ingreso.py). Una sola consulta
                # de red por bloque, al arrancar; el reescalado según llegan
                # líneas de log es aritmética local, sin más peticiones.
                estimacion_base = estimacion_ingreso.estimar_referencia(simbolo)
                self.cola.put(("info_bloque", bloque, (simbolo, nombre_motor, estimacion_base)))

                try:
                    bin_path = instalador.asegurar_motor(
                        nombre_motor, RAIZ_PROYECTO, fabricante_gpu=fab,
                        on_progreso=lambda m, b=bloque: self.cola.put(("progreso", b, m)),
                    )
                except instalador.InstaladorError as e:
                    self.cola.put(("progreso", bloque, f"Error preparando el motor: {e}"))
                    continue
                except Exception as e:  # nunca dejar caer la app
                    self.cola.put(("progreso", bloque, f"Error inesperado: {e}"))
                    continue

                try:
                    sesion = minar.iniciar_minado(
                        bloque, info, datos["wallet"], {}, RAIZ_PROYECTO, bin_path,
                        dry_run=False,
                        on_linea=lambda b, linea: self.cola.put(("linea", b, linea)),
                    )
                except PermissionError as e:
                    self.cola.put((
                        "progreso", bloque,
                        f"No se pudo arrancar el motor de minado (permiso denegado: {e}). "
                        "Es muy probable que el antivirus (Windows Defender u otro) haya "
                        "bloqueado o puesto en cuarentena el programa recién descargado — "
                        "es habitual, porque los antivirus marcan los mineros como "
                        "sospechosos aunque sean legítimos. Añade una excepción para la "
                        "carpeta 'bin' de este proyecto en tu antivirus y vuelve a "
                        "intentarlo.",
                    ))
                    continue
                except OSError as e:
                    self.cola.put(("progreso", bloque, f"No se pudo arrancar el motor de minado: {e}"))
                    continue
                if sesion is not None:
                    self.cola.put(("sesion", sesion, None))

        threading.Thread(target=trabajo, daemon=True).start()

    def _procesar_cola(self):
        if not self._bucle_activo:
            return
        try:
            while True:
                tipo, a, b = self.cola.get_nowait()
                if tipo == "sesion":
                    self.sesiones.append(a)
                elif tipo == "progreso":
                    self._anexar(f"[{a.upper()}] {b}")
                elif tipo == "info_bloque":
                    bloque = a
                    simbolo, nombre_motor, estimacion_base = b
                    self.info_bloque_activo[bloque] = {
                        "simbolo": simbolo, "motor": nombre_motor, "base": estimacion_base,
                    }
                    self._actualizar_lbl_real(bloque, texto_ingreso_real(simbolo, estimacion_base is not None))
                elif tipo == "linea":
                    bloque, cruda = a, b
                    interpretada = minar.interpretar_linea(cruda)
                    self.log_lineas.append((bloque, cruda, interpretada))
                    if self.ver_completo.get():
                        self._anexar(f"[{bloque.upper()}] {cruda}")
                    elif interpretada is not None:
                        self._anexar(f"[{bloque.upper()}] {interpretada}")
                    self._procesar_hashrate_real(bloque, cruda)
        except queue.Empty:
            pass
        self.after(200, self._procesar_cola)

    def _procesar_hashrate_real(self, bloque: str, linea_cruda: str) -> None:
        info = self.info_bloque_activo.get(bloque)
        if info is None or info["base"] is None:
            return
        resultado = minar.extraer_hashrate_real(linea_cruda, info["motor"])
        if resultado is None:
            return
        hz, texto_hr = resultado
        moneda_h, usd_h = estimacion_ingreso.escalar_a_hashrate(info["base"], hz)
        self._actualizar_lbl_real(
            bloque, texto_ingreso_real(info["simbolo"], True, texto_hr, moneda_h, usd_h)
        )

    def _actualizar_lbl_real(self, bloque: str, texto: str) -> None:
        lbl = self.lbl_real_cpu if bloque == "cpu" else self.lbl_real_gpu
        if lbl is not None:
            lbl.configure(text=texto)

    def _anexar(self, texto: str):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", texto + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _detener(self):
        for sesion in list(self.sesiones):
            try:
                sesion.detener()
            except Exception:
                pass
        self.sesiones = []
        self._anexar("Minado detenido.")
        self._preguntar_reactivar_aislamiento()

    def _volver(self):
        self._detener()
        self._bucle_activo = False
        self.log_lineas = []
        if self.frame_logs is not None:
            self.frame_logs.destroy()
            self.frame_logs = None
        self._detectar()
        self._construir_config()

    def _preguntar_reactivar_aislamiento(self):
        """Si esta misma app desactivó "Aislamiento del núcleo /
        Integridad de memoria" para minar más rápido (ver
        src/comprobar_aislamiento.py), pregunta ahora si se quiere
        volver a activar. No hace nada si nunca se desactivó desde
        aquí."""
        if not aislamiento_nucleo.RUTA_MARCA.exists():
            return
        quiere_reactivar = messagebox.askyesno(
            "Aislamiento del núcleo",
            "Desactivaste la protección de Windows \"Aislamiento del "
            "núcleo / Integridad de memoria\" para minar más rápido. "
            "¿Quieres volver a activarla ahora? (hace falta reiniciar "
            "el ordenador después para que se aplique)",
        )
        if quiere_reactivar:
            ok, mensaje = aislamiento_nucleo.reactivar()
            if ok:
                aislamiento_nucleo.RUTA_MARCA.unlink(missing_ok=True)
            # No usamos self._anexar aquí: puede que ni siquiera exista el
            # registro de log todavía (por ejemplo, si el usuario cierra
            # la app sin haber llegado a minar). Un aviso aparte siempre
            # funciona, esté donde esté la ventana en ese momento.
            messagebox.showinfo("Aislamiento del núcleo", mensaje)
        # Si dice que no, se deja la marca: se le volverá a preguntar
        # la próxima vez que detenga el minado o cierre la app.

    def _al_cerrar_ventana(self):
        self._preguntar_reactivar_aislamiento()
        self.destroy()


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    app = App()
    app.protocol("WM_DELETE_WINDOW", app._al_cerrar_ventana)
    app.mainloop()


if __name__ == "__main__":
    main()
