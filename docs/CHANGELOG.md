# Historial de sesiones

## 2026-08-24 — Segunda causa del MSR mod: la lista de controladores vulnerables bloqueados

- Tras la entrada anterior (Aislamiento del núcleo desactivado y
  reiniciado), el MSR mod seguía fallando. Investigado en vivo en el
  equipo real: `HKLM\SYSTEM\CurrentControlSet\Control\CI\Config\
  VulnerableDriverBlocklistEnable = 1` — la lista de controladores
  vulnerables bloqueados de Microsoft (activa por defecto desde
  Windows 11 2022 Update, independiente de Aislamiento del núcleo)
  bloquea `WinRing0x64.sys` por una CVE real y documentada
  (CVE-2020-14979). Confirmado con KB5020779 de Microsoft.
- Pedido explícito: llegar al máximo rendimiento asumiendo esa
  vulnerabilidad conocida, avisando bien al usuario.
- Nuevo `src/lista_controladores_vulnerables.py`, mismo patrón que
  `aislamiento_nucleo.py` (leer/cambiar con `winreg`, nunca por su
  cuenta).
- `src/comprobar_aislamiento.py` sustituido por
  `src/comprobar_seguridad_rendimiento.py`: comprueba las dos
  protecciones (pueden estar activas a la vez) y hace una sola
  pregunta combinada, con el aviso de la CVE y de la ganancia total
  (~25-30% con huge pages + MSR mod, frente al ~20% de solo huge
  pages).
- `src/formulario.py`: la pregunta de "¿reactivamos?" ahora cubre las
  dos protecciones, cada una si hace falta.
- Añadidas 9 pruebas nuevas (169 en total). Verificado en real: la
  lectura de `lista_controladores_vulnerables.esta_activo()` da `True`,
  igual que el registro comprobado a mano; el cambio de estado solo se
  probó con mocks, no contra el ajuste real.

## 2026-08-23 (14) — Causa real del MSR mod: "Aislamiento del núcleo", con opción de desactivarlo

- Corregido: la entrada anterior decía que la máquina de desarrollo
  "parece una VM" — era un error mío (confundí una etiqueta de xmrig
  sobre virtualización de CPU con estar dentro de una VM). Es un
  ordenador físico real.
- Causa real, comprobada de verdad (`Get-CimInstance Win32_DeviceGuard`
  en la propia máquina): "Aislamiento del núcleo / Integridad de
  memoria" (HVCI) bloquea `WinRing0x64.sys`, el controlador que xmrig
  necesita para el MSR mod. Conflicto conocido con software de minado.
- Nuevo `src/aislamiento_nucleo.py`: lee el estado vía PowerShell sobre
  `Win32_DeviceGuard` y lo cambia vía la clave de registro oficial de
  Microsoft — sin paquetes externos.
- Nuevo `src/comprobar_aislamiento.py`: pregunta (antes de abrir la
  app) si desactivarlo, solo desde el lanzador de rendimiento máximo.
  Si se desactiva, pide reiniciar y no abre la app todavía.
- `src/formulario.py`: pregunta si reactivarlo al detener el minado o
  cerrar la ventana (bug real encontrado y arreglado en el proceso: la
  pregunta podía reventar la app si el registro de log aún no existía;
  ahora usa un aviso aparte).
- No se tocó el ajuste real de Carlos en esta sesión: solo se verificó
  la lectura de estado de verdad; el cambio se probó con mocks.
- Añadidas 15 pruebas nuevas (160 en total). De paso, test de
  regresión endurecido (`test_no_descarga_si_ya_esta_en_bin`: le
  faltaba mockear `shutil.which`, se vio fallar una vez de forma no
  reproducible).

## 2026-08-23 (13) — "Modo rendimiento": segundo acceso directo para minar más rápido (con administrador)

- Arreglado `src/instalador.py`: ahora copia también los "ficheros
  acompañantes" que necesite un motor (nueva clave
  `ficheros_acompanantes` en `src/motores.py`; xmrig necesita
  `WinRing0x64.sys`, antes se quedaba sin copiar). Se autosana también
  en instalaciones que ya tenías, no solo en las nuevas.
- Nuevo `src/rendimiento_windows.py`: concede el permiso "Lock pages
  in memory" (huge pages, hasta ~20% más hashrate en RandomX) al
  usuario actual mediante las funciones de seguridad de Windows con
  `ctypes` (sin `pywin32` ni ningún paquete externo). Solo hace falta
  una vez; verificado de verdad con `secedit /export` en esta máquina,
  no solo que la función no diera error.
