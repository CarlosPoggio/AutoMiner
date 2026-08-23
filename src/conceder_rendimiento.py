#!/usr/bin/env python3
"""
Punto de entrada de línea de comandos para conceder el permiso de
"huge pages" de Windows (ver src/rendimiento_windows.py). Lo llama
"Iniciar minado (rendimiento máximo).bat", ya elevado a administrador,
antes de abrir la app — solo hace falta una vez por ordenador.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rendimiento_windows  # noqa: E402


def main() -> int:
    ok, mensaje = rendimiento_windows.conceder_privilegio_huge_pages()
    print(("[OK] " if ok else "[AVISO] ") + mensaje)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
