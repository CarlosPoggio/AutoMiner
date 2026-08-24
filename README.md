# Minero Cripto

Herramienta personal para minar criptomonedas (CPU y/o GPU) con tu
propia wallet, desde una única ventana: analiza tu ordenador, tú eliges
qué monedas minar y pulsas "Comenzar a minar" — la app se encarga de
todo lo demás, incluido instalar el programa de minado que haga falta.

## Antes de empezar (en tu ordenador, no aquí)

**En Windows no hace falta instalar nada primero.** Descarga este
repositorio y haz doble click en `Iniciar minado.bat`: si no tienes
Python, el propio lanzador lo detecta y lo instala solo (una versión
para tu usuario, sin permisos de administrador, sin que tengas que
tocar nada) antes de abrir la app. Solo hace falta conexión a internet
la primera vez.

En Mac y Linux hace falta **Python 3** (ver `docs/DECISIONS.md`):

- En Mac suele venir de serie.
- En Linux suele venir de serie; si al abrir el formulario da un error
  de Tkinter, instala el paquete del sistema `python3-tk` (por ejemplo
  `sudo apt install python3-tk`).

No hace falta instalar el motor de minado (XMRig, kawpowminer o
lolMiner) a mano: la app lo descarga sola la primera vez que hace
falta, desde la página oficial del proyecto correspondiente en GitHub
(ver `src/instalador.py` y `bin/LEEME.md` si prefieres instalarlo tú).

## Uso

1. En Windows tienes dos accesos directos, en la carpeta principal del
   proyecto — elige el que prefieras cada vez que abras la app:

   - **`Iniciar minado.bat`**: el normal, sin pedir nada especial.
   - **`Iniciar minado (rendimiento máximo).bat`**: pide permiso de
     administrador de Windows (una vez, al abrirlo) para minar más
     rápido con la CPU en Monero y monedas similares (hasta ~25-30%
     más hashrate, según tu hardware). Si Windows tiene activada
     "Aislamiento del núcleo / Integridad de memoria" y/o la "lista de
     controladores vulnerables bloqueados" de Microsoft (protecciones
     de seguridad reales, independientes entre sí, no solo ajustes de
     rendimiento), te preguntará si quieres desactivarlas para ganar
     ese extra — avisando de que la segunda implica asumir una
     vulnerabilidad real y conocida (CVE-2020-14979) del controlador
     que usa el MSR mod. Es tu decisión, y puedes volver a activarlas
     cuando quieras, la propia app te lo pregunta al detener el minado
     o al cerrarla. Si prefieres no dar ese permiso, usa el normal —
     sigue funcionando exactamente igual, solo un poco más despacio en
     esas monedas.

   En Mac/Linux, o si prefieres no usar esos ficheros, ejecuta en una
   terminal:

   ```
   python3 src/formulario.py
   ```

2. Verás tu CPU y tu GPU detectadas, cada una con su propio desplegable
   — solo con las monedas que esta app ya sabe minar de verdad y que tu
   hardware puede minar — con la de mayor ingreso estimado ya
   preseleccionada, y su propio campo de wallet. Marca la casilla de
   CPU y/o de GPU, revisa (o cambia) la moneda y escribe tu wallet en
   cada bloque que quieras usar — puedes minar solo con la CPU, solo
   con la GPU, o con las dos a la vez.

   Si rellenas `wallets.md` (en la raíz del proyecto) con tus
   direcciones por defecto, el campo de wallet se rellena solo al
   elegir esa moneda — puedes cambiarlo a mano si quieres usar otra.
   Bajo cada desplegable verás también una estimación tipo "≈ 0,014
   XMR/hora ≈ 1,20 $/hora": es una referencia calculada con datos
   reales de dificultad de red y precio actual, pero a una velocidad de
   minado fija y redonda (no la de tu hardware exacto) — sirve para
   comparar monedas entre sí, no como una promesa exacta de lo que vas
   a ganar. Wownero y Raptoreum todavía no tienen esta estimación (no
   se encontró una fuente de datos fiable y gratuita para ellas); en
   vez de inventar un número, se muestra "Estimación no
   disponible ahora mismo".
