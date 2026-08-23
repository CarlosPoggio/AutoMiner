# CLAUDE.md — Guía para trabajar en este repositorio

Carlos (el dueño de este proyecto) no es técnico. No le pidas decisiones de
arquitectura, herramientas o estructura: decídelas tú, explícalas en una
frase sencilla y regístralas en `docs/DECISIONS.md`.

## Qué es este proyecto

Herramienta personal para minar criptomonedas (uso propio, con su propia
wallet y su propio ordenador), pensada para alguien que no sabe nada de
técnica: `src/formulario.py` es una única ventana (Tkinter) que analiza
el hardware, deja elegir moneda y wallet por separado para CPU y para
GPU, y al pulsar "Comenzar a minar" hace todo el trabajo sola —
instala el motor de minado que falte (descargándolo de su release
oficial en GitHub, ver `src/instalador.py`) y arranca a minar,
mostrando un registro en vivo traducido a lenguaje sencillo. Un fichero
de texto (`config.md`, formato dual `cpu_moneda`/`cpu_wallet`/
`gpu_moneda`/`gpu_wallet`, ambos bloques opcionales) guarda lo elegido;
`src/minar.py` también se puede usar solo, sin el formulario, leyendo
ese fichero.

Módulos en `src/`: `hardware.py` (detecta CPU/GPU), `monedas.py`
(catálogo de monedas de CPU y GPU, con su comisión y si están
implementadas), `motores.py` (sabe encontrar cada programa de minado —
xmrig, kawpowminer, lolMiner — y construir su comando), `instalador.py`
(si un motor no está instalado, lo descarga solo desde su release
oficial de GitHub y lo deja listo en `bin/`), `ingresos.py` (ranking de
ingresos, en vivo o de reserva), `recomendador.py` (junta hardware +
catálogo + ingresos; `recomendar_cpu`/`recomendar_gpu` separan las
opciones de cada componente), `config_writer.py` (escribe `config.md`
en formato dual), `wallets_defecto.py` (lee `wallets.md`, ver más abajo),
`estimacion_ingreso.py` (calcula, con datos reales de dificultad de red
y precio, cuánto se ganaría por hora a una velocidad de minado de
referencia fija — no el hardware real del usuario, ver docstring del
propio fichero para qué monedas tienen fuente verificada hoy y cuáles
no), `formulario.py` (la ventana: solo muestra monedas ya minables, con
la de mayor ingreso preseleccionada, la wallet rellenada sola si está
en `wallets.md`, y la estimación de `estimacion_ingreso.py` bajo cada
desplegable; configuración + arranque + logs, todo en una sola app),
`minar.py` (parsea/valida `config.md`, sabe arrancar CPU y GPU a la vez
como procesos concurrentes, e interpreta su salida en
`interpretar_linea`).

`wallets.md` (en la raíz del repo) guarda las wallets por defecto de
Carlos, una por moneda (`SIMBOLO: direccion`). A diferencia de
`config.md`, **este fichero SÍ se sube a git**: una dirección de wallet
es la que recibe el dinero, así que es pública por diseño (no es una
clave privada). Si se toca este fichero, nunca hay que escribir en él
una clave privada o frase semilla real.

Monedas soportadas hoy por `minar.py` (ver tabla completa en README.md):
XMR, WOW, ZEPH, SAL, RTM (CPU, motor xmrig) y RVN, KAS, ALPH (GPU,
motores kawpowminer/lolMiner). Las de GPU están implementadas y con
tests, pero **nunca probadas contra una GPU real** (este entorno no
tiene ninguna) — están marcadas como tal en `monedas.py`
(`tipo == "gpu"` + `soportado_por_minar_hoy == True` implica "sin
confirmar" por convención) y en la interfaz del formulario (icono 🧪).
Añadir una moneda nueva que ya use un motor existente (mismo xmrig,
kawpowminer o lolMiner) es sencillo; añadir una que necesite un motor
distinto implica registrarlo primero en `motores.py`, investigando pool,
formato de comando y comisión con fuentes fiables (ver
`docs/DECISIONS.md` para el patrón a seguir).

## Comandos

- Ejecutar tests: `python3 -m unittest discover -s tests -v`
- Abrir la app (analiza, deja elegir y arranca a minar de verdad):
  `python3 src/formulario.py` — necesita una pantalla; en Linux puede
  hacer falta instalar el paquete del sistema `python3-tk` si no abre.
  **Ojo: a diferencia de antes, el botón "Comenzar a minar" sí conecta
  con un pool real y mina de verdad** (e instala el motor que falte).
- Comprobar el script de minado sin minar de verdad: `python3 src/minar.py --dry-run`
- Ejecutar el minado de verdad sin el formulario (con `config.md` ya
  escrito a mano o generado antes): `python3 src/minar.py` — si falta
  el motor de minado, lo descarga solo (ver `src/instalador.py`).

No hay dependencias externas de Python (todo usa la librería estándar,
incluyendo Tkinter, la consulta de ingresos por internet y la descarga
automática de motores con `urllib`) para que Carlos no tenga que
instalar nada complicado. Si en el futuro hace falta una librería de
verdad, añádela a un `requirements.txt` y explica por qué en
`docs/DECISIONS.md`.

Este entorno de sesión en la nube no tiene pantalla ni el paquete gráfico
de Tkinter instalado, y no se puede instalar (la red está limitada). Por
eso `formulario.py` no se puede ejecutar ni probar visualmente aquí: solo
su lógica interna (con tests). Si se toca ese fichero, verifica con tests
y `py_compile`, y pide al usuario una captura de pantalla o confirmación
cuando lo pruebe en su propio ordenador.

## Reglas importantes

- **Nunca subas `config.md` a git** (contiene la wallet real). Ya está en
  `.gitignore`; no lo quites. Usa `config.example.md` como plantilla.
- **No ejecutes minado real dentro de este entorno de sesión en la nube.**
  Este entorno es un espacio de trabajo compartido de Anthropic; usarlo
  para minar de verdad sería un mal uso de ese recurso. Verifica el
  código con `--dry-run` o con un ejecutable de prueba (ver
  `docs/DECISIONS.md`), nunca conectándote a un pool real desde aquí.
- Antes de tocar código, lee este fichero y los `docs/` relevantes.
- Si el cambio no es trivial, explica el plan en lenguaje simple (qué vas
  a hacer, qué archivos toca, qué alternativas descartaste) y espera
  confirmación si la decisión es importante o difícil de deshacer.
- Verifica siempre antes de dar algo por terminado: corre los tests y, si
  aplica, una comprobación manual (`--dry-run` o similar). Muestra el
  resultado, no solo la afirmación de que "ya está".
- Actualiza `docs/DECISIONS.md`, `docs/GLOSSARY.md` y `docs/CHANGELOG.md`
  cuando el cambio lo justifique.
- Termina con un commit descriptivo.
- No añadas skills, subagentes, hooks ni conexiones MCP salvo que ya sean
  claramente necesarios para lo pedido. Si en algún momento hace falta
  uno, explica en una frase qué vas a crear y por qué antes de hacerlo.
