# Minero Cripto

Herramienta personal para minar criptomonedas (CPU y/o GPU) con tu
propia wallet, desde una única ventana: analiza tu ordenador, tú eliges
qué monedas minar y pulsas "Comenzar a minar" — la app se encarga de
todo lo demás, incluido instalar el programa de minado que haga falta.

## Antes de empezar (en tu ordenador, no aquí)

Solo hace falta **Python 3** instalado (ver `docs/DECISIONS.md`):

- En Mac y Linux suele venir de serie.
- En Windows hay que instalarlo desde python.org (marca la casilla "Add
  to PATH" durante la instalación).
- En Linux, si al abrir el formulario da un error de Tkinter, instala el
  paquete del sistema `python3-tk` (por ejemplo `sudo apt install
  python3-tk`).

No hace falta instalar el motor de minado (XMRig, kawpowminer o
lolMiner) a mano: la app lo descarga sola la primera vez que hace
falta, desde la página oficial del proyecto correspondiente en GitHub
(ver `src/instalador.py` y `bin/LEEME.md` si prefieres instalarlo tú).

## Uso

1. En Windows, haz doble click en `Iniciar minado.bat` (en la carpeta
   principal del proyecto). En Mac/Linux, o si prefieres no usar ese
   fichero, ejecuta en una terminal:

   ```
   python3 src/formulario.py
   ```

2. Verás tu CPU y tu GPU detectadas, cada una con su propio desplegable
   de monedas (solo las que tu hardware puede minar) y su propio campo
   de wallet. Marca la casilla de CPU y/o de GPU, elige la moneda y
   escribe tu wallet en cada bloque que quieras usar — puedes minar solo
   con la CPU, solo con la GPU, o con las dos a la vez.
3. Pulsa "Comenzar a minar". La app guarda `config.md`, instala el
   motor que falte si hace falta, y arranca a minar — verás un registro
   en vivo traducido a lenguaje sencillo (conectado al pool, velocidad,
   comparte aceptados...). Hay una casilla para ver el log técnico
   completo si lo necesitas.
4. Para detener el minado, pulsa "Detener minado" en esa misma ventana.

Monedas que ya se pueden minar así hoy:

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

"Sin confirmar" significa: el comando que se genera está comprobado
(con un programa de prueba), pero nunca se ha ejecutado contra una
tarjeta gráfica real, porque se desarrolló en un entorno sin GPU.
Pruébalo en tu ordenador y cuenta qué tal ha ido.

Si eliges en el desplegable alguna otra moneda del catálogo (marcada
🚧), `config.md` se genera igual, pero la app te avisará de que todavía
no sabe arrancarla de verdad — pide que se añada su motor de minado
cuando quieras usarla.

## Uso avanzado: sin el formulario

Si prefieres no abrir la ventana gráfica, puedes escribir `config.md` a
mano (copia `config.example.md`, ahí se explica el formato) y ejecutar
directamente:

```
python3 src/minar.py
```

o, para comprobar qué haría sin minar de verdad:

```
python3 src/minar.py --dry-run
```

`minar.py` también instala solo el motor que falte, igual que el
formulario.

## Documentación

- `CLAUDE.md`: reglas y comandos para seguir trabajando en este proyecto.
- `docs/DECISIONS.md`: por qué se tomó cada decisión técnica, en lenguaje simple.
- `docs/GLOSSARY.md`: términos técnicos explicados en una línea.
- `docs/CHANGELOG.md`: qué se hizo en cada sesión de trabajo.
