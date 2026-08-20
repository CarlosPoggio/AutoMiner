# CLAUDE.md — Guía para trabajar en este repositorio

Carlos (el dueño de este proyecto) no es técnico. No le pidas decisiones de
arquitectura, herramientas o estructura: decídelas tú, explícalas en una
frase sencilla y regístralas en `docs/DECISIONS.md`.

## Qué es este proyecto

Herramienta personal para iniciar el minado de criptomonedas (uso propio,
con su propia wallet y su propio ordenador). Un fichero de texto
(`config.md`) guarda la wallet y la moneda; el script `src/minar.py` lee
ese fichero y arranca el motor de minado correcto con esos datos.
`src/formulario.py` es una ventana muy sencilla (Tkinter) que analiza el
hardware del ordenador, muestra qué monedas se pueden minar con él y
genera `config.md` por ti.

Módulos en `src/`: `hardware.py` (detecta CPU/GPU), `monedas.py`
(catálogo de monedas de CPU y GPU, con su comisión y si están
implementadas), `motores.py` (sabe encontrar y arrancar cada programa de
minado: xmrig, kawpowminer, lolMiner), `ingresos.py` (ranking de
ingresos, en vivo o de reserva), `recomendador.py` (junta hardware +
catálogo + ingresos), `config_writer.py` (escribe `config.md`),
`formulario.py` (la ventana), `minar.py` (arranca el minado de verdad).

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
- Abrir el formulario gráfico (rellena config.md por ti): `python3 src/formulario.py`
  — necesita una pantalla; en Linux puede hacer falta instalar el paquete
  del sistema `python3-tk` si no abre.
- Comprobar el script de minado sin minar de verdad: `python3 src/minar.py --dry-run`
- Ejecutar el minado de verdad (requiere XMRig instalado): `python3 src/minar.py`

No hay dependencias externas de Python (todo usa la librería estándar,
incluyendo Tkinter y la consulta de ingresos por internet) para que
Carlos no tenga que instalar nada complicado. Si en el futuro hace falta
una librería de verdad, añádela a un `requirements.txt` y explica por qué
en `docs/DECISIONS.md`.

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
