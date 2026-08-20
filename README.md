# Minero Cripto

Herramienta personal para iniciar el minado de una criptomoneda escribiendo
solo tu wallet y la moneda en un fichero de texto.

## Uso rápido

1. Instala XMRig (el programa que hace el minado de verdad). Descárgalo
   desde la página oficial del proyecto XMRig y colócalo en tu `PATH`, o
   copia el ejecutable dentro de la carpeta `bin/` de este proyecto.
2. Copia `config.example.md` como `config.md` y rellena tu wallet y la
   moneda (por ahora: `XMR`).
3. Ejecuta:

   ```
   python3 src/minar.py
   ```

   Para comprobar qué haría sin minar de verdad:

   ```
   python3 src/minar.py --dry-run
   ```

## Documentación

- `CLAUDE.md`: reglas y comandos para seguir trabajando en este proyecto.
- `docs/DECISIONS.md`: por qué se tomó cada decisión técnica, en lenguaje simple.
- `docs/GLOSSARY.md`: términos técnicos explicados en una línea.
- `docs/CHANGELOG.md`: qué se hizo en cada sesión de trabajo.
