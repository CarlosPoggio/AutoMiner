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

Módulos en `src/`: `red.py` (el `ssl.SSLContext` compartido para toda
petición HTTPS del proyecto; combina dos capas para esquivar dos fallos
distintos de certificados en Windows que dan el mismo mensaje de
error — ver docstring del fichero y docs/DECISIONS.md entradas 11 y 12:
carga el almacén de certificados de Windows uno a uno, y además usa
`bin/cacert.pem` si `Iniciar minado.bat` lo descargó), `rendimiento_windows.py`
(concede el permiso "huge pages" de Windows al usuario actual, con
`ctypes` sobre las funciones de LSA — necesita administrador, por eso
lo llama `conceder_rendimiento.py` solo desde
`Iniciar minado (rendimiento máximo).bat`, no en el flujo normal, ver
docs/DECISIONS.md entrada 13), `aislamiento_nucleo.py` (lee y cambia
"Aislamiento del núcleo / Integridad de memoria" de Windows — bloquea
el MSR mod de xmrig; nunca se cambia sin preguntar antes, ver
docs/DECISIONS.md entrada 14), `lista_controladores_vulnerables.py`
(lee y cambia la "lista de controladores vulnerables bloqueados" de
Microsoft — otra protección independiente que también bloquea el MSR
mod, porque `WinRing0x64.sys` tiene una CVE real conocida; mismo
cuidado que aislamiento_nucleo.py, nunca se cambia sin preguntar antes,
ver docs/DECISIONS.md entrada 15), `comprobar_seguridad_rendimiento.py`
(el script que pregunta por las dos protecciones anteriores antes de
abrir la app, solo desde el lanzador de rendimiento máximo),
`hardware.py` (detecta CPU/GPU), `monedas.py`
(catálogo de monedas de CPU y GPU, con su comisión y si están
implementadas), `motores.py` (sabe encontrar cada programa de minado —
xmrig, kawpowminer, lolMiner — y construir su comando, incluidos
ficheros acompañantes como `WinRing0x64.sys`), `instalador.py`
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
tests, pero **todavía sin confirmar contra una GPU real** — están
marcadas como tal en `monedas.py` (`tipo == "gpu"` +
`soportado_por_minar_hoy == True` implica "sin confirmar" por
convención, vía `OpcionMoneda.confirmado_en_hardware_real` en
`recomendador.py`, que hoy da por hecho que ninguna GPU está
confirmada) y en la interfaz del formulario (icono 🧪). El ordenador de
Carlos SÍ tiene GPU real (NVIDIA RTX 4060 Laptop, 8GB — detectada por
`hardware.py` en esta misma máquina), así que en cuanto confirme que
alguna de estas tres mina de verdad, hay que actualizar
`confirmado_en_hardware_real` (o el dato correspondiente en
`monedas.py`) para que pase a mostrarse con ✅ en vez de 🧪.
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
  En Windows, `Iniciar minado.bat` hace lo mismo con doble click y, si
  falta Python, lo instala él solo primero: descarga el instalador
  oficial de python.org (versión fijada en el propio `.bat`, variable
  `PY_VERSION`) y lo instala en silencio solo para el usuario actual
  (sin permisos de administrador).
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

Este proyecto se trabaja con Claude Code **en local**, directamente en el
Windows de Carlos (`C:\proyectos\autominer`), con pantalla y red reales
— no es una sesión en la nube sin interfaz. Aun así, no hay forma de ver
la ventana de Tkinter renderizada desde aquí (no hay herramienta de
captura para apps nativas de Windows): verifica `formulario.py` con
tests y `python -m py_compile`, y para la comprobación visual pide a
Carlos que la abra él y describa qué ve, o que te pase una captura de
pantalla (puedes leerla como imagen si te da la ruta del fichero).

## Reglas importantes

- **Nunca subas `config.md` a git** (contiene la wallet real). Ya está en
  `.gitignore`; no lo quites. Usa `config.example.md` como plantilla.
- **No arranques minado real por tu cuenta.** Este proyecto corre en el
  propio ordenador de Carlos (no en un entorno compartido), así que
  técnicamente sí se podría minar de verdad desde aquí — pero conectarse
  a un pool real, gastar electricidad y dejar un proceso corriendo es
  una acción con efectos reales fuera del propio código: solo hazlo si
  Carlos te lo pide explícitamente en ese momento. Para verificar cambios
  de código, por defecto usa `--dry-run` o un ejecutable de prueba (ver
  `docs/DECISIONS.md`).
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