- Nuevo `Iniciar minado (rendimiento máximo).bat`: se autoeleva a
  administrador una vez, concede ese permiso y arranca la app —
  como todo el proceso queda elevado, xmrig también puede usar el
  "MSR mod" (que sí necesita admin cada vez que arranca, a diferencia
  de huge pages). `Iniciar minado.bat` normal sigue sin pedir nada.
- `src/formulario.py` muestra arriba si estás en "🚀 Modo rendimiento"
  o en modo normal.
- Añadidas 21 pruebas nuevas (146 en total): `test_rendimiento_windows.py`
  (con la API de Windows simulada, sin tocar la política de seguridad
  real en cada ejecución de los tests) y ampliado `test_instalador.py`.
- `docs/DECISIONS.md` con el detalle completo, incluida una limitación
  conocida: no pude confirmar en esta sesión si el MSR mod llega a
  aplicarse de verdad (esta máquina de desarrollo parece ser una VM,
  donde eso suele estar bloqueado aparte de los permisos).

## 2026-08-23 (12) — Mismo error SSL, causa distinta: almacén de Windows "frío" sin CA públicas

- Diagnosticado (por otra sesión de Claude Code, en un tercer
  ordenador, verificado aquí antes de actuar) que el arreglo de la
  entrada anterior no cubre un caso distinto que da el mismo error:
  Windows rellena las autoridades de certificación públicas BAJO
  DEMANDA (la primera vez que algo con Schannel las necesita); Python
  usa OpenSSL, nunca dispara esa descarga, así que en un equipo donde
  nunca se ha usado un navegador el almacén puede estar casi vacío.
- `Iniciar minado.bat` ahora descarga con `curl` (Schannel, "calienta"
  el almacén de paso) un paquete público de certificados de confianza
  a `bin/cacert.pem` (el mismo que usan Mozilla/`certifi`, fuente
  oficial curl.se/ca/cacert.pem, checksum verificado). No se sube a
  git, ya cubierto por `bin/*`.
- `src/red.py` lo carga como fuente adicional, independiente del
  almacén de Windows. Nuevos tests que cubren fichero ausente, corrupto
  y válido. 134 tests en verde (antes 131).
- `docs/DECISIONS.md` actualizado con el detalle completo.

## 2026-08-23 (11) — "unable to get local issuer certificate" en Windows: fallo conocido de Python, sin paquetes externos

- Nuevo `src/red.py`: `contexto_https()` construye un `ssl.SSLContext`
  cargando los certificados del almacén de Windows uno a uno, en vez de
  todos de golpe — así uno dañado (fallo conocido de Python,
  bugs.python.org/issue26313) no rompe la verificación de TODOS los
  demás. Sin depender de `certifi` ni ningún paquete externo (pip por
  HTTPS tendría el mismo problema).
- Usado en las tres peticiones https del proyecto: `instalador.py`,
  `ingresos.py`, `estimacion_ingreso.py`.
- Nuevo `tests/test_red.py`, con un test que reproduce el fallo
  original (certificado dañado en medio de la lista). 131 tests en
  verde (antes 127).
- `CLAUDE.md` y `docs/DECISIONS.md` actualizados.

## 2026-08-23 (10) — El alias falso de Windows engañaba a la detección de Python

- Confirmado en un Windows real sin Python: `where python` encuentra el
  "alias de ejecución" falso que Windows instala de serie para
  `python.exe` (abre la Microsoft Store o da error), así que el `.bat`
  creía que Python ya estaba instalado y nunca lo descargaba.
- Arreglado: ahora se ejecuta `python --version`/`py --version` de
  verdad y se comprueba que responde, en vez de solo mirar si "algo"
  con ese nombre existe en el PATH. Probado de nuevo con Python real
  instalado (sigue detectándolo bien).
- `docs/DECISIONS.md` actualizado.

## 2026-08-23 (9) — `Iniciar minado.bat` instala Python solo si falta

- El lanzador ya no se limita a avisar si falta Python: si no encuentra
  `py` ni `python`, descarga el instalador oficial de python.org
  (versión fijada `3.13.15`, verificada que el enlace funciona) con
  `curl` (o PowerShell si `curl` no está disponible) y lo instala en
  silencio solo para el usuario actual (`/quiet InstallAllUsers=0`,
  sin admin, con Tkinter incluido y añadido al PATH).
- Probado de verdad en este ordenador: descarga real (28 MB) con la
  misma línea de `curl` del `.bat`, y la lógica de detección de la
  ruta de instalación. No probado el ciclo completo en un Windows
  limpio sin Python (no había uno a mano en esta sesión).
