#!/usr/bin/env python3
"""
Formulario gráfico muy básico que:
1. Analiza el hardware del ordenador (CPU y tarjeta gráfica).
2. Muestra qué criptomonedas se pueden minar técnicamente con ese hardware.
3. Deja preseleccionada la de mayor ingreso estimado (no la más rentable:
   no sabemos el coste de tu luz, así que no calculamos beneficio).
4. Al pulsar "Guardar configuración", escribe config.md con tu wallet y
   la moneda elegida, listo para usar con `python3 src/minar.py`.

Este fichero necesita una pantalla (no funciona en un servidor sin
interfaz gráfica). Se ejecuta con:

    python3 src/formulario.py
"""

import sys
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk

from hardware import InfoGPU, detectar_cpu, detectar_gpus
from config_writer import guardar_config
from recomendador import recomendar

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


def _etiqueta_opcion(opcion) -> str:
    if not opcion.soportado_por_minar_hoy:
        icono = "🚧"  # todavía no implementado en minar.py
    elif opcion.confirmado_en_hardware_real:
        icono = "✅"  # implementado y probado en este tipo de hardware
    else:
        icono = "🧪"  # implementado pero sin confirmar en una GPU real
    return f"{icono} [{opcion.tipo.upper()}] {opcion.nombre} ({opcion.simbolo}) — {opcion.algoritmo}"


