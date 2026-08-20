# Historial de sesiones

## 2026-08-20 — Formulario gráfico que rellena config.md

- Se investigaron las criptomonedas más habituales de minado con CPU (9,
  ver docs/DECISIONS.md sobre por qué no son 15) y con GPU (15), con su
  algoritmo, requisito aproximado de VRAM y motor de minado necesario.
- Se creó `src/hardware.py`: detecta el modelo de CPU y de GPU (con su
  VRAM cuando es posible) en Windows, Mac y Linux, sin instalar nada.
- Se creó `src/monedas.py`: catálogo de las 24 monedas investigadas.
- Se creó `src/ingresos.py`: consulta ingresos en vivo (whattomine.com)
  para recomendar la moneda de mayor ingreso, con un ranking de reserva
  si no hay conexión.
- Se creó `src/recomendador.py`: filtra qué monedas son técnicamente
  posibles con el hardware detectado y elige la recomendada.
- Se creó `src/config_writer.py` y `src/formulario.py`: una ventana
  (Tkinter) que junta todo lo anterior en un formulario y genera
  `config.md`.
- Se añadieron 18 pruebas automáticas nuevas (42 en total), todas en
  verde, incluyendo la detección real de hardware de este entorno.
- No se pudo mostrar una captura de pantalla del formulario porque este
  entorno de sesión no tiene pantalla ni el paquete gráfico de Tkinter
  instalado (ver docs/DECISIONS.md). Pendiente: que el usuario lo
  ejecute en su ordenador y confirme que la ventana se ve bien.
- Actualizados README.md, CLAUDE.md, docs/DECISIONS.md y docs/GLOSSARY.md.

## 2026-08-20 — Arranque del proyecto

- Se creó el repositorio y su estructura base (`src/`, `docs/`, `tests/`, `bin/`).
- Se construyó `src/minar.py`: lee `config.md` (wallet + moneda), valida los
  datos y arranca XMRig con la configuración correcta.
- Se añadió `config.example.md` como plantilla (la real, `config.md`, nunca
  se sube a git).
- Primera moneda soportada: Monero (XMR).
- Se añadieron 6 pruebas automáticas (`tests/test_minar.py`), todas en verde.
- Se verificó el flujo completo en modo simulación (`--dry-run`) y con un
  ejecutable de prueba, sin conectarse a ningún servidor de minado real.
- Se creó la documentación base: `CLAUDE.md`, `docs/DECISIONS.md`,
  `docs/GLOSSARY.md`, este changelog y `README.md`.