- README.md, CLAUDE.md y docs/DECISIONS.md actualizados.

## 2026-08-23 (8) — Ingreso estimado con hashrate real en la pantalla de minado

- Nuevo `minar.extraer_hashrate_real(linea, motor)`: saca la velocidad
  real de minado de una línea de log concreta (formato de xmrig
  verificado con ejemplos reales de GitHub; kawpowminer verificado
  contra su código fuente real, `TelemetryType::str()` en
  `libethcore/Miner.h`; lolMiner por varios registros reales
  coincidentes, es de código cerrado). Devuelve `None` si esa línea no
  trae el dato (la mayoría no).
- Nuevo `estimacion_ingreso.escalar_a_hashrate(...)`: reescala la
  estimación de referencia ya calculada a la velocidad real medida,
  sin ninguna consulta de red adicional (aritmética local).
- `src/formulario.py`: nueva etiqueta fija arriba de "Minado en
  marcha" por bloque activo, que pasa de "calculando tu velocidad
  real…" a la cifra real en cuanto llega la primera lectura del motor.
  Sigue mostrando "no disponible" para WOW/RTM/ALPH, igual que antes.
- Probado de extremo a extremo con una `App` de Tkinter real. 127 tests
  en verde (antes 124).
- `docs/DECISIONS.md` actualizado con el detalle y las fuentes exactas.

## 2026-08-23 (7) — El autorrelleno de wallet seguía fallando: el campo empieza deshabilitado

- Causa real (la del parser de la entrada anterior no era la única): el
  campo de wallet de cada bloque empieza deshabilitado hasta que marcas
  la casilla "Minar con la CPU/GPU" — y un campo deshabilitado en
  Tkinter ignora en silencio cualquier `insert()`/`delete()` por código.
  El primer intento de autorrelleno (al abrir la app) no hacía nada, y
  como la app ya había registrado esa moneda como "procesada", marcar
  la casilla después tampoco lo reintentaba.
- Arreglado en `src/formulario.py` (`_on_toggle`): al habilitarse el
  campo, si sigue vacío, se reintenta el autorrelleno. No pisa nada que
  ya hayas escrito a mano.
- Nuevo test de regresión que instancia una `App` de Tkinter real
  (`tests/test_formulario_logica.py`) — este tipo de fallo solo se ve
  con un widget real, no con funciones aisladas. 115 tests en verde.

## 2026-08-23 (6) — wallets.md: activadas tus wallets y arreglado el parser

- Activadas las líneas de XMR y RVN en `wallets.md` (te faltaba borrar
  el `#` delante, tal como explica el propio fichero).
- Bug real encontrado al investigarlo: `src/wallets_defecto.py` aceptaba
  como "moneda" cualquier línea con `:`, incluidas las frases
  explicativas del principio de `wallets.md`. No se notaba en la
  ventana (esas frases nunca coinciden con una moneda real), pero se
  arregló exigiendo que el símbolo tenga pinta de ticker real. Nuevo
  test de regresión en `tests/test_wallets_defecto.py`. 114 tests en
  verde.

## 2026-08-23 (5) — La causa real del "Acceso denegado" no era el antivirus: bug en la búsqueda del ejecutable

- El "Acceso denegado" seguía pasando después de excluir la carpeta del
  antivirus. Investigado directamente en el ordenador de Carlos:
  `src/motores.py` (`_buscar_binario`) encontraba la carpeta
  `bin/xmrig/` (creada por `src/instalador.py` al descomprimir la
  descarga) en vez del ejecutable real `bin/xmrig.exe`, porque solo
  comprobaba que el candidato "existiera" y no que fuera un fichero.
  Windows no puede ejecutar una carpeta y lo reporta como "Acceso
  denegado", de ahí el mensaje engañoso.
- Arreglado: `_buscar_binario` ahora exige `candidato.is_file()`. Nuevo
  test de regresión en `tests/test_motores.py`. 113 tests en verde.
- `docs/DECISIONS.md` actualizado con la corrección (la explicación
  anterior, "es el antivirus", quedaba incompleta/incorrecta como causa
  única — documentado explícitamente en vez de borrarlo).

## 2026-08-23 (4) — Sesión local confirmada, y arreglo del "Acceso denegado" al arrancar el motor

