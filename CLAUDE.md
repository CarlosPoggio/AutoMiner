# CLAUDE.md — Guía para trabajar en este repositorio

Carlos (el dueño de este proyecto) no es técnico. No le pidas decisiones de
arquitectura, herramientas o estructura: decídelas tú, explícalas en una
frase sencilla y regístralas en `docs/DECISIONS.md`.

## Qué es este proyecto

Herramienta personal para iniciar el minado de criptomonedas (uso propio,
con su propia wallet y su propio ordenador). Un fichero de texto
(`config.md`) guarda la wallet y la moneda; el script `src/minar.py` lee
ese fichero y arranca XMRig con esos datos.

## Comandos

- Ejecutar tests: `python3 -m unittest discover -s tests -v`
- Comprobar el script sin minar de verdad: `python3 src/minar.py --dry-run`
- Ejecutar de verdad (requiere XMRig instalado): `python3 src/minar.py`

No hay dependencias externas de Python (todo usa la librería estándar) para
que Carlos no tenga que instalar nada complicado. Si en el futuro hace
falta una librería, añádela a un `requirements.txt` y explica por qué en
`docs/DECISIONS.md`.

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
