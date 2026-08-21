# Minero Cripto

Herramienta personal para iniciar el minado de una criptomoneda escribiendo
solo tu wallet y la moneda en un fichero de texto.

## Antes de empezar (en tu ordenador, no aquí)

Este repositorio por sí solo no basta para minar: hacen falta dos cosas
más, que no vienen incluidas a propósito (ver `docs/DECISIONS.md`):

1. **Python 3** instalado en tu ordenador. En Mac y Linux suele venir de
   serie; en Windows hay que instalarlo desde python.org (marca la
   casilla "Add to PATH" durante la instalación). En Linux, si al abrir
   el formulario da un error de Tkinter, instala el paquete del sistema
   `python3-tk` (por ejemplo `sudo apt install python3-tk`).
2. **El motor de minado** (XMRig, kawpowminer o lolMiner según la
   moneda — ver tabla más abajo), descargado por separado desde su web
   oficial y colocado en la carpeta `bin/` de este proyecto o en tu PATH.
   Instrucciones en `bin/LEEME.md`.

## Uso rápido

### Opción A: con el formulario (recomendado)

1. Ejecuta `python3 src/formulario.py`. Se abrirá una ventana que analiza
   tu ordenador, te dice qué criptomonedas puedes minar con tu hardware
   y te deja preseleccionada la de mayor ingreso estimado.
2. Escribe tu wallet y pulsa "Guardar configuración". **Esto solo crea
   `config.md`; todavía no empieza a minar.**
3. Para minar de verdad, con el motor ya instalado (paso anterior),
   ejecuta en una terminal, dentro de la carpeta del proyecto:

   ```
   python3 src/minar.py
   ```

   Verás el hashrate subir en pantalla: eso confirma que está minando.
   Para detenerlo, Ctrl+C.

Hoy en día `minar.py` ya sabe arrancar 8 monedas:

| Moneda | Tipo | Motor | Comisión | Probado con hardware real |
|---|---|---|---|---|
| Monero (XMR) | CPU | XMRig | 1% (ajustable) | ✅ |
| Wownero (WOW) | CPU | XMRig | 1% (ajustable) | ✅ |
| Zephyr (ZEPH) | CPU | XMRig | 1% (ajustable) | ✅ |
| Salvium (SAL) | CPU | XMRig | 1% (ajustable) | ✅ |
| Raptoreum (RTM) | CPU | XMRig | 1% (ajustable) | ✅ |
| Ravencoin (RVN) | GPU | kawpowminer | 0% | 🧪 sin confirmar |
| Kaspa (KAS) | GPU | lolMiner | 0,75% | 🧪 sin confirmar |
| Alephium (ALPH) | GPU | lolMiner | 0,75% | 🧪 sin confirmar |

"Sin confirmar" significa: el comando que genera `minar.py` está
comprobado (con un programa de prueba), pero nunca se ha ejecutado
contra una tarjeta gráfica real, porque se desarrolló en un entorno sin
GPU. Pruébalo en tu ordenador y cuenta qué tal ha ido.

Si el formulario recomienda alguna otra moneda de la lista (no incluida
arriba), `config.md` se genera igual, pero tendrás que pedir que se
añada su motor de minado antes de poder arrancarla de verdad.

### Opción B: a mano

1. Instala el motor de minado que necesite tu moneda (ver tabla arriba;
   XMRig, kawpowminer o lolMiner) y colócalo en tu `PATH`, o copia el
   ejecutable dentro de la carpeta `bin/` de este proyecto (ver
   `bin/LEEME.md`).
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