- Confirmado que el trabajo en este proyecto ya no ocurre en la sesión
  en la nube de las primeras sesiones (sin pantalla ni GPU), sino en
  local, en el propio Windows de Carlos, con pantalla, red y GPU reales
  (NVIDIA RTX 4060 Laptop, 8GB — detectada en esta misma máquina).
  Actualizado `CLAUDE.md` para reflejarlo: `formulario.py` sí se puede
  ejecutar de verdad aquí (aunque sigue sin haber forma de ver la
  ventana renderizada sin que Carlos la abra o mande una captura), y ya
  no hay una prohibición general de minar de verdad — solo hacerlo
  cuando él lo pida.
- Arreglado un fallo real: al pulsar "Comenzar a minar", si arrancar el
  motor de minado fallaba (por ejemplo, "Acceso denegado" — muy
  probablemente el antivirus bloqueando el `.exe` recién descargado,
  algo habitual con cualquier programa de minado), el hilo de fondo
  reventaba con una traza en la consola en vez de avisar en la ventana.
  Ahora se captura (`src/formulario.py` y el `main()` de `src/minar.py`)
  y se muestra un mensaje claro explicando la causa probable y qué
  hacer (añadir una excepción en el antivirus para la carpeta `bin/`).
- Actualizado `docs/DECISIONS.md` con el detalle de ambos cambios.

## 2026-08-23 (3) — Estimación de ingreso en €/hora (5 de 8 monedas)

- Nuevo `src/estimacion_ingreso.py`: `estimar_referencia(simbolo)`
  calcula moneda/hora y $/hora a una velocidad de minado de referencia
  fija (no el hardware real del usuario), usando dificultad/hashrate de
  red en vivo (supportxmr.com para XMR, herominers.com para SAL/ZEPH,
  2miners.com para RVN, api.kaspa.org para KAS) y precio en vivo de
  CoinGecko, cacheado 5 minutos en memoria.
- WOW, RTM y ALPH quedan sin estimación a propósito: no se encontró una
  fuente gratuita, en vivo y verificable con confianza para ellas (ver
  cabecera de `estimacion_ingreso.py` y `docs/DECISIONS.md` para el
  detalle por moneda). La app muestra "Estimación no disponible ahora
  mismo" en vez de un número inventado.
- `src/formulario.py`: nueva etiqueta bajo cada desplegable (CPU y GPU)
  con la estimación de la moneda seleccionada; se recalcula al cambiar
  de moneda, en un hilo de fondo (con cola + `after`, mismo patrón que
  el log de minado) para no congelar la ventana, y descarta resultados
  obsoletos si el usuario cambia de moneda antes de que llegue la
  respuesta.
- Añadidas 18 pruebas nuevas (112 en total): `test_estimacion_ingreso.py`
  (con respuestas de ejemplo reales de cada API, todo mockeado) y
  ampliado `test_formulario_logica.py`.
- Actualizados README.md, CLAUDE.md y docs/DECISIONS.md.

## 2026-08-23 (2) — Solo monedas minables, wallets por defecto, y arreglo de un bug real de recomendación

- `src/formulario.py`: los desplegables de CPU y GPU ahora solo muestran
  monedas con `soportado_por_minar_hoy: True` (nueva
  `filtrar_solo_soportadas`), con la de mayor ingreso estimado
  preseleccionada.
- `src/ingresos.py`: corregido un bug real en `clasificar_por_ingreso`.
  whattomine.com no incluye hoy ninguna moneda de CPU ni Kaspa/Alephium
  de GPU; el código antiguo, con datos en vivo parciales, mandaba a esas
  monedas al fondo del ranking como si valieran cero (`any` en vez de
  `all` al comprobar cobertura). Corregido: si los datos en vivo no
  cubren TODAS las monedas comparadas, se usa el ranking de reserva
  completo en su lugar. Nuevo test cubre el caso.
- Nuevo `wallets.md` (raíz del repo, **sí se sube a git** — una wallet
  es una dirección pública, no una clave privada) + `src/wallets_defecto.py`:
  el formulario rellena solo el campo de wallet al elegir una moneda, si
  hay una guardada ahí.
- `src/formulario.py`: al reanalizar el hardware (por ejemplo, al marcar
  la VRAM manual de la GPU), ya no se pierde la moneda que tenías
  elegida ni la wallet que hubieras escrito a mano, si seguía siendo una
  opción válida (antes se reiniciaba todo al valor recomendado).
- Añadidas 7 pruebas nuevas (94 en total): `test_wallets_defecto.py`, y
  ampliados `test_formulario_logica.py` y
  `test_hardware_monedas_recomendador.py`.
- Nuevo `Iniciar minado.bat` en la raíz: doble click en Windows para
  abrir la app sin necesidad de terminal.
- Actualizados README.md, CLAUDE.md y docs/DECISIONS.md.

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
