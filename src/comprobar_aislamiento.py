#!/usr/bin/env python3
"""
Punto de entrada de línea de comandos que llama "Iniciar minado
(rendimiento máximo).bat", ya elevado a administrador, justo antes de
abrir la app. Si "Aislamiento del núcleo / Integridad de memoria" está
activo, pregunta si se quiere desactivar para desbloquear el MSR mod de
xmrig (ver src/aislamiento_nucleo.py y docs/DECISIONS.md).

Códigos de salida (los usa el .bat para decidir si sigue o no):
- 0: todo normal, seguir y abrir la app (ya estaba desactivado, no se
     pudo saber, o el usuario ha dicho que no).
- 2: se acaba de desactivar; hace falta reiniciar el ordenador antes de
     minar con el MSR mod, así que el .bat NO debe abrir la app todavía.
"""

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aislamiento_nucleo  # noqa: E402


def main() -> int:
    activo = aislamiento_nucleo.esta_activo()
    if not activo:
        return 0  # ya está desactivado, o no se pudo saber: seguir sin más

    raiz = tk.Tk()
    raiz.withdraw()
    quiere_desactivar = messagebox.askyesno(
        "Modo rendimiento — Windows",
        "Windows tiene activada la protección \"Aislamiento del núcleo / "
        "Integridad de memoria\". Es una protección de seguridad real "
        "(no un simple ajuste de rendimiento), y bloquea una optimización "
        "de xmrig (el MSR mod, ~5-10% más rápido en Monero y monedas "
        "similares).\n\n"
        "¿Quieres desactivarla ahora para minar más rápido? Podrás volver "
        "a activarla cuando quieras (te lo preguntará la app al detener "
        "el minado o al cerrarla). Hace falta reiniciar el ordenador "
        "después de este cambio.",
    )
    raiz.destroy()

    if not quiere_desactivar:
        return 0

    ok, mensaje = aislamiento_nucleo.desactivar()
    if not ok:
        print(f"[AVISO] {mensaje}")
        return 0

    aislamiento_nucleo.RUTA_MARCA.parent.mkdir(parents=True, exist_ok=True)
    aislamiento_nucleo.RUTA_MARCA.write_text(
        "La app desactivó Aislamiento del núcleo / Integridad de memoria "
        "para minar más rápido. Se puede volver a activar desde la propia "
        "app (al detener el minado o al cerrarla) o a mano en Seguridad "
        "de Windows.",
        encoding="utf-8",
    )

    raiz = tk.Tk()
    raiz.withdraw()
    messagebox.showinfo(
        "Modo rendimiento — Windows",
        "Hecho. Reinicia el ordenador y vuelve a abrir "
        "\"Iniciar minado (rendimiento máximo).bat\" para minar con el "
        "máximo rendimiento.",
    )
    raiz.destroy()
    return 2


if __name__ == "__main__":
    sys.exit(main())