3. Pulsa "Comenzar a minar". La app guarda `config.md`, instala el
   motor que falte si hace falta, y arranca a minar — verás un registro
   en vivo traducido a lenguaje sencillo (conectado al pool, velocidad,
   comparte aceptados...). Hay una casilla para ver el log técnico
   completo si lo necesitas.
4. Para detener el minado, pulsa "Detener minado" en esa misma ventana.

Monedas que ya se pueden minar así hoy (son las únicas que verás en los
desplegables; el resto del catálogo, más de una docena de monedas
investigadas pero sin motor de minado todavía, se queda fuera de la app
para no confundir, hasta que se implementen):

| Moneda | Tipo | Motor | Comisión | Probado con hardware real |
|---|---|---|---|---|
| Monero (XMR) | CPU | XMRig | 1% (ajustable) | ✅ |
| Wownero (WOW) | CPU | XMRig | 1% (ajustable) | ✅ |
| Zephyr (ZEPH) | CPU | XMRig | 1% (ajustable) | ✅ |
| Salvium (SAL) | CPU | XMRig | 1% (ajustable) | ✅ |
| Raptoreum (RTM) | CPU | XMRig | 1% (ajustable) | ✅ |
| Ravencoin (RVN) | GPU | kawpowminer | 0% | 🧪 sin confirmar (ver nota) |
| Alephium (ALPH) | GPU | lolMiner | 0,75% | ✅ (ver nota) |
| Iron Fish (IRON) | GPU | lolMiner | 1% | 🧪 sin confirmar |
| Ergo (ERG) | GPU | lolMiner | 1,5% | 🧪 sin confirmar |
| Beam (BEAM) | GPU | lolMiner | 1% | 🧪 sin confirmar |

"Sin confirmar" significa: el comando que se genera está comprobado
(con un programa de prueba), pero ninguna se ha confirmado minando de
verdad de principio a fin contra un pool real todavía. Pruébalo en tu
ordenador y cuenta qué tal ha ido.

**Iron Fish, Ergo y Beam se añadieron el 2026-08-24** buscando mejores
ingresos reales que RVN/KAS/ALPH (ver `docs/DECISIONS.md` para la
comparación completa, con datos en vivo de whattomine.com). Las tres
usan lolMiner —el mismo motor que ya funciona con ALPH en esta GPU—, así
que no deberían tener el problema de kawpowminer con GPUs NVIDIA
recientes; probadas brevemente en esta máquina (sin wallet real todavía,
solo para comprobar que el motor arranca): las tres detectan la GPU y
calculan sin fallar. Igual que con Ravencoin/Alephium, la clasificación
✅/🧪 no dice nada sobre si compensa económicamente — mira siempre la
estimación de ingreso de la propia app antes de decidir.

**Nota sobre Ravencoin (RVN) en GPUs NVIDIA**: probado de verdad en dos
tarjetas distintas (2026-08-24) y en ninguna de las dos consigue minar
todavía — en una RTX 5060 (Blackwell) falla nada más generar el DAG; en
una RTX 4060 Laptop (Ada Lovelace) genera el DAG bien pero kawpowminer
se cierra solo justo al empezar a minar de verdad. Los dos son fallos
del propio kawpowminer (un programa externo que no controlamos, con un
CUDA interno anticuado para las GPUs NVIDIA actuales), no de esta app;
verás un aviso claro en el registro si te pasa, en vez de quedarse en
silencio. Ver `docs/DECISIONS.md` para el detalle.

**Kaspa (KAS) se quitó de esta lista el 2026-08-24**: lolMiner retiró
el algoritmo que necesitaba (la red de Kaspa está dominada por ASICs
desde 2023-2024, ya no compensa minarla con GPU) — ver
`docs/DECISIONS.md`.

**Nota sobre Alephium (ALPH)**: confirmado minando de verdad (2026-08-24).
La estimación de ingreso ya funciona, pero sé honesto contigo mismo con
el número que te va a salir: la red de Alephium tiene un hashrate
combinado altísimo para un precio muy bajo, así que con una GPU de
consumo el ingreso real es minúsculo hoy (del orden de fracciones de
centavo al día). Funciona, pero no esperes que compense la luz.

Si quieres minar alguna otra moneda del catálogo más amplio (ver
`src/monedas.py`), pide que se añada su motor de minado primero.

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
