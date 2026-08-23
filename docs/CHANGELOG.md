# Historial de sesiones

## 2026-08-23 — App única: elige, instala y mina sin salir de la ventana

- Nuevo `src/instalador.py`: descarga automática del motor de minado
  (xmrig/kawpowminer/lolMiner) desde su release oficial de GitHub
  cuando falta, eligiendo el archivo correcto según sistema operativo
  y, para kawpowminer, según el fabricante de la GPU (NVIDIA vs. resto).
- `src/config_writer.py` y `config.md`/`config.example.md` pasan a un
  formato dual (`cpu_moneda`/`cpu_wallet` y `gpu_moneda`/`gpu_wallet`,
  ambos bloques opcionales, al menos uno obligatorio) en vez de una
  única moneda/wallet global.
- `src/recomendador.py`: nuevas `recomendar_cpu`/`recomendar_gpu` para
  dar opciones y recomendación por separado a cada componente.
- `src/minar.py`: valida cada bloque por separado, sabe arrancar CPU y
  GPU como procesos concurrentes (`SesionMinado`, `iniciar_minado`) y
  traduce la salida cruda de los motores a mensajes en español legibles
  (`interpretar_linea`); el CLI (`--dry-run` incluido) sigue funcionando
  para quien no quiera usar la ventana.
- `src/formulario.py` reescrito por completo: una única ventana con
  bloque de CPU y bloque de GPU independientes (desplegable + wallet
  cada uno), y el botón "Comenzar a minar" ya no solo guarda
  `config.md` — instala lo que falte y arranca a minar de verdad, con
  una vista de registro en vivo (interpretado por defecto, con opción
  de ver el log técnico completo) y botón para detener el minado.
- Se corrigió `.gitignore` (antes solo ignoraba `bin/xmrig`/`xmrig.exe`;
  ahora ignora todo `bin/` salvo `LEEME.md`, para cubrir también
  kawpowminer, lolMiner y las carpetas que crea la descarga automática)
  y se actualizaron `bin/LEEME.md`, `README.md` y `CLAUDE.md` para
  reflejar que ya no hace falta instalar nada a mano.
- Añadidas 87 pruebas en total (antes 71): nuevas `test_instalador.py`
  y `test_formulario_logica.py`, y ampliadas `test_minar.py` y
  `test_hardware_monedas_recomendador.py` para el formato dual, la
  interpretación de logs y el arranque de sesiones (todo con mocks de
  red y de `subprocess`, sin descargar binarios reales ni conectarse a
  ningún pool).
- Pendiente de tu confirmación en tu propio ordenador (aquí no hay
  pantalla ni se puede minar de verdad): que la ventana se vea y
  funcione bien, que la descarga real de un motor funcione la primera
  vez, y que el minado de GPU (RVN/KAS/ALPH, marcadas 🧪) funcione
  contra hardware real.


## 2026-08-20 — 3 monedas de GPU más (Ravencoin, Kaspa, Alephium)

- Se creó `src/motores.py`: un registro que sabe encontrar y arrancar
  distintos programas de minado (antes solo existía para XMRig).
- Se investigaron y añadieron las 3 monedas de GPU con mayor ingreso
  estimado: Ravencoin (motor kawpowminer, código abierto, 0% comisión),
  Kaspa y Alephium (motor lolMiner, 0,75% comisión). Las 3 de CPU con
  mayor ingreso ya estaban hechas de la sesión anterior.
- Se corrigió un dato: XMRig sí tiene una comisión por defecto (1%),
  ajustable con la nueva opción `donate_level` en config.md. Antes el
  catálogo decía que no tenía comisión, lo cual era incorrecto.
- `monedas.py` y el formulario ahora marcan cada moneda con un icono:
  ✅ implementada y probada en ese tipo de hardware, 🧪 implementada
  pero sin confirmar en GPU real, 🚧 todavía sin implementar. El
  fichero `config.md` generado también incluye ese aviso como comentario.
- Se añadieron 11 pruebas nuevas (39 en total), todas en verde, y se
  comprobó a mano el comando exacto que se generaría para las 3 monedas
  nuevas con un ejecutable de prueba (kawpowminer/lolMiner no se pudieron
  probar contra hardware real: este entorno no tiene GPU).
- Actualizados README.md, CLAUDE.md, docs/DECISIONS.md,
  docs/GLOSSARY.md y config.example.md.
- Pendiente (siguiente candidata por ingreso si se quiere seguir):
  Ergo (ERG) en GPU; Dero (DERO) en CPU.

## 2026-08-20 — minar.py ya arranca 5 monedas (no solo Monero)

- Investigados el pool y la variante de algoritmo correctos para
  Wownero (WOW), Zephyr (ZEPH), Salvium (SAL) y Raptoreum (RTM), todas
  minables con el mismo motor ya usado (XMRig).
- Se añadieron las 4 a `src/minar.py` (`MONEDAS_SOPORTADAS`) y se marcó
  `soportado_por_minar_hoy: True` para ellas en `src/monedas.py`.
- Se añadió soporte para argumentos extra por moneda (`extra_args`), que
  usa Raptoreum para conectarse por TLS a su pool.
- Se añadieron 4 pruebas nuevas (28 en total en `tests/test_minar.py` +
  las del formulario), todas en verde, y se comprobó a mano con
  `--dry-run`-style que el comando generado para cada moneda es correcto.
- Quedan pendientes (necesitan un motor de minado distinto a XMRig, y no
  se ha podido probar nada de GPU en este entorno sin tarjeta gráfica):
  Dero, Verus Coin, Xelis, Talecoin y las 15 monedas de GPU. Se abordarán
  una a una cuando el usuario diga cuál quiere usar (ver DECISIONS.md).

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
- Se añadieron 18 pruebas automáticas nuevas (24 en total), todas en
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
