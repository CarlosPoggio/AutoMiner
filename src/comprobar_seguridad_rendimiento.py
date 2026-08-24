#!/usr/bin/env python3
"""
Punto de entrada de línea de comandos que llama "Iniciar minado
(rendimiento máximo).bat", ya elevado a administrador, justo antes de
abrir la app. Comprueba las dos protecciones de seguridad de Windows
que pueden bloquear el "MSR mod" de xmrig — "Aislamiento del núcleo /
Integridad de memoria" (ver src/aislamiento_nucleo.py) y la "lista de
controladores vulnerables bloqueados" de Microsoft (ver
src/lista_controladores_vulnerables.py), que son independientes entre
sí y pueden estar bloqueando el MSR mod a la vez — y, si alguna está
activa, pregunta una sola vez (nombrando las que hagan falta) si se
quieren desactivar.

Códigos de salida (los usa el .bat para decidir si sigue o no):
- 0: todo normal, seguir y abrir la app (ya estaba todo desactivado, no
     se pudo saber, o el usuario ha dicho que no).
- 2: se acaba de desactivar algo; hace falta reiniciar el ordenador
     antes de minar con el MSR mod, así que el .bat NO debe abrir la
     app todavía.
"""

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aislamiento_nucleo  # noqa: E402
import lista_controladores_vulnerables  # noqa: E402

_PROTECCIONES = (
    ("Aislamiento del núcleo / Integridad de memoria", aislamiento_nucleo),
    ("Lista de controladores vulnerables bloqueados de Microsoft", lista_controladores_vulnerables),
)


def main() -> int:
    activas = [(nombre, modulo) for nombre, modulo in _PROTECCIONES if modulo.esta_activo()]
    if not activas:
        return 0  # ya está todo desactivado, o no se pudo saber: seguir sin más

    lista_nombres = "\n".join(f"- {nombre}" for nombre, _modulo in activas)
    raiz = tk.Tk()
    raiz.withdraw()
    quiere_desactivar = messagebox.askyesno(
        "Modo rendimiento — Windows",
        "Windows tiene activada esta protección de seguridad:\n\n"
        f"{lista_nombres}\n\n"
        "Son protecciones reales (no simples ajustes de rendimiento) y "
        "bloquean el MSR mod de xmrig. Con huge pages (ya activo) más el "
        "MSR mod minarías en total un 25-30% más rápido que sin ninguna "
        "de las dos optimizaciones, en vez del ~20% que ya tienes solo "
        "con huge pages.\n\n"
        "Desactivar la lista de controladores bloqueados en concreto "
        "significa asumir una vulnerabilidad real y conocida "
        "(CVE-2020-14979) del controlador que usa el MSR mod: un "
        "programa malicioso que se ejecutara en tu cuenta podría "
        "aprovecharla para tomar control total del sistema. Es tu "
        "decisión.\n\n"
        "¿Quieres desactivarlo ahora para minar más rápido? Podrás "
        "volver a activarlo cuando quieras (te lo preguntará la app al "
        "detener el minado o al cerrarla). Hace falta reiniciar el "
        "ordenador después de este cambio.",
    )
    raiz.destroy()

    if not quiere_desactivar:
        return 0

    algo_desactivado = False
    avisos = []
    for nombre, modulo in activas:
        ok, mensaje = modulo.desactivar()
        if ok:
            modulo.RUTA_MARCA.parent.mkdir(parents=True, exist_ok=True)
            modulo.RUTA_MARCA.write_text(
                f"La app desactivó \"{nombre}\" para minar más rápido. Se "
                "puede volver a activar desde la propia app (al detener el "
                "minado o al cerrarla) o a mano en Seguridad de Windows.",
                encoding="utf-8",
            )
            algo_desactivado = True
        else:
            avisos.append(f"{nombre}: {mensaje}")

    raiz = tk.Tk()
    raiz.withdraw()
    if algo_desactivado:
        mensaje_final = (
            "Hecho. Reinicia el ordenador y vuelve a abrir "
            "\"Iniciar minado (rendimiento máximo).bat\" para minar con el "
            "máximo rendimiento."
        )
        if avisos:
            mensaje_final += "\n\nAvisos:\n" + "\n".join(avisos)
        messagebox.showinfo("Modo rendimiento — Windows", mensaje_final)
    else:
        messagebox.showinfo(
            "Modo rendimiento — Windows",
            "No se pudo desactivar ninguna protección:\n\n" + "\n".join(avisos),
        )
    raiz.destroy()

    return 2 if algo_desactivado else 0


if __name__ == "__main__":
    sys.exit(main())