class Formulario(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Configurar minado")
        self.geometry("560x540")
        self.resizable(False, False)

        self.gpu_manual_vram = tk.DoubleVar(value=0)
        self.gpu_manual_activa = tk.BooleanVar(value=False)

        self._construir_layout()
        self._analizar_y_mostrar()

    def _construir_layout(self):
        marco = ttk.Frame(self, padding=16)
        marco.pack(fill="both", expand=True)

        ttk.Label(marco, text="Hardware detectado", font=("", 12, "bold")).pack(anchor="w")
        self.txt_hardware = tk.Text(marco, height=5, width=64, state="disabled", wrap="word")
        self.txt_hardware.pack(anchor="w", pady=(2, 8))

        self.marco_manual = ttk.Frame(marco)
        self.chk_manual = ttk.Checkbutton(
            self.marco_manual,
            text="No se detectó bien mi GPU: tengo una tarjeta dedicada con al menos (GB):",
            variable=self.gpu_manual_activa,
            command=self._analizar_y_mostrar,
        )
        self.chk_manual.pack(side="left")
        self.spin_manual = ttk.Spinbox(
            self.marco_manual, from_=1, to=48, textvariable=self.gpu_manual_vram, width=5,
            command=self._analizar_y_mostrar,
        )
        self.spin_manual.pack(side="left", padx=6)
        self.marco_manual.pack(anchor="w", pady=(0, 8))

        ttk.Label(
            marco,
            text=(
                "Estas son las monedas que tu hardware puede minar por motivos\n"
                "técnicos. No es un juicio de rentabilidad: eso depende del precio\n"
                "de la moneda y del coste de tu luz, que aquí no calculamos."
            ),
            foreground="#555555",
        ).pack(anchor="w", pady=(4, 8))

        ttk.Label(marco, text="Moneda a minar", font=("", 12, "bold")).pack(anchor="w")
        self.combo_monedas = ttk.Combobox(marco, state="readonly", width=64)
        self.combo_monedas.pack(anchor="w", pady=(2, 4))
        self.combo_monedas.bind("<<ComboboxSelected>>", lambda e: self._actualizar_avisos())

        ttk.Label(
            marco,
            text="✅ lista y probada en este tipo de hardware   🧪 lista pero sin confirmar en GPU real   🚧 aún no implementada",
            foreground="#555555", wraplength=520, justify="left",
        ).pack(anchor="w", pady=(2, 6))

        self.lbl_aviso_soporte = ttk.Label(marco, foreground="#b45309", wraplength=520, justify="left")
        self.lbl_aviso_soporte.pack(anchor="w", pady=(0, 4))
        self.lbl_aviso_comision = ttk.Label(marco, foreground="#555555", wraplength=520, justify="left")
        self.lbl_aviso_comision.pack(anchor="w", pady=(0, 4))
        self.lbl_aviso_riesgo = ttk.Label(marco, foreground="#b91c1c", wraplength=520, justify="left")
        self.lbl_aviso_riesgo.pack(anchor="w", pady=(0, 8))

        ttk.Label(marco, text="Tu wallet", font=("", 12, "bold")).pack(anchor="w")
        self.entry_wallet = ttk.Entry(marco, width=64)
        self.entry_wallet.pack(anchor="w", pady=(2, 12))

        ttk.Button(marco, text="Guardar configuración", command=self._guardar).pack(anchor="w")
        self.lbl_estado = ttk.Label(marco, foreground="#166534")
        self.lbl_estado.pack(anchor="w", pady=(8, 0))

    def _analizar_y_mostrar(self):
        self.cpu = detectar_cpu()
        self.gpus = detectar_gpus()

        if self.gpu_manual_activa.get() and self.gpu_manual_vram.get() > 0:
            self.gpus = [InfoGPU(modelo="(indicada manualmente)", vram_gb=self.gpu_manual_vram.get(), fabricante="Desconocido")]

        self.opciones, self.recomendado = recomendar(self.cpu, self.gpus)

        self._mostrar_resumen_hardware()
        self._mostrar_monedas()

    def _mostrar_resumen_hardware(self):
        self.txt_hardware.configure(state="normal")
        self.txt_hardware.delete("1.0", "end")
        lineas = [f"CPU: {self.cpu.modelo} ({self.cpu.nucleos_logicos} núcleos lógicos)"]
        if self.gpus:
            for g in self.gpus:
                vram_txt = f"{g.vram_gb} GB" if g.vram_gb is not None else "VRAM desconocida"
                lineas.append(f"GPU: {g.modelo} — {vram_txt} ({g.fabricante})")
        else:
            lineas.append("GPU: no se detectó ninguna tarjeta gráfica dedicada automáticamente.")
        self.txt_hardware.insert("1.0", "\n".join(lineas))
        self.txt_hardware.configure(state="disabled")

    def _mostrar_monedas(self):
        etiquetas = [_etiqueta_opcion(o) for o in self.opciones]
        self.combo_monedas["values"] = etiquetas
        self._opciones_por_etiqueta = dict(zip(etiquetas, self.opciones))

        if self.recomendado:
            recomendado_obj = next(o for o in self.opciones if o.simbolo == self.recomendado)
            self.combo_monedas.set(_etiqueta_opcion(recomendado_obj))
        elif etiquetas:
            self.combo_monedas.current(0)
        else:
            self.combo_monedas.set("")
        self._actualizar_avisos()

    def _opcion_seleccionada(self):
        return self._opciones_por_etiqueta.get(self.combo_monedas.get())

    def _actualizar_avisos(self):
        opcion = self._opcion_seleccionada()
        if opcion is None:
            self.lbl_aviso_soporte.configure(text="")
            self.lbl_aviso_comision.configure(text="")
            self.lbl_aviso_riesgo.configure(text="")
            return

        if not opcion.soportado_por_minar_hoy:
            self.lbl_aviso_soporte.configure(
                text="🚧 minar.py aún no sabe arrancar esta moneda automáticamente. "
                "El fichero se generará igual; pide que se añada soporte cuando quieras usarla."
            )
        elif not opcion.confirmado_en_hardware_real:
            self.lbl_aviso_soporte.configure(
                text="🧪 El comando ya está implementado y probado con un ejecutable de "
                "prueba, pero nunca se ha ejecutado contra una tarjeta gráfica real "
                "(se hizo en un entorno sin GPU). Pruébalo tú y cuenta qué tal."
            )
        else:
            self.lbl_aviso_soporte.configure(text="")

        if opcion.comision_pct is not None:
            texto_comision = (
                "sin comisión (motor de código abierto)"
                if opcion.comision_pct == 0
                else f"comisión del motor de minado: {opcion.comision_pct}%"
            )
            self.lbl_aviso_comision.configure(text=texto_comision)
        else:
            self.lbl_aviso_comision.configure(text="")

        self.lbl_aviso_riesgo.configure(text=f"⚠ {opcion.riesgo}" if opcion.riesgo else "")

    def _guardar(self):
        opcion = self._opcion_seleccionada()
        wallet = self.entry_wallet.get().strip()

        if opcion is None:
            messagebox.showerror("Falta información", "No hay ninguna moneda seleccionada.")
            return
        if not wallet:
            messagebox.showerror("Falta información", "Escribe tu wallet antes de guardar.")
            return

        ruta_config = RAIZ_PROYECTO / "config.md"
        guardar_config(ruta_config, wallet, opcion.simbolo, date.today().isoformat())
        self.lbl_estado.configure(text=f"Guardado en {ruta_config}")


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    app = Formulario()
    app.mainloop()


if __name__ == "__main__":
    main()
