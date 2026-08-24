# Decisiones técnicas

Cada entrada explica una decisión y el porqué, en lenguaje simple.

## 2026-08-20 — Lenguaje: Python

Se usa Python porque es fácil de instalar y de leer aunque no seas
programador, y ya viene preparado para leer y escribir ficheros de texto
sencillos como el que pediste.

## 2026-08-20 — El minado lo hace XMRig, no un código nuestro

Programar el algoritmo de minado desde cero es extremadamente complejo y
fácil de hacer mal (u de forma insegura). En su lugar, el script escribe
por ti los datos correctos y llama a **XMRig**, que es el programa
gratuito y de confianza que usa la comunidad para minar monedas del tipo
Monero. Es como si nuestro script fuera "el mando a distancia" y XMRig
fuera "la tele": nosotros solo configuramos y encendemos.

## 2026-08-20 — Formato del fichero de configuración: texto simple

Pediste que fuera un `.md` o `.txt` sencillo. Se usa un formato de líneas
`clave: valor` (por ejemplo `wallet: ...` y `moneda: XMR`) porque se puede
editar con cualquier editor de texto, sin aprender ninguna sintaxis
especial.

## 2026-08-20 — Primera moneda soportada: Monero (XMR)

Elegimos Monero como primera moneda porque es la más práctica para minar
con el procesador (CPU) de un ordenador normal, sin hardware especial.
Otras monedas suelen necesitar tarjetas gráficas potentes o máquinas
dedicadas (ASICs), que complicarían mucho la primera versión. Se puede
añadir soporte para más monedas más adelante si hace falta.

## 2026-08-20 — No se ejecuta minado real dentro de esta sesión en la nube

Esta conversación ocurre en un espacio de trabajo compartido en la nube
de Anthropic. Usar ese espacio para minar criptomonedas de verdad (aunque
sea para tu propia wallet) sería un mal uso de ese recurso compartido, así
que las comprobaciones dentro de la sesión se hacen en modo simulación
(`--dry-run`) o con un programa de prueba que no se conecta a ningún
servidor real. El minado real solo debe ocurrir cuando tú ejecutes el
script en tu propio ordenador.

## 2026-08-20 — Formulario gráfico con Tkinter

Para el formulario que rellena `config.md` visualmente, se usa **Tkinter**,
que viene incluido con Python (no hace falta instalar nada aparte, salvo
en algunos Linux donde falta un pequeño paquete del sistema). Se descartó
hacerlo como página web local porque habría que arrancar un servidor y
abrir el navegador, un paso más para algo que se supone "muy básico".

## 2026-08-20 — Detección de hardware "a mejor esfuerzo"

No existe una forma 100% fiable de detectar cualquier CPU y GPU en
Windows, Mac y Linux a la vez sin instalar programas adicionales. El
formulario prueba varios comandos que ya vienen en cada sistema operativo
(por ejemplo `nvidia-smi`, `wmic`, `system_profiler`) y, si ninguno
funciona, dice claramente que no pudo detectar la tarjeta en vez de
inventar un dato. Además, si la GPU no se detecta bien, el formulario deja
la opción de indicar a mano cuánta memoria de vídeo tiene, para no
bloquear a nadie.

## 2026-08-20 — Solo 9 monedas de CPU, no 15

Pediste investigar unas 15 monedas habituales de cada tipo. Para GPU sí
hay 15 con sentido real. Para CPU, en 2026 casi todas las criptomonedas
serias ya no se pueden minar rentablemente con procesador (las minan
máquinas especializadas o tarjetas gráficas); las únicas que de verdad
siguen usando algoritmos pensados para CPU son las 9 que aparecen en
`src/monedas.py` (Monero, Wownero, Zephyr, Salvium, Talecoin, Raptoreum,
Dero, Verus Coin y Xelis). Se decidió no rellenar hasta 15 con monedas
irrelevantes o de riesgo alto solo por completar el número.

## 2026-08-20 — Cómo se decide "la de mayor ingreso"

El formulario intenta consultar datos en vivo de whattomine.com (una web
pública de referencia en minería) para comparar ingresos entre monedas.
Si en ese momento no hay conexión a internet, usa un ranking aproximado
que se investigó el 2026-08-20 (guardado en el propio código). En ambos
casos es una estimación: no conoce el rendimiento exacto de tu hardware
en cada algoritmo concreto, así que trátalo como una orientación razonable,
no como un cálculo exacto. Como pediste, no se tiene en cuenta el coste
de la luz (eso sería "beneficio", no "ingreso").

## 2026-08-20 — El formulario solo rellena el fichero; no todas las monedas ya se pueden minar

El formulario deja bien configurada cualquiera de las 24 monedas del
catálogo. Pero `src/minar.py` (el que arranca el minado de verdad) hoy
solo sabe hacerlo con Monero, porque es el único para el que ya
preparamos el programa de minado (XMRig). Si eliges otra moneda, el
fichero se generará igual y el formulario te avisará; arrancarla de
verdad sería un paso futuro (añadir el programa de minado adecuado para
ese algoritmo), que haremos cuando me digas cuál quieres usar.

## 2026-08-20 — Esta sesión en la nube no tiene pantalla ni paquete gráfico

Este entorno de trabajo en la nube no tiene instalado el paquete que
Tkinter necesita para dibujar ventanas, y no se pudo instalar durante
esta sesión (el acceso a internet de este espacio está limitado a lo
imprescindible). Por eso no se pudo enseñar una captura de pantalla del
formulario funcionando: se comprobó a fondo toda la lógica interna (24
pruebas automáticas, detección real de tu hardware en este entorno,
comprobación de que el fichero que genera es compatible con
`minar.py`), pero la ventana en sí tendrás que abrirla tú la primera vez,
en tu propio ordenador.

## 2026-08-20 — minar.py ya sabe arrancar 5 monedas, no solo Monero

Preguntaste si, ya que conocemos el motor de cada moneda, podíamos
arrancarlas todas automáticamente. La respuesta corta es: para 5 de las
9 monedas de CPU, sí, y ya está hecho; para el resto (incluidas las 15
de GPU) hace falta más trabajo, y prefiero ir con cuidado en vez de
improvisarlo. Te explico la diferencia:

**Ya añadido (Wownero, Zephyr, Salvium, Raptoreum):** estas 4 monedas,
igual que Monero, se minan con el mismo programa, XMRig — solo cambia a
qué servidor (pool) se conecta y qué "variante" del cálculo usa. Como
XMRig es un programa de código abierto que ya conocíamos bien, fue
seguro extenderlo: investigué en fuentes fiables (la propia web de cada
proyecto, o ejemplos oficiales del repositorio de XMRig en GitHub) el
pool y la variante correctas para cada una, lo añadí y lo probé.

**Todavía no añadido (Dero, Verus Coin, Xelis, Talecoin, y las 15 de
GPU):** estas necesitan programas de minado completamente distintos
(uno por cada familia de algoritmo: T-Rex, lolMiner, gminer, bzminer,
miniZ...). Antes de automatizarlo de verdad, prefiero ser transparente
con dos cosas:
1. Varios de esos programas son gratuitos pero de código cerrado, y
   cobran una pequeña "comisión del desarrollador" (un pequeño
   porcentaje del tiempo de minado va para quien hizo el programa, no
   para ti) — esto afecta un poco al ingreso real, así que merece la
   pena decírtelo antes de instalar uno.
2. Esta sesión de trabajo en la nube no tiene tarjeta gráfica ni
   pantalla, así que no puedo probar de verdad ninguna parte de minado
   por GPU aquí (solo la lógica que decide qué moneda es posible).
Por eso, en vez de intentarlo todo a la vez sin poder comprobarlo bien,
prefiero ir moneda por moneda, empezando por la que realmente vayas a
usar. Dímelo cuando quieras y seguimos con esa.

Fuentes consultadas para los pools y variantes añadidos: la web oficial
de Wownero, RavenMiner (Zephyr), HeroMiners (Salvium) y el propio
repositorio de XMRig en GitHub (ejemplo oficial de Raptoreum/GhostRider
y lista de variantes RandomX). Los pools por defecto pueden cambiar con
el tiempo; si alguno deja de funcionar, se puede indicar otro distinto
añadiendo una línea `pool: otro-servidor:puerto` en `config.md`.

## 2026-08-20 — Por qué no programamos nuestro propio motor de minado

Preguntaste si, para evitar la comisión del desarrollador, podíamos
construir nuestro propio programa de minado. Es una idea razonable, pero
la respuesta es que no compensa, por dos motivos:

1. **Es un proyecto enorme por sí mismo.** Cada algoritmo (RandomX,
   KawPow, kHeavyHash...) es un cálculo matemático muy específico que
   hay que programar y optimizar para que aproveche bien la tarjeta
   gráfica o el procesador. Los programas que usamos (XMRig, kawpowminer,
   lolMiner) son el resultado de años de trabajo de gente especializada
   en esto. Reproducirlo nosotros, además de llevar mucho más tiempo del
   que tiene sentido invertir aquí, probablemente saldría peor
   optimizado — y un programa un poco menos eficiente te haría perder
   más dinero en electricidad del que ahorrarías en comisión.
2. **A veces ya existe la alternativa gratuita, sin tener que
   programarla.** Al investigar Ravencoin encontré `kawpowminer`, un
   programa de código abierto y sin ninguna comisión, mantenido por la
   propia comunidad de Ravencoin — así que ahí no hace falta pagar nada
   ni construir nada. Para Kaspa y Alephium sí existen "mineros
   oficiales" de código abierto de los propios creadores de la moneda,
   pero están pensados para minar en solitario contra tu propio nodo
   completo (mucho más complicado de mantener, y minar en solitario casi
   nunca encuentra recompensa con un solo ordenador); para conectarse a
   un pool público de forma sencilla, la opción fiable es lolMiner, con
   una comisión pequeña (0,75%).

Además, algo importante que aprendí investigando esto: **XMRig, el
motor que ya usábamos, también tiene una comisión por defecto (1%)**,
aunque es ajustable porque es de código abierto (se puede bajar con
`donate_level: N` en `config.md`). No es que XMRig fuera gratis y las
demás no — la diferencia real es entre motores de código abierto (donde
tú puedes ver y cambiar la comisión) y motores de código cerrado como
lolMiner (donde la comisión es fija, pero suele ser pequeña y el
programa está muy bien optimizado).

## 2026-08-20 — Implementadas 3 monedas más de GPU (RVN, KAS, ALPH)

Pediste las 3 monedas de CPU y las de GPU con mayor ingreso estimado.
Las 3 de CPU con mayor ingreso (Monero, Raptoreum, Zephyr) ya estaban
implementadas desde la sesión anterior. Para GPU, implementé las 3
primeras del ranking:

- **Ravencoin (RVN)**: motor `kawpowminer`, código abierto, 0% de
  comisión. Fuente: RavenMiner (pool y comando) y minerstat (comisión).
- **Kaspa (KAS)**: motor `lolMiner`, 0,75% de comisión. Fuente: HeroMiners
  (pool) y el README oficial de lolMiner (comando y tabla de comisiones).
- **Alephium (ALPH)**: motor `lolMiner`, 0,75% de comisión. Mismas
  fuentes que Kaspa.

Estas tres son técnicamente distintas de las 5 de CPU: cada una necesita
un programa de minado distinto (por eso se creó `src/motores.py`, un
"registro" de motores que sabe encontrar cada ejecutable y construir su
comando concreto). El código está escrito y probado con un ejecutable de
prueba (igual que se hizo con XMRig), pero **nunca se ha ejecutado
contra una tarjeta gráfica real ni un pool real**, porque este entorno de
trabajo no tiene GPU. Lo dejo hecho para que lo pruebes tú en tu propio
ordenador; en `monedas.py`, en el formulario (icono 🧪) y en el README
queda marcado como "sin confirmar" hasta que alguien lo pruebe de verdad
y lo confirme.

Quedan pendientes, por orden de ingreso estimado: Ergo (ERG), Ethereum
Classic (ETC), Conflux (CFX)... y del lado de CPU, Dero (DERO), Verus
Coin (VRSC) y Xelis (XEL). Se pueden ir añadiendo de la misma forma
cuando se necesiten.

## 2026-08-20 — El ejecutable de XMRig no se guarda en el repositorio

XMRig es un programa grande y distinto para cada sistema operativo
(Windows, Mac, Linux). En vez de guardarlo dentro del repositorio, el
script lo busca en tu ordenador o en una carpeta `bin/` local que tú
rellenas tú mismo siguiendo las instrucciones de `bin/LEEME.md`.

## 2026-08-23 — Formulario y minado, una sola app; el motor de minado se instala solo

Dijiste, con razón, que pedirte instalar tú el motor de minado a mano ya
era pedirte demasiado: la premisa de este proyecto es que no tienes que
saber hacer nada técnico. Cuatro cambios grandes de esta sesión, todos
con la misma idea detrás:

1. **Una sola ventana hace todo.** Antes `formulario.py` solo escribía
   `config.md` y había que abrir una terminal aparte y ejecutar
   `minar.py` para minar de verdad — dos pasos, uno de ellos por
   terminal. Ahora el botón "Comenzar a minar" del propio formulario
   hace las dos cosas: guarda la configuración y arranca a minar en el
   momento, sin salir de la ventana.
2. **El motor de minado se descarga solo.** Nuevo módulo
   `src/instalador.py`: si al pulsar "Comenzar a minar" falta el
   programa de minado (XMRig, kawpowminer o lolMiner), la app consulta
   la página oficial de ese proyecto en GitHub, descarga la versión
   correcta para tu sistema operativo (y, para kawpowminer, según si tu
   tarjeta gráfica es NVIDIA o de otra marca) y la deja lista en `bin/`
   — sin que tengas que buscar ni descargar nada tú. `bin/LEEME.md`
   queda como explicación de qué es esa carpeta y como opción manual de
   repuesto, no como paso obligatorio.
3. **CPU y GPU, cada una con su propia moneda y wallet.** Antes solo se
   podía elegir una moneda y una wallet para todo el ordenador. Ahora
   `config.md` tiene dos bloques independientes (`cpu_moneda`/
   `cpu_wallet` y `gpu_moneda`/`gpu_wallet`, cada uno opcional) y puedes
   minar solo con el procesador, solo con la tarjeta gráfica, o con las
   dos a la vez — cada una mandando sus ingresos a la wallet que tú
   quieras.
4. **El registro de minado se traduce a lenguaje sencillo.** Los
   programas de minado (XMRig, etc.) escriben su registro técnico en
   inglés y con mucho detalle. Ahora `minar.py` interpreta ese registro
   y muestra frases simples ("conectado al pool", "comparte aceptado",
   "velocidad: ..."); si quieres ver el registro técnico completo, hay
   una casilla para activarlo.

Una decisión más pequeña dentro de este cambio: la descarga automática
del motor de minado no comprueba una "firma" o "huella digital" de
seguridad del archivo (algo que sí ofrecen XMRig y kawpowminer, pero no
lolMiner, así que no había forma de hacerlo igual para los tres). Se
descarga siempre en conexión cifrada (https) directamente desde el
repositorio oficial del proyecto en GitHub, que es la misma fuente que
usaría cualquier persona si lo descargara a mano. Si en el futuro
quieres ese nivel extra de comprobación, se puede añadir para XMRig y
kawpowminer.

## 2026-08-23 — Solo se muestran monedas ya minables, y se corrige un fallo real en "la de mayor ingreso"

Probaste la app y viste dos problemas: los desplegables mostraban
monedas que la app en realidad no sabe minar todavía, y la moneda
preseleccionada no siempre parecía la más lógica. Investigando el
segundo problema encontré un fallo real en el código, no solo una
cuestión de gusto:

`ingresos.py` intenta comparar el ingreso estimado de todas las monedas
candidatas usando datos en vivo de whattomine.com. El problema es que
esa web, hoy, **no incluye ninguna de las monedas de CPU de este
proyecto** (ni Monero) **y solo una de las tres de GPU** (Ravencoin; le
faltan Kaspa y Alephium). El código antiguo, en cuanto encontraba
aunque fuera un solo dato en vivo entre las candidatas, comparaba TODAS
con esos datos — y a las que no tenían dato en vivo (casi todas) las
mandaba automáticamente al final de la lista, como si ganaran cero,
en vez de usar el ranking de reserva que sí las tiene en cuenta. En la
práctica esto hacía que Ravencoin saliera casi siempre recomendada por
delante de Kaspa o Alephium, aunque no fuera la que más rinde. Ahora
solo se usan los datos en vivo cuando cubren a TODAS las monedas que se
están comparando; si falta alguna, se compara el grupo entero con el
ranking de reserva, para no mezclar una fuente real con un cero
inventado.

Además, el desplegable ahora solo enseña monedas con
`soportado_por_minar_hoy: True` (las de la tabla del README). Antes se
mostraba el catálogo entero (más de una docena de monedas investigadas
pero sin motor de minado todavía) mezclado con las que sí funcionan; era
información útil para mí como referencia, pero confusa para ti como
usuario final de la app: podías elegir una moneda que luego no arrancaba
de verdad. El catálogo completo se sigue pudiendo consultar en
`src/monedas.py` para cuando se añada soporte a alguna más.

## 2026-08-23 — `wallets.md`: un fichero con tus wallets por defecto, y sí se sube a git

Pediste poder guardar tus wallets por moneda directamente en un fichero
del repositorio, para que el formulario las rellene solas. Esto podría
sonar contradictorio con la regla de "nunca subas tu wallet a git" de
`config.md` — pero no lo es, y merece explicarse: esa regla es sobre
`config.md` en concreto porque en su momento se trató la wallet como un
dato sensible por precaución, pero una dirección de wallet (donde
RECIBES el dinero minado) es pública por diseño: en cuanto te llega un
pago, cualquiera puede verla en la cadena de bloques, igual que un
número de cuenta que le das a alguien para que te pague. Lo que nunca
debe subirse a ningún sitio es tu **clave privada** o **frase semilla**
(lo que demuestra que ERES el dueño de la wallet y te permite gastar el
dinero) — eso sí es secreto, y no tiene nada que ver con la dirección.

Por eso `wallets.md` es un fichero nuevo, distinto de `config.md`: vive
en la raíz del proyecto, con líneas `SIMBOLO: direccion`, y sí se sube a
GitHub sin problema. El formulario lo lee al abrir y rellena el campo de
wallet correspondiente en cuanto eliges esa moneda (si no hay wallet
guardada para ella, el campo se queda vacío, como hasta ahora).

## 2026-08-23 — Estimación de ingreso en €/hora: solo para las monedas con una fuente de datos real y verificada

Pediste ver, junto a cada moneda, más o menos cuánto se ganaría por
hora (en la moneda y en dólares). Para calcular eso de verdad hacen
falta dos datos por moneda: el precio actual, y la dificultad/velocidad
de la red (cuánta "competencia" hay para minar un bloque). Investigué
las opciones:

- **whattomine.com** (la web que ya se usaba para ordenar monedas por
  ingreso) hoy no incluye ninguna de nuestras 5 monedas de CPU, y de las
  3 de GPU solo Ravencoin. No sirve para esto.
- **minerstat.com** tiene justo el dato que hace falta, pero ahora exige
  crear una cuenta de desarrollador de pago — lo descarté, no encaja con
  la idea de que esta app no te pida cuentas ni pagos externos.
- La alternativa que sí funcionó: usar, moneda por moneda, la API
  pública y gratuita del propio pool (o explorador oficial) que ya
  usamos como servidor por defecto para minarla, más el precio actual de
  **CoinGecko** (gratis, sin registro).

Resultado, verificado con peticiones reales antes de dar nada por
bueno: **5 de las 8 monedas tienen estimación real** (Monero vía
supportxmr.com, Salvium y Zephyr vía sus pools en herominers.com,
Ravencoin vía 2miners.com, Kaspa vía api.kaspa.org — fuentes exactas en
la cabecera de `src/estimacion_ingreso.py`). Para las otras 3, decidí
**no mostrar ningún número en vez de arriesgarme a que estuviera mal**:

- **Wownero (WOW)**: no cotiza en CoinGecko (hay un token distinto con
  el mismo símbolo "WOW" en otra red, que no es Wownero), así que no hay
  un precio fiable de dónde partir.
- **Raptoreum (RTM)**: no encontré una web pública y gratuita que diera
  su dificultad de red en vivo y de forma fiable.
- **Alephium (ALPH)**: su algoritmo (Blake3) es de una familia distinta
  a las demás, y la única fuente encontrada daba una dificultad cuya
  escala no pude verificar contra el hashrate real de la red — antes de
  arriesgarme a una fórmula mal calculada (que te haría tomar una
  decisión con un dato falso), preferí dejarla sin estimar.

Esto es coherente con cómo se trató desde el principio la detección de
hardware (ver más arriba, "Detección de hardware 'a mejor esfuerzo'"):
mejor decir claramente "no lo sé" que inventar un dato. Si en el futuro
aparece una fuente fiable para estas 3, es sencillo añadirla en
`src/estimacion_ingreso.py`.

Importante también: el número que se muestra **no es tu hardware
real**. Es un cálculo normalizado a una velocidad de minado fija y
redonda por algoritmo (por ejemplo, 1 kH/s para las monedas tipo
Monero, 10 MH/s para Ravencoin) — sirve para comparar monedas entre sí
y hacerte una idea de escala, no como una promesa exacta de cuánto vas
a ganar tú. Medir tu velocidad real habría requerido ejecutar un
benchmark del propio motor de minado, que descartamos por ahora para no
alargar más esta parte (queda como posible mejora futura si algún día
quieres esa precisión).

## 2026-08-23 (4) — Este proyecto se trabaja en local, no en una sesión en la nube

Las primeras sesiones de este proyecto ocurrieron en un entorno de
trabajo en la nube de Anthropic sin pantalla ni GPU (por eso hay
decisiones antiguas, más arriba en este documento, que hablan de "esta
sesión en la nube" y de comprobar todo con `--dry-run`). Confirmaste que
esas sesiones se han terminado: ahora se trabaja con Claude Code
directamente en tu propio ordenador Windows
(`C:\proyectos\autominer`), con pantalla, red y GPU reales. No se borran
esas decisiones antiguas (explican bien por qué se hicieron las cosas
así en su momento), pero desde ahora ya no aplican como limitación: se
puede ejecutar `formulario.py` de verdad, y se puede minar de verdad
cuando tú lo pidas (ver `CLAUDE.md`, sección "Reglas importantes", para
la regla actualizada). Detecté con `hardware.py`, en esta misma máquina,
una GPU real: NVIDIA RTX 4060 Laptop, 8GB de VRAM — de sobra para RVN,
KAS y ALPH.

## 2026-08-23 (5) — El motor de minado descargado no arrancaba: "Acceso denegado" (WinError 5)

Al pulsar "Comenzar a minar" en tu ordenador, xmrig se descargó bien
pero no llegó a arrancar: Windows devolvió "Acceso denegado" al
intentar ejecutarlo. La causa casi segura no es un fallo de este
proyecto, sino el antivirus (Windows Defender u otro): los programas de
minado —y en concreto el fichero `WinRing0x64.sys` que XMRig instala
para acelerar el cálculo— están entre los más marcados como
sospechosos por cualquier antivirus, aunque sean legítimos y de código
abierto. Es tan habitual que la propia documentación oficial de XMRig
lo advierte. Puede pasar de dos formas: que el antivirus bloquee/ponga
en cuarentena el `.exe` sin más, o que lo esté escaneando en el mismo
instante en que la app intenta arrancarlo (un fichero recién
descargado) y bloquee ese primer intento por eso.

Dos cambios:
1. **Arreglado un fallo real**: si arrancar el motor fallaba, el hilo de
   fondo del formulario reventaba con una traza de error en la consola
   en vez de avisar en la propia ventana. Ahora se captura ese fallo
   (`PermissionError` y cualquier otro `OSError`) y se muestra un
   mensaje claro en el registro de la app, con la explicación de arriba
   y qué hacer.
2. **Qué hacer tú**: añade una excepción en tu antivirus para la carpeta
   `bin/` de este proyecto (o para la carpeta completa del proyecto) y
   vuelve a intentarlo. En Windows Defender: Seguridad de Windows →
   Protección antivirus y contra amenazas → Administrar configuración →
   Exclusiones → Agregar una exclusión → Carpeta. También puedes revisar
   "Historial de protección" ahí mismo para ver si detectó y bloqueó
   algo en concreto.

**Corrección (2026-08-23, más tarde el mismo día):** la explicación de
arriba resultó estar equivocada — añadiste la excepción y el error
seguía pasando, igual que antes. Investigué directamente en tu
ordenador (misma sesión de Claude Code, mismo equipo) en vez de seguir
suponiendo, y encontré la causa real, que no tiene nada que ver con el
antivirus:

`src/instalador.py`, al descargar xmrig, lo descomprime en una carpeta
`bin/xmrig/` (además de dejar también una copia suelta en
`bin/xmrig.exe`, que es la que de verdad se usa para minar). El
problema es que `src/motores.py` busca el ejecutable probando una lista
de nombres candidatos (`"xmrig"`, luego `"xmrig.exe"`) y se quedaba con
el primero que "existiera" en esa carpeta — pero **no comprobaba que
fuera un fichero y no una carpeta**. Como esa carpeta de extracción se
llama exactamente `xmrig` (el primer nombre candidato, sin extensión),
el código encontraba la CARPETA antes de llegar a comprobar
`xmrig.exe`, y le pasaba esa ruta a `subprocess.Popen` como si fuera el
programa a ejecutar. Windows no puede "ejecutar" una carpeta, y reporta
justo ese caso como "Acceso denegado" (WinError 5) — de ahí el mensaje
engañoso, que apuntaba al antivirus sin serlo.

Arreglado en `src/motores.py` (`_buscar_binario`): ahora comprueba
`candidato.is_file()` en vez de `candidato.exists()`, así que una
carpeta con el mismo nombre nunca se puede confundir con el ejecutable.
Nuevo test de regresión en `tests/test_motores.py` que reproduce
exactamente este caso (una carpeta `bin/xmrig/` junto a un
`bin/xmrig.exe` real) para que no se repita. La lección para la próxima
vez que aparezca un error así: si el mismo problema persiste después de
aplicar el arreglo "más probable" a la primera, hay que parar de
suponer y comprobar directamente qué está pasando en la máquina real
antes de dar otra explicación.

## 2026-08-23 (6) — `wallets_defecto.py` leía como "moneda" cualquier línea con ":"

Al rellenar `wallets.md` con tu wallet de Monero, no se autocompletaba
en el formulario. Causas, las dos reales:

1. **Tuya, de instrucciones poco claras**: dejaste el `#` delante de la
   línea (`# XMR: tu-dirección`), y el propio fichero explica que hay
   que borrarlo para activarla — sin el `#` de por medio, esa línea es
   solo un comentario y se ignora a propósito. Ya te la activé yo.
2. **Nuestra, un bug real** que encontré al comprobar por qué: el lector
   de `wallets.md` (`src/wallets_defecto.py`) aceptaba como "moneda"
   CUALQUIER línea con un `:` — incluidas las frases explicativas del
   principio del propio fichero (por ejemplo "...formato \`SIMBOLO:
   direccion\`..." se leía como si "Una línea por moneda, formato
   \`SIMBOLO" fuera el símbolo de una moneda). No se notaba en la
   ventana porque esas frases nunca coinciden con una moneda de verdad,
   pero era un fallo real de todos modos. Arreglado exigiendo que el
   símbolo tenga pinta de ticker real (letras/números, sin espacios,
   2 a 10 caracteres) antes de aceptar la línea. Test de regresión en
   `tests/test_wallets_defecto.py` que reproduce el caso exacto.

## 2026-08-23 (7) — El bug de verdad: el campo de wallet empieza deshabilitado

Arreglé lo de arriba y seguía sin autorrellenarse. La causa real era
otra, y esta vez sí era la última: el campo de wallet de cada bloque
(CPU/GPU) empieza **deshabilitado** en la ventana, porque la casilla
"Minar con la CPU/GPU" no está marcada todavía al abrir la app. En
Tkinter, un campo deshabilitado ignora en silencio cualquier intento de
escribir en él por código (`insert`/`delete`) — no da ningún error, solo
no hace nada. Como el autorrelleno se intentaba justo al construir la
ventana (con el campo todavía deshabilitado), no servía de nada; y como
la app ya había apuntado esa moneda como "procesada", marcar la casilla
después tampoco lo volvía a intentar.

Arreglado en `src/formulario.py` (`_on_toggle`): al marcar la casilla y
habilitarse el campo, si sigue vacío, se vuelve a intentar el
autorrelleno en ese momento. Si ya habías escrito algo a mano (por
ejemplo, desmarcaste y volviste a marcar la casilla), no se toca — solo
rellena campos vacíos. Nuevo test de regresión en
`tests/test_formulario_logica.py` que abre una app de verdad (con
Tkinter real, ya que esto es exactamente el tipo de fallo que una
función aislada sin ventana no puede detectar) y comprueba que marcar
la casilla rellena el campo.

## 2026-08-23 (8) — Ingreso estimado con tu hashrate REAL, en la pantalla de minado

Preguntaste, con razón: si el motor de minado ya está reportando tu
velocidad real, ¿por qué seguir mostrando solo la estimación de
referencia (1 kH/s, etc.)? Confirmado: la estimación de antes de
arrancar es siempre a esa velocidad fija, nunca la tuya. Ahora, en la
pantalla "Minado en marcha", arriba del todo, aparece una segunda
estimación que se actualiza sola con tu velocidad real, en cuanto el
motor la reporta por primera vez.

Cómo se hizo, con cuidado de no inventar ningún formato:
- **xmrig**: confirmé el formato exacto de su línea de velocidad
  (`speed 10s/60s/15m X Y Z H/s max W H/s`) con ejemplos reales de
  usuarios en el propio repositorio de GitHub del proyecto (issues
  #872 y #2624), no adivinado.
- **kawpowminer**: es de código abierto, así que fui a la fuente
  directamente: la función que construye esa línea
  (`TelemetryType::str()` en `libethcore/Miner.h` del repositorio
  oficial `RavenCommunity/kawpowminer`) — formato 100% verificado, no
  una suposición sobre cómo "debería" verse.
- **lolMiner**: es de código cerrado, así que no hay fuente que
  consultar; usé el formato ("Total: X mh/s") que aparece igual en
  varios registros reales compartidos por distintos usuarios en GitHub,
  con confianza razonable pero no absoluta (si alguna vez no coincide,
  simplemente no se actualiza esa cifra — nunca se rompe la app ni se
  inventa un número).
- Nuevo `minar.extraer_hashrate_real(linea, motor)`: intenta sacar la
  velocidad real de una línea de log concreta; si esa línea no la trae
  (la mayoría no), devuelve `None` sin más.
- Nuevo `estimacion_ingreso.escalar_a_hashrate(...)`: reescala la
  estimación de referencia (ya calculada con datos reales de red y
  precio) a la velocidad real medida. Es solo una multiplicación local
  — no hace ninguna consulta de red nueva por cada línea de log, así
  que no hay riesgo de saturar las APIs aunque el motor reporte la
  velocidad muy seguido.
- Como antes, si la moneda no tiene fuente de datos verificada (WOW,
  RTM, ALPH), se muestra "estimación no disponible" en vez de un número
  inventado — igual de honesto que la estimación de referencia.
- Probado de extremo a extremo simulando una línea real de xmrig contra
  una `App` de Tkinter de verdad (no solo con funciones aisladas), para
  no repetir el tipo de fallo de la entrada anterior. 127 tests en
  verde.

## 2026-08-23 (9) — `Iniciar minado.bat` instala Python solo si hace falta

Probaste el proyecto en un segundo ordenador (clonado desde cero) y no
funcionó: no tenía Python instalado, y hasta ahora el lanzador solo
comprobaba si ya estaba y, si no, te mandaba a instalarlo tú a mano.
Pediste que fuera de verdad "plug & play". Ahora `Iniciar minado.bat`,
si no encuentra `py` ni `python`, se instala Python él solo antes de
abrir la app:

1. Descarga el instalador oficial de Windows desde python.org (la
   misma fuente que usarías si lo hicieras tú a mano) con `curl`
   (viene incluido en Windows 10/11 modernos) o, si no está
   disponible, con PowerShell como alternativa.
2. Lo ejecuta en modo silencioso (`/quiet`) y **solo para tu usuario**
   (`InstallAllUsers=0`) — así no hace falta ser administrador ni
   aparece ningún permiso de Windows que aceptar, y no toca a otros
   usuarios del ordenador. Incluye Tkinter (`Include_tcltk=1`, hace
   falta para la ventana) y añade Python al PATH para la próxima vez
   (`PrependPath=1`).
3. Como el PATH recién añadido no se nota hasta abrir una ventana
   nueva, en esta misma ejecución se usa directamente la ruta donde
   Python acaba de instalarse, sin depender de PATH.

Fijé una versión concreta de Python en el propio `.bat`
(`PY_VERSION=3.13.15`, comprobado que el enlace de descarga funciona de
verdad antes de fijarla) en vez de "la última", por lo mismo que ya se
explicó para los motores de minado: es más fiable depender de un
número de versión conocido que de una URL que puede cambiar de forma
imprevisible. Habrá que actualizar ese número de vez en cuando; no es
urgente, cualquier Python 3.10 o más reciente sirve para este proyecto.

Si por lo que sea la descarga o instalación fallan (sin internet, red
bloqueada...), el `.bat` no se queda colgado ni da un error críptico:
avisa con un mensaje claro y, como último recurso, sigue apuntando a
instalar Python tú mismo desde python.org.

Probado de verdad en este ordenador: la descarga (con la misma línea
de `curl` del `.bat`, no una simulación) y la detección de la ruta de
instalación, sin necesidad de reinstalar Python de verdad sobre un
sistema que ya lo tiene (lo que sí quedó sin probar en esta sesión,
por no tener a mano un Windows limpio sin Python: pruébalo tú la
próxima vez que lo necesites en un ordenador nuevo, y dime cómo ha
ido).

## 2026-08-23 (10) — El instalador automático de Python no se disparaba: un alias falso de Windows

Lo probaste de verdad en un Windows sin Python y seguía sin funcionar.
La causa, esta vez confirmada con tu mensaje de error exacto, no tenía
nada que ver con lo que se explicó en la entrada anterior: Windows 10
y 11 traen de serie, sin que tú hagas nada, un "alias de ejecución" —
un acceso directo falso — para `python.exe` y `python3.exe` que abre la
Microsoft Store (o da el error que viste) si escribes `python` en una
consola y no tienes Python instalado de verdad. El problema es que ese
alias falso **sí aparece como "encontrado" para el comando `where`**,
que es justo lo que usaba `Iniciar minado.bat` para comprobar si ya
tenías Python. El `.bat` se lo creía, pensaba "ya está instalado" y
nunca llegaba a descargarlo de verdad — y al intentar arrancar la app
con ese Python falso, salía el mensaje de la Microsoft Store que viste.

Arreglado en `Iniciar minado.bat`: en vez de preguntar "¿existe algo
que se llame python en el PATH?" (`where`), ahora se **ejecuta de
verdad** (`python --version`) y se comprueba si responde correctamente
— el alias falso de Windows no lo hace, así que ya no engaña al
script. Lo mismo para `py`, por si acaso. Probado de nuevo con Python
real instalado en este ordenador (sigue detectándolo bien) — la
comprobación completa en un Windows limpio con el alias falso activo
la hizo Carlos, y con este cambio debería funcionar ya.

## 2026-08-23 (11) — "unable to get local issuer certificate": otro fallo real de un Windows recién instalado

Con Python ya instalado y la app abierta, al pulsar "Comenzar a minar"
salió un error de certificado SSL al consultar GitHub para descargar
xmrig. Investigué antes de tocar nada (esta vez sí hay un motivo
técnico claro, no era el antivirus): es un fallo conocido de Python en
Windows (bugs.python.org/issue26313). Cuando Python arranca una
conexión https, intenta cargar de golpe TODOS los certificados de
confianza del almacén de Windows — y si hay aunque sea uno que Python
no sepa leer (algo nada raro, hasta en un Windows recién instalado y
normal), la carga falla ENTERA y se queda sin ningún certificado de
confianza. Resultado: cualquier conexión https falla con "no se puede
verificar el certificado", aunque la web sea perfectamente de fiar y
la conexión a internet funcione bien.

La solución habitual que recomienda la comunidad de Python es instalar
el paquete externo `certifi` (`pip install certifi`) — pero eso no
sirve aquí: necesitaría la propia red para instalarse, y si la
verificación de certificados está rota, esa instalación por HTTPS
también fallaría (el mismo problema, dando vueltas). Así que se hizo
sin ningún paquete externo, solo con la librería estándar: nuevo
`src/red.py`, que en vez de cargar los certificados de Windows todos
de golpe, los carga **uno a uno** — así uno dañado no se lleva por
delante a los demás. Se usa en las tres únicas peticiones https del
proyecto (`instalador.py` para descargar motores, `ingresos.py` y
`estimacion_ingreso.py` para consultar precios e ingresos).

Probado de verdad: la nueva función funciona contra GitHub en este
ordenador, y hay un test que reproduce exactamente el fallo original
(un certificado "dañado" en medio de la lista) para comprobar que ya
no rompe la carga de los demás.

## 2026-08-23 (12) — El mismo mensaje SSL, pero una causa distinta: almacén de Windows "frío"

Abriste una segunda sesión de Claude Code en un tercer ordenador para
diagnosticar (sin tocar nada) por qué el arreglo anterior no bastaba
ahí, y trasladaste el informe. Buen diagnóstico, lo comprobé antes de
actuar (no me fío a ciegas ni de mis propias sesiones anteriores) y es
correcto: es el mismo mensaje de error, pero una causa distinta a la de
la entrada 11.

Windows no viene con todas las autoridades de certificación (CA)
públicas ya instaladas: las va guardando **bajo demanda**, la primera
vez que algo que usa Schannel (Edge, PowerShell, `curl.exe`...) valida
una web que las necesita ("Actualización automática de certificados
raíz"). Python, por dentro, usa OpenSSL en vez de Schannel, así que
`ssl.enum_certificates()` (lo que arregló la entrada 11) solo lee lo
que YA esté guardado — nunca dispara esa descarga. En un ordenador
donde nunca se ha abierto un navegador, ese almacén puede estar
prácticamente vacío de CA públicas, y entonces no hay nada que
enumerar: el arreglo anterior no tiene nada que cargar, aunque
funcione perfectamente.

Solución, otra vez sin ningún paquete externo de Python: en vez de
depender solo de que el almacén de Windows tenga lo necesario,
`Iniciar minado.bat` descarga con `curl` (que sí usa Schannel — de
paso "calienta" el almacén, como haría un navegador) un paquete de
certificados públicos de confianza a `bin/cacert.pem`: el mismo que
usan Mozilla y el paquete `certifi`, publicado oficialmente por el
propio proyecto curl (curl.se/ca/cacert.pem, con su suma de
comprobación verificada antes de usarlo). `src/red.py` lo carga como
fuente adicional, independiente de si el almacén de Windows está frío
o no. No se sube a git (ya cubierto por la regla `bin/*` del
`.gitignore`): es un fichero público que se puede volver a descargar en
cualquier momento, igual que los motores de minado.

Quedan entonces dos capas independientes cubriendo el mismo problema:
`bin/cacert.pem` (soluciona el almacén "frío") y la carga uno a uno del
almacén de Windows de la entrada 11 (soluciona un certificado dañado
en un almacén que sí tiene datos). Cualquiera de las dos basta por
separado; juntas cubren más casos que cualquiera sola.

## 2026-08-23 (13) — "Modo rendimiento": segundo acceso directo, con permiso de administrador, para minar más rápido

Viste en el registro de minado un aviso de xmrig: `failed to start
WinRing0 driver: "WinRing0x64.sys not found"` seguido de
`FAILED TO APPLY MSR MOD, HASHRATE WILL BE LOW`. No es grave — xmrig
sigue minando igual, solo un poco más despacio — pero pediste
explícitamente ir a por el máximo rendimiento posible, así que
investigué qué hace falta para eliminarlo del todo.

Hay dos optimizaciones de Windows detrás de ese aviso, con requisitos
distintos que conviene separar:

1. **El fichero que faltaba de verdad.** `src/instalador.py` solo
   copiaba el programa principal (`xmrig.exe`) a `bin/`, no el fichero
   `WinRing0x64.sys` que también trae la descarga (se queda dentro de
   la carpeta descomprimida). Arreglado: ahora se copian también los
   "ficheros acompañantes" que necesite cada motor (nueva clave
   `ficheros_acompanantes` en `src/motores.py`), tanto en instalaciones
   nuevas como en las que ya tenías (mientras siga existiendo la
   carpeta descomprimida original, cosa que ya comprobé que pasa en la
   práctica).
2. **Dos permisos de administrador con reglas distintas.** Investigué
   antes de tocar nada (fuentes: xmrig.com/docs/miner/randomx-optimization-guide/msr,
   y guías de configuración de "huge pages" en Windows):
   - **"MSR mod"** (~5-10% más rápido): necesita permisos de
     administrador **cada vez que xmrig arranca**, porque carga un
     controlador. No es un paso de una sola vez.
   - **"Huge pages"** (hasta ~20% más rápido): necesita conceder el
     permiso "Lock pages in memory" (`SeLockMemoryPrivilege`) a tu
     usuario de Windows, pero **solo una vez** — después, xmrig lo usa
     solo, sin admin, para siempre.

   Como el "MSR mod" pide permiso cada vez, meterlo en el flujo normal
   de "Iniciar minado.bat" rompería el "sin fricción" que es la razón
   de ser de este proyecto (aparecería un aviso de Windows cada vez que
   pulsaras el icono). En vez de eso, nuevo acceso directo separado:
   **`Iniciar minado (rendimiento máximo).bat`** — se auto-eleva a
   administrador (pide el permiso de Windows una vez, al abrirlo), le
   concede a tu usuario el permiso de "huge pages" (nuevo
   `src/rendimiento_windows.py`, usando directamente las funciones de
   seguridad de Windows con `ctypes` — sin ningún paquete externo como
   `pywin32`) y luego arranca la app con normalidad. Como el proceso
   entero queda elevado, xmrig (que arranca como hijo de la propia app)
   hereda esos permisos y puede usar el MSR mod también, sin pedir nada
   aparte. `Iniciar minado.bat` (el de siempre) sigue funcionando
   exactamente igual que hasta ahora, sin pedir nada — es tu elección
   qué icono abrir cada vez.

   Verificado de verdad, no solo "debería funcionar": corrí
   `src/rendimiento_windows.py` en esta máquina (con permisos de
   administrador reales) y comprobé con `secedit /export` que el
   permiso quedó concedido de verdad en la política de seguridad de
   Windows, no solo que la función devolviera "sin errores".

   La ventana ahora muestra arriba si estás en "🚀 Modo rendimiento"
   o en modo normal, para que sepas en cuál estás sin tener que
   adivinarlo.

Lo que no pude confirmar del todo aquí: si el MSR mod llega a aplicarse
de verdad en tu hardware. El aviso cambió de "no encuentro el fichero"
a "no puedo escribir el registro del procesador" — el fichero ya se
copia bien, pero escribir esos registros directamente seguía fallando.

**Corrección (misma sesión, un poco después):** dije que esta máquina
de desarrollo "parece ser una máquina virtual" — me equivoqué. Es tu
ordenador físico real; confundí una etiqueta "VM" que muestra xmrig
(sobre si tu CPU admite virtualización, no sobre si el propio xmrig
está corriendo dentro de una) con estar realmente virtualizado. La
causa real la encontré (y la comprobé de verdad en tu equipo, no
adivinada) en la siguiente entrada.

## 2026-08-23 (14) — La causa real del MSR mod: "Aislamiento del núcleo", y la app ahora puede desactivarlo (con tu permiso, cada vez)

Investigué la causa de verdad en vez de dar la VM por buena, y la
comprobé directamente en tu ordenador (no es una suposición):

```
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
  SecurityServicesConfigured        : {2}
  VirtualizationBasedSecurityStatus : 2   (activa y funcionando)
```

Tu Windows tiene activada **"Aislamiento del núcleo / Integridad de
memoria"** (también llamada HVCI): una protección de seguridad real de
Windows 11 que bloquea controladores de kernel antiguos o sin firmar,
como `WinRing0x64.sys` — el que necesita xmrig para el MSR mod. Es un
conflicto conocido y documentado entre esta protección y programas de
minado, no un fallo de nuestro código.

Aquí SÍ hacía falta preguntarte, porque tocar esto es una decisión de
seguridad real: te pregunté directamente si querías que la app pudiera
desactivarla, y me contestaste que sí, pero con reglas concretas que
implementé tal cual:

- **Solo desde "Iniciar minado (rendimiento máximo).bat"**, nunca desde
  el lanzador normal — igual que ya pasaba con el MSR mod y el permiso
  de administrador.
- **Se pregunta cada vez que hace falta**, con una ventana, antes de
  abrir la app: si la protección está activa, ¿quieres desactivarla
  ahora? Si dices que sí, la app la desactiva, avisa de que hace falta
  reiniciar el ordenador, y no abre la app todavía (hay que reiniciar
  primero para que el cambio se aplique de verdad). La próxima vez que
  abras "modo rendimiento", si ya está desactivada, no vuelve a
  preguntar y sigue directa a minar.
- **Al detener el minado o cerrar la app**, si fue la propia app quien
  la desactivó, pregunta si quieres volver a activarla. Si dices que
  no, te lo volverá a preguntar la próxima vez (no se te olvida sin
  que lo sepas). Si dices que sí, la reactiva y avisa de que hace falta
  reiniciar para que se aplique.

Cómo se hizo, en tres piezas nuevas, todas con librería estándar (nada
de paquetes externos):
- `src/aislamiento_nucleo.py`: lee el estado con PowerShell sobre la
  clase WMI oficial de Microsoft para esto (`Win32_DeviceGuard`, la
  misma que usé para comprobar tu equipo) y cambia el estado con la
  clave de registro que Microsoft documenta oficialmente
  (`HKLM\...\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity`,
  valor `Enabled`) — la fuente exacta está en
  learn.microsoft.com/windows/security/hardware-security/
  enable-virtualization-based-protection-of-code-integrity, no
  adivinada.
- `src/comprobar_aislamiento.py`: el script que pregunta antes de abrir
  la app (llamado desde el `.bat`).
- `src/formulario.py`: la pregunta de "¿lo reactivamos?" al detener el
  minado o cerrar la ventana.

Importante: **no toqué tu ajuste real durante esta sesión.** Comprobé
que la LECTURA del estado funciona de verdad en tu equipo (dio
"activo", justo lo que esperábamos). El cambio de estado en sí
(desactivar/reactivar) lo probé con pruebas automáticas que simulan el
registro de Windows, sin tocar el tuyo de verdad — esa acción solo
ocurrirá cuando tú la autorices desde el propio lanzador, nunca desde
aquí.

## 2026-08-24 — Segunda causa del MSR mod: la "lista de controladores vulnerables bloqueados" de Microsoft, independiente de Aislamiento del núcleo

Seguiste el flujo completo de la entrada anterior (desactivar
Aislamiento del núcleo, reiniciar, reabrir "modo rendimiento") y el MSR
mod seguía fallando: `FAILED TO APPLY MSR MOD, HASHRATE WILL BE LOW`.
En vez de suponer que el arreglo anterior no había funcionado,
investigué directamente en tu equipo, en vivo:

- Confirmé por código (`aislamiento_nucleo.esta_activo()`) que
  Aislamiento del núcleo seguía desactivado de verdad — no era eso.
- `WinRing0x64.sys` está presente en `bin/` — tampoco era el fichero
  que faltaba (entrada 13).
- Pero `sc query WinRing0_1_2_0` decía que el servicio del controlador
  ni siquiera llega a crearse.
- En el registro: `HKLM\SYSTEM\CurrentControlSet\Control\CI\Config\
  VulnerableDriverBlocklistEnable = 1`.

Ese valor es la **"lista de controladores vulnerables bloqueados"** de
Microsoft: activa por defecto en Windows desde la actualización de
2022 de Windows 11, y **es un ajuste totalmente independiente de
Aislamiento del núcleo** (desactivar uno no desactiva el otro, aunque
los dos puedan bloquear el mismo controlador). `WinRing0x64.sys` está
en esa lista porque tiene una vulnerabilidad real y documentada,
CVE-2020-14979: un proceso sin privilegios puede leer/escribir memoria
del sistema y llegar a control total (SYSTEM). Fuentes: KB5020779 de
Microsoft (support.microsoft.com/topic/kb5020779) y el propio registro
comprobado en tu máquina, no una suposición.

Pediste explícitamente ir a por el máximo rendimiento posible **a pesar
de la seguridad, avisando bien al usuario de la vulnerabilidad que
asume**. Implementado así:

- `src/lista_controladores_vulnerables.py`: mismo patrón que
  `aislamiento_nucleo.py` (leer con `winreg`, cambiar con `winreg`,
  nunca tocar nada por su cuenta, solo cuando se le pide
  explícitamente).
- `src/comprobar_aislamiento.py` se sustituyó por
  `src/comprobar_seguridad_rendimiento.py`: ahora comprueba las DOS
  protecciones (son independientes, pueden estar bloqueando el MSR mod
  a la vez, como te pasó a ti) y hace una sola pregunta combinada,
  nombrando cuál(es) están activas. El mensaje deja claro que
  desactivar la lista de controladores implica asumir la CVE conocida,
  y que el beneficio total (huge pages + MSR mod) es ~25-30% más
  hashrate frente al ~20% que ya tenías solo con huge pages.
- `src/formulario.py`: la pregunta de "¿reactivamos?" al detener el
  minado o cerrar la ventana ahora cubre las dos protecciones — si
  desactivaste las dos, te pregunta por las dos juntas; si solo una
  seguía activa (como te pasó, Aislamiento del núcleo ya estaba
  desactivado por la entrada anterior), solo pregunta por esa.

Verificado en tu equipo real: `lista_controladores_vulnerables.esta_activo()`
da `True`, igual que el registro comprobado a mano. El cambio de
estado (desactivar/reactivar) se probó con pruebas automáticas que
simulan el registro, no contra el tuyo de verdad — se aplicará solo
cuando tú lo autorices desde el propio lanzador, con el aviso de la
CVE delante.

## 2026-08-24 (16) — kawpowminer (GPU NVIDIA) no arrancaba: mismo tipo de fallo que WinRing0x64.sys, pero con DLLs de CUDA

Probaste minar Ravencoin (RVN) con GPU en otro ordenador y falló. Ese
mismo ordenador ejecutó otra sesión de Claude Code, que diagnosticó el
problema (sin minar de verdad, sin tocar el repo) y dejó el análisis en
un fichero `GPU_ERROR.md` que subiste a `develop` para que lo
resolviera. Comprobé el diagnóstico antes de aplicar nada, y es
correcto: `kawpowminer.exe`, en la build para NVIDIA (`cuda11`),
necesita dos DLLs que trae dentro de su propio `.zip`
(`nvrtc64_112_0.dll`, `nvrtc-builtins64_112.dll`) pero que
`src/instalador.py` no copiaba a `bin/` junto al ejecutable — solo
copiaba el `.exe`. Sin ellas, `kawpowminer.exe` ni siquiera llega a
arrancar (falla al cargar la DLL, antes de leer un solo argumento).

En vez de aplicar el arreglo propuesto en `GPU_ERROR.md` tal cual
(añadir esos dos nombres de fichero a una lista, igual que ya existía
para `WinRing0x64.sys` de xmrig), aquí generalicé la solución, porque
el problema de fondo es una clase de fallo, no un caso aislado:
mantener a mano una lista de nombres exactos por motor se desactualiza
en cuanto el proyecto original (kawpowminer, en este caso) suba de
versión — por ejemplo, el día que su CUDA empaquetado pase de la
versión 11.2 a otra, el nombre cambiaría a algo como
`nvrtc64_120_0.dll` y volveríamos a tener este mismo bug con un nombre
distinto.

Arreglo aplicado en `src/instalador.py`
(`_copiar_ficheros_acompanantes_si_faltan`): en vez de copiar solo los
nombres de una lista fija, copia a `bin/` **cualquier fichero de
librería/controlador** (`.dll`, `.sys`, `.so`, `.dylib`) que venga
dentro de la descarga del motor, sea cual sea su nombre exacto. Esto
cubre el caso de kawpowminer/NVIDIA de golpe, sigue cubriendo
`WinRing0x64.sys` de xmrig igual que antes (por eso se pudo quitar la
lista `ficheros_acompanantes` de `src/motores.py`, ya no hace falta) y,
de paso, protege contra el mismo tipo de fallo si algún día aparece en
lolMiner o en una versión futura de cualquiera de los tres motores.

Verificado de dos formas, no solo con mocks:
1. Nuevo test de regresión (`tests/test_instalador.py`) que reproduce
   exactamente el caso de `GPU_ERROR.md` con un `.zip` simulado.
2. **Descarga real** de kawpowminer desde GitHub en este ordenador
   (`instalador.asegurar_motor("kawpowminer", ..., fabricante_gpu="NVIDIA")`,
   sin mocks) — las dos DLLs aparecieron copiadas en `bin/` de verdad, y
   `bin/kawpowminer.exe --help` (el mismo comando que usó `GPU_ERROR.md`
   para reproducir el fallo, sin conectarse a ningún pool) ya devuelve
   la versión del programa en vez de fallar.

Lo que queda pendiente, y no se ha hecho aquí porque haría falta
conectarse a un pool real: confirmar que kawpowminer llega a minar RVN
de verdad contra la GPU (NVIDIA RTX 4060 Laptop en este ordenador). Ver
`CLAUDE.md` para la regla sobre no arrancar minado real sin pedirlo tú
en el momento.

Dato aparte que llevaba `GPU_ERROR.md`, y que decidí NO aplicar sin
comprobarlo: mencionaba que `nvidia-smi` detectó "RTX 5060" en el otro
ordenador donde se reprodujo el fallo, distinto de la "RTX 4060
Laptop" que dice `CLAUDE.md`. Eso no es una discrepancia real: son dos
ordenadores distintos (el tuyo, con la RTX 4060 Laptop, y el "otro
equipo" donde probaste GPU, con otra tarjeta) — así que no he tocado el
dato de `CLAUDE.md`, que sigue describiendo correctamente este
ordenador.

## 2026-08-24 (17) — RVN no mina en GPUs Blackwell (kawpowminer), y KAS ya no se puede minar con GPU (lolMiner)

Nueva ronda de pruebas en el "otro equipo" (GPU NVIDIA RTX 5060,
generación Blackwell), con otro `GPU_ERROR.md` subido a `develop` con
el diagnóstico. Dos problemas distintos, ninguno arreglable tocando
nuestro código — verifiqué el análisis antes de actuar y es correcto en
los dos casos, con reproducción real (`--benchmark`/`--list-algos`, sin
pool ni wallet de por medio):

**RVN (kawpowminer) — "invalid device symbol"**: el bug de las DLLs de
NVRTC de la entrada 16 ya está resuelto, kawpowminer arranca de verdad,
pero falla al generar el DAG en la GPU. Causa: kawpowminer 1.2.4 trae
compilado un CUDA 11.2 que no conoce la arquitectura "Compute 12.0" de
las GPUs Blackwell (RTX 50, lanzadas en 2025) — es el mismo fallo
conocido y documentado que kawpowminer/ethminer arrastran desde 2020
cada vez que sale una GPU NVIDIA más nueva que su CUDA interno (varios
issues de años distintos, mismo error exacto, con GPUs cada vez más
recientes). No es arreglable sin recompilar kawpowminer contra un CUDA
más moderno, algo fuera del alcance de este proyecto.

Decisión: **RVN se queda como estaba** (`soportado_por_minar_hoy: True`
en `monedas.py`), porque el problema es específico de esta generación
de GPU muy reciente, no de kawpowminer en general — en una GPU NVIDIA
algo más antigua (como la RTX 4060 Laptop de este ordenador) no hay
motivo para que falle igual. Lo que sí cambié:
- `src/minar.py` (`interpretar_linea`): antes, este error se mostraba
  tal cual, en inglés y con jerga técnica de CUDA ("cudaMemcpyToSymbol
  failed with error invalid device symbol..."). Ahora se reconoce ese
  caso concreto y se traduce a una frase clara: que la tarjeta es
  demasiado nueva para el programa de minado, y que no es un fallo de
  esta app.
- `src/monedas.py`: nota (`riesgo`) en la entrada de RVN explicando la
  limitación, para que quede documentada donde se consulta el catálogo.
- README.md y `CLAUDE.md` actualizados con el mismo aviso.

**KAS (lolMiner) — "--algo option KASPA is not supported"**: causa 100%
confirmada, sin ambigüedad. `lolMiner` retiró el algoritmo kHeavyHash
(el que usa Kaspa) de sus versiones recientes — confirmado ejecutando
`lolMiner.exe --list-algos` en la 1.98a (la última release oficial):
"KASPA" no aparece en absoluto en la lista. Según varios issues del
propio repositorio de lolMiner (2023-2024) y fuentes externas, el
motivo es que la red de Kaspa está dominada por ASICs dedicados desde
esos años, así que minar kHeavyHash con GPU dejó de compensar y el
propio autor quitó el algoritmo. A diferencia de RVN, esto no depende
de qué GPU tengas: **no hay ninguna forma de minar KAS con GPU hoy,
con el catálogo de motores de este proyecto, en ningún ordenador.**

Decisión: **quitar KAS de las monedas activas** (opción que el propio
diagnóstico recomendaba, la más honesta):
- `src/minar.py`: eliminada la entrada `"KAS"` de `MONEDAS_SOPORTADAS`
  (ya no se genera ningún comando para ella).
- `src/monedas.py`: `soportado_por_minar_hoy: False` para KAS, con nota
  (`riesgo`) explicando el motivo y la fecha en que se confirmó.
- El formulario deja de mostrar KAS en el desplegable de GPU
  automáticamente (usa el mismo filtro `soportado_por_minar_hoy` que ya
  existía; no hizo falta tocar `formulario.py`).
- README.md, `CLAUDE.md` y la cabecera de `wallets.md` actualizados.
  Pusiste tu wallet de Kaspa en `wallets.md` antes de este diagnóstico
  (parte de las pruebas del punto 3 del `GPU_ERROR.md` anterior) — la
  dejé tal cual, no borro datos tuyos; simplemente no se usará hasta
  que en algún momento se decida soportar una moneda equivalente
  (lolMiner mantiene Karlsen y Pyrin, familia de algoritmo parecida
  pero monedas distintas — no aplicado, a decidir si algún día
  interesa).

Verificado: 170 tests en verde (se quitó el test que validaba el
comando de KAS —ya no tiene sentido, probaba un comportamiento que
sabemos roto a propósito— y se añadió uno nuevo para la traducción del
error de RVN). No se ha ejecutado minado real de ninguna de las dos
monedas en ningún pool; toda la reproducción fue offline
(`--benchmark`/`--list-algos`), como en la entrada 16.

Fuentes: los issues y enlaces exactos consultados por la sesión que
hizo el diagnóstico están citados dentro del propio `GPU_ERROR.md`
(ya borrado de la raíz una vez incorporado aquí) — repositorios
oficiales de `RavenCommunity/kawpowminer`, `ethereum-mining/ethminer` y
`Lolliedieb/lolMiner-releases`.

## 2026-08-24 (18) — Minado real de RVN en ESTE ordenador: mismo tipo de fallo (kawpowminer, GPU NVIDIA moderna), y arreglado el silencio total del registro

Probaste minar RVN con GPU en este mismo ordenador (RTX 4060 Laptop) y
viste: se conecta al pool bien, pero después no aparece ningún log más,
y la estimación de ingreso real se queda en 0,000000. Pediste
expresamente que hiciera una prueba de minado REAL (no simulada) para
ver exactamente lo mismo que tú — lo hice, con tu wallet real de RVN,
en sesiones cortas (35-180 segundos, deteniendo el proceso yo mismo al
final de cada una).

**Lo que encontré, reproducido 4 veces seguidas de forma idéntica:**
kawpowminer se conecta al pool, autoriza el worker, genera el DAG de la
GPU correctamente (esta vez SÍ, a diferencia de la RTX 5060 de la
entrada 17) y, justo al terminar de generarlo y arrancar el cálculo
real, **el proceso se cierra solo**, con el código de salida
`3221226505` (`0xC0000409` en hexadecimal — `STATUS_STACK_BUFFER_OVERRUN`
de Windows, un fallo de corrupción de memoria detectado por el propio
sistema). No es un cuelgue: el proceso muere de verdad, cada vez, en el
mismo punto exacto ("Generated DAG + Light..." es la última línea que
llega a imprimir).

Es la MISMA familia de problema que la entrada 17 (kawpowminer 1.2.4
trae un CUDA de 2021 demasiado antiguo para las GPUs NVIDIA actuales),
pero con un síntoma distinto: en la RTX 5060 (Blackwell) fallaba ANTES,
al generar el DAG ("invalid device symbol"); en esta RTX 4060 Laptop
(Ada Lovelace) el DAG se genera bien pero revienta justo DESPUÉS, al
arrancar el cálculo. **Con esto, kawpowminer ha fallado en las dos
únicas GPUs NVIDIA reales con las que se ha probado este proyecto** —
ninguna de las dos ha conseguido minar RVN todavía. Es una limitación
real del propio kawpowminer 1.2.4 (un binario de terceros que ya no se
actualiza con frecuencia), no de nuestro código: el comando que
`minar.py` genera es correcto, kawpowminer arranca, se conecta y
autentica bien — el fallo ocurre dentro del propio programa, en su
código CUDA.

**El motivo real de "no aparece ningún log más" es más grave que solo
una traducción que falta: el registro se quedaba completamente mudo,
sin ningún aviso, cuando el motor de minado se moría por su cuenta.**
Investigando esto encontré DOS problemas separados, arreglé los dos:

1. **`interpretar_linea` no reconocía casi ningún formato real de
   kawpowminer.** Comprobado con la salida real capturada: ni la línea
   de progreso del DAG ("Generating/Generated DAG..."), ni el informe
   periódico de velocidad (formato real: `A0 0.00 h - cu0 0.00`, que NO
   contiene la palabra "speed" como sí hace xmrig) coincidían con
   ninguno de los casos que ya existían. Resultado: aunque kawpowminer
   SÍ estaba dando señales de vida cada 5 segundos, el registro sencillo
   no mostraba nada de eso. Arreglado en `src/minar.py`
   (`interpretar_linea`): ahora se traducen esas líneas también
   ("🧮 Preparando la GPU (generando el DAG)...", "🧮 GPU lista,
   arrancando el cálculo real", y la velocidad real con el mismo formato
   que ya se usaba para xmrig).
2. **Cuando el motor se cerraba solo (crash), no había NINGÚN aviso, ni
   siquiera en el log técnico completo.** El hilo que lee la salida del
   proceso simplemente terminaba en silencio en cuanto el proceso moría,
   porque ya no había más líneas que leer — nunca se comprobaba el
   código de salida. Arreglado en `src/minar.py` (`SesionMinado`,
   `iniciar_minado`): ahora, si el proceso termina con un código
   distinto de 0 y NO fue porque el usuario pulsó "Detener minado"
   (nuevo campo `SesionMinado.detenido_por_usuario`, para no avisar de
   "error" cuando el cierre lo pediste tú), se muestra un aviso claro
   explicando que el programa de minado se cerró solo y que no es un
   fallo de esta app.

Con los dos arreglos juntos, minar RVN en esta GPU ahora se ve así en
el registro (verificado con otra prueba real): conecta → "preparando
la GPU..." → "velocidad: 0.00 h/s" unas cuantas veces (normal mientras
genera el DAG) → "GPU lista, arrancando el cálculo real" →
inmediatamente el aviso claro de que el programa se cerró solo. Antes
de este arreglo, después de "conectado al pool" no había NADA más, para
siempre — exactamente lo que describiste.

**Decisión sobre RVN**: se queda como "soportada" en `monedas.py` (el
código de este proyecto es correcto), pero con la nota de riesgo
actualizada explicando que, a día de hoy, no se ha conseguido un minado
real completo en ninguna GPU NVIDIA probada — ni la tuya ni la del otro
equipo. README.md y `CLAUDE.md` actualizados en el mismo sentido. Si en
el futuro aparece una versión más moderna de kawpowminer (o un motor
KawPow alternativo mejor mantenido), merece la pena reintentarlo.

Sobre tu segunda pregunta ("dice que no puede utilizar el modo de
máximo minado con GPU, no sé por qué"): no encontré ningún mensaje así
en el código de esta app — ni `formulario.py`, ni el lanzador de
rendimiento máximo, ni los módulos de aislamiento del núcleo/lista de
controladores mencionan la GPU en ningún sitio (esas dos protecciones
solo afectan al MSR mod de xmrig, que es cosa de CPU). Puede que sea un
mensaje de Windows o del propio panel de NVIDIA, ajeno a este proyecto.
Pendiente: que Carlos pase el texto exacto del aviso para poder
localizar la causa real en vez de suponerla.

Verificado: 175 tests en verde (5 nuevos: 2 sobre el aviso sesión
cuando el proceso muere solo, 3 sobre las traducciones nuevas de
kawpowminer). Las pruebas de minado real (con tu wallet de RVN, contra
el pool real) se hicieron directamente con `minar.iniciar_minado`
desde un script aparte (no desde `minar.py`/`formulario.py` tal cual,
para poder controlar la duración exacta y detener el proceso yo mismo
a los pocos segundos), nunca dejadas corriendo sin vigilancia.

## 2026-08-24 (19) — ALPH ya tiene estimación de ingreso, y arreglado que el hashrate real de lolMiner no se leía

Confirmaste que ya has minado ALPH de verdad con tu GPU (probé yo mismo
lolMiner en esta misma máquina un poco antes, con una wallet de prueba,
y detecté la GPU y arrancó CUDA sin problema — coincide con lo tuyo).
Preguntaste tres cosas.

**1) Por qué no había estimación de ingreso para ALPH.** La entrada del
2026-08-23 que investigó esto decía que no se encontró una fuente
fiable para la dificultad/hashrate de red de Alephium. Investigué de
nuevo, y esta vez sí hay una: el propio pool que ya usamos por defecto
(`alephium.herominers.com`, HeroMiners) expone `/api/stats` con
dificultad de red en vivo, igual que ya usábamos para Salvium/Zephyr —
antes no se había probado con ALPH en concreto. Añadido en
`src/estimacion_ingreso.py` (`_fetch_alph`, `REFERENCIA_HASHRATE["ALPH"]`,
id de CoinGecko "alephium" verificado con precio real y contrastado
contra el que reporta el propio pool: coinciden).

No lo di por bueno sin comprobarlo — dos cosas que fallaron a la
primera y que arreglé antes de terminar:
- El parser genérico que ya usábamos para bloques de HeroMiners
  (`_reward_de_bloques_herominers`, que asume que el primer token largo
  alfanumérico de un bloque es la dirección del minero) se confunde con
  ALPH: sus bloques traen un campo hexadecimal extra
  (`827b000...b621`) que "parece" una dirección para ese parser genérico
  y da una recompensa completamente equivocada. Arreglado con un parser
  específico (`_reward_alph_de_bloques`) que busca el campo que de
  verdad tiene forma de dirección real de Alephium (la misma regex que
  ya usa `minar.py` para validar la wallet — una dirección real nunca
  contiene "0", el campo hexadecimal problemático está lleno de ceros).
- El campo `pool.stats.averageReward`, que en teoría daba la recompensa
  ya calculada sin tener que parsear nada, resultó no ser fiable: en
  peticiones reales viene `null` parte del tiempo. Descartado a favor
  del parser de bloques de arriba, que sí es consistente.

Antes de dar la fórmula por buena (la misma que XMR/SAL/ZEPH:
`moneda_por_hora = ref * recompensa * 3600 / dificultad`, que asume que
"dificultad" son hashes esperados por bloque — una conversión "delicada"
según el propio docstring del módulo), la contrasté contra un dato
real independiente: los pagos diarios reales del pool
(`pool.stats.daily_earnings`) divididos entre su hashrate combinado
(`pool.stats.hashrate`) dan un ingreso por hash muy parecido al que
calcula la fórmula para el hashrate real de tu GPU — se valida sola, no
es una cifra inventada.

**Resultado honesto: a tu velocidad real (1055.99 Mh/s), ALPH da
aproximadamente 0,0057 $/hora — unos 0,00014 $/día.** Es una cifra
real, no un fallo de cálculo (contrastada como se explica arriba): la
red de Alephium tiene un hashrate combinado altísimo (varios PH/s) para
un precio muy bajo, así que el reparto por hash individual es minúsculo.
No es que "no se pueda estimar" — es que, con los datos reales de hoy,
apenas se gana nada.

**2) El log de velocidad de lolMiner no se leía para el hashrate real.**
Bug real, mismo tipo que el de kawpowminer de la entrada 18: el formato
que se había documentado antes ("Total: X mh/s", visto en registros
compartidos por usuarios) resultó no coincidir con lo que lolMiner
imprime de verdad minando ALPH con una sola GPU: `"Average speed (15s):
1055.99 Mh/s"`, sin la palabra "Total" en ningún sitio. El patrón
antiguo nunca coincidía con esta salida real, así que la estimación con
tu hashrate real nunca se actualizaba (aparte de que antes ni siquiera
había estimación de referencia con la que escalar). Arreglado en
`src/minar.py`: se prueban los dos formatos, con preferencia por
"Total" (el agregado, cuando hay más de una GPU y sí aparece) sobre
"Average speed" (respaldo para una sola GPU). De paso, `interpretar_linea`
también mostraba esta línea de forma redundante ("Velocidad: speed
(15s): ...") porque contiene la palabra "speed" y caía en el caso
genérico antes de llegar al específico — arreglado con el mismo cambio.

**3) ¿Hay monedas de GPU más rentables que no tengamos?** Del catálogo
completo (`src/monedas.py`, investigado el 2026-08-20), solo RVN, KAS y
ALPH tienen motor de minado registrado hoy — el resto (Ergo, Ethereum
Classic, Flux, Zcash, Bitcoin Gold, Beam, Firo, Conflux, Zano, Nexa,
Radiant, Neoxa...) están en el catálogo pero sin motor implementado
todavía, así que hoy por hoy no son opciones reales, solo candidatas
para el futuro. De las tres implementadas: KAS ya no es minable con
ningún hardware (entrada 17), RVN falla en las dos GPUs NVIDIA
modernas probadas (entradas 17 y 18), y ALPH funciona pero, con datos
reales, apenas rinde nada en esta GPU. Es coherente con la realidad más
amplia del sector en 2026: la minería de altcoins por GPU lleva años
cada vez más exprimida por ASICs y por el hashrate combinado de minería
a gran escala — un portátil individual ya no es muy competitivo salvo
en monedas muy concretas. Si Carlos quiere, el siguiente paso sería
investigar una candidata concreta del catálogo (Ergo es la más citada
habitualmente como viable con GPU de consumo) siguiendo el mismo
proceso de siempre: pool, formato de comando y comisión con fuentes
fiables antes de registrar un motor nuevo — no aplicado todavía, a la
espera de que lo pida.

Verificado: 177 tests en verde (antes 175). La estimación de ALPH y el
arreglo de lolMiner se comprobaron contra la API real del pool y con la
línea de log real capturada minando de verdad, no solo con datos
simulados.

## 2026-08-24 (20) — Investigadas y añadidas las monedas de GPU con mejor ingreso real: Iron Fish, Ergo y Beam

Pediste implementar las monedas de GPU con mejores ingresos, sin mirar
coste ni consumo. En vez de adivinar o reutilizar el ranking de
2026-08-20 (`orden_respaldo` en `monedas.py`, que ya sabíamos poco
fiable: KAS resultó no minable y ALPH apenas rinde), investigué con
datos en vivo antes de decidir nada.

**Fuente de ranking real**: `whattomine.com/coins.json` (la misma web
que se intentó usar al principio del proyecto, que entonces no cubría
ninguna de nuestras monedas) SÍ tiene hoy un índice de "profitability"
en vivo para 43 monedas, muchas de ellas minables por GPU. Descargado y
ordenado de mayor a menor. Antes de elegir candidatas, descarté las que
no tenían sentido real: monedas extremadamente pequeñas/con algoritmo
propio raro (Pearl, EPIC-ProgPow — máxima puntuación pero muy
arriesgadas, sin motor de minado mainstream claro), entradas "Nicehash-*"
(no son monedas, es un mercado), y cualquiera cuyo algoritmo fuera
KawPow (Evrmore, Neoxa, Frencoin, Neurai...) — **descartadas a
propósito**, porque ya sabemos que kawpowminer falla en las dos GPUs
NVIDIA modernas que hemos probado (entradas 17-18): añadir más monedas
con el mismo motor roto no soluciona nada.

De las candidatas que quedaron con puntuación alta y algoritmo
"normal", el criterio decisivo fue: **¿la soporta lolMiner?** — el
motor que ya confirmamos funcionando sin fallos en esta GPU con ALPH
(entrada 19), evitando por completo el riesgo de repetir el problema de
kawpowminer. Comprobé el listado exacto de algoritmos ejecutando
`lolMiner.exe --list-algos` en esta máquina (fuente 100% verificada, no
un README):

```
KARLSENV2   Karlsenhash V2   1.0
FISHHASH    FishHash         1.0
AUTOLYKOS2  Autolykos V2     1.5
BEAM-III    BeamHash III     1.0
```

**Karlsen (KLS)**, con la puntuación más alta de las candidatas serias
(1142, justo detrás de Pearl/EPIC), quedó descartada por ahora: no
encontré ningún pool que responda de verdad (`karlsen.herominers.com`,
`kls.2miners.com`, `woolypooly`... ninguno resuelve o responde), aunque
el algoritmo sí está soportado por lolMiner. Sin un pool real no hay
forma de minarla, así que no se implementó — queda como candidata para
retomar si aparece un pool en marcha.

Las tres que sí tienen pool real (HeroMiners, el mismo proveedor que ya
usamos para SAL/ZEPH/ALPH) y algoritmo soportado por lolMiner:

- **Iron Fish (IRON)**, FishHash — puntuación whattomine 699.
- **Beam (BEAM)**, BeamHash III — puntuación 511.
- **Ergo (ERG)**, Autolykos V2 — puntuación 451.

Las tres muy por encima de RVN (618, pero no funciona) y de ALPH (que
ni siquiera aparece en el ranking de whattomine — coherente con lo
minúsculo de su ingreso real, entrada 19).

**Verificado antes de implementar, no dado por hecho:**
- Los tres pools (`ironfish.herominers.com`, `ergo.herominers.com`,
  `beam.herominers.com`) responden de verdad y dan dificultad de red en
  vivo.
- Los tres precios existen en CoinGecko con datos reales ("iron-fish",
  "ergo", "beam-2").
- El formato de bloque de los tres SÍ funciona con el parser genérico
  ya existente (`_reward_de_bloques_herominers`) — revisado campo a
  campo para los tres, ninguno tiene el problema del campo hexadecimal
  que sí tenía ALPH (entrada 19).
- **Prueba real breve en esta GPU** (RTX 4060 Laptop), con direcciones
  de prueba (no wallets reales, solo para comprobar que el motor
  arranca — igual que se hizo antes con ALPH): las tres detectan la
  GPU, seleccionan el algoritmo correcto y calculan sin ningún fallo de
  CUDA. ERG fue rechazada por el pool por la dirección falsa (esperado,
  y confirma que el aviso de "el programa se cerró solo" de la entrada
  18 funciona también aquí). IRON y BEAM llegaron a reportar velocidad
  real (aunque en 0, por no tener wallet real todavía).

**Bug real encontrado de paso, mismo tipo que el de la entrada 19**:
BeamHash (familia Equihash) no mide en H/s sino en "soluciones por
segundo" (`Sol/s`) — visto en la prueba real de BEAM
(`"Average speed (15s): 0.0 sol/s"`). El patrón de `minar.py` para
lolMiner solo reconocía sufijos `kh/mh/gh/h`, así que ni se traducía en
el registro sencillo ni se podía escalar el ingreso con la velocidad
real. Arreglado añadiendo la familia de unidades `sol/ksol/msol/gsol`
junto a las de H/s.

Implementado en el mismo patrón que las monedas existentes:
`src/minar.py` (`MONEDAS_SOPORTADAS`), `src/monedas.py`
(`MONEDAS_GPU`), `src/estimacion_ingreso.py` (reutilizando
`_fetch_cryptonote_herominers`, sin necesitar un parser especial como
ALPH). Reordené también el `orden_respaldo` de KAS/RVN/ALPH y de estas
tres nuevas para que refleje el ranking real de whattomine en vez del
ranking a ciegas de 2026-08-20 (ETC y CFX, que no están implementadas,
se movieron a números libres para no chocar).

**Importante — ninguna de las tres está "confirmada en hardware real"
todavía**: la prueba fue solo técnica (arranca, calcula, no revienta),
no un minado real de principio a fin con una wallet de verdad y comparios
aceptados por el pool, así que en `monedas.py` NO se marcó
`confirmado_en_hardware_real` para ninguna de las tres (a diferencia de
ALPH, que sí se confirmó de verdad) — se marcarán en cuanto Carlos
confirme un minado real, siguiendo la misma convención que ya existía.

Verificado: 185 tests en verde (antes 177). De paso, endurecido otro
test flaky preexistente
(`test_autosana_ficheros_acompanantes_de_una_instalacion_previa` en
`test_instalador.py`, visto fallar una vez durante esta sesión) con el
mismo arreglo ya aplicado antes a un test hermano: mockear
`motores.shutil.which` para no depender de si el PATH real de la
máquina tiene algo llamado "xmrig".

## 2026-08-24 (21) — "La GPU está al 0%" — no era cierto: el Administrador de tareas de Windows mostraba el motor equivocado (y de paso, IRON queda confirmado)

Carlos lanzó minado real (XMR por CPU + IRON por GPU) y vio la GPU dar
un pico puntual y quedarse en 0% — con los logs diciendo que todo iba
bien. Pidió investigar el minado en marcha, y como el proceso real
seguía corriendo en su equipo, lo investigué en vivo, en dos fases.

**Primera comprobación, con el proceso de Carlos ya en marcha**: usé el
contador de Windows que atribuye uso de GPU por proceso
(`Get-Counter '\GPU Engine(*)\Utilization Percentage'`, filtrado por el
PID de lolMiner) y daba 0% también ahí, con los 21 hilos del proceso en
estado "Wait". Con esa evidencia dije que lolMiner parecía realmente
parado — **resultó ser una conclusión equivocada, corregida en la
segunda fase de abajo**, documentado aquí en vez de callado.

**Segunda fase, con permiso explícito de Carlos** ("lanza tú el
proceso"): arranqué yo mismo un minado real de IRON, con su wallet real
(ya en `wallets.md`), vigilando el mismo contador de GPU por proceso
cada ~4 segundos durante 157 segundos seguidos, en paralelo al log real
del propio lolMiner. Resultado, inequívoco:

- lolMiner reportó una velocidad real y estable de **16-17 Mh/s**
  durante casi todo el tiempo.
- **Dos comparios aceptados de verdad por el pool** ("Share accepted").
- El contador de Windows por proceso siguió dando **0% en las 34
  muestras**, sin ni una sola excepción, durante los mismos 157
  segundos en los que lolMiner estaba demostrablemente calculando y
  enviando trabajo válido al pool.

Conclusión: **lolMiner SÍ está minando correctamente. El problema es de
medición, no de minado.** Contrastado con fuentes: es un problema
conocido y bien documentado de Windows — tanto el Administrador de
tareas como (en este caso) el contador `GPU Engine` que usé miden por
defecto el motor **"3D"** de la tarjeta, que un programa de cálculo por
GPU (CUDA, como lolMiner) nunca usa. El motor que sí usan estos
programas se llama **"Cuda"** (o "Compute"), y no se muestra por
defecto — hay que cambiarlo a mano en cada gráfica del Administrador de
tareas (clic en la flecha desplegable de una de las cuatro gráficas de
GPU → elegir "Cuda" en vez de "3D"/"Copia"/etc.). El pico inicial que
vio Carlos coincide con esta explicación: es probable que fuera
actividad real del motor 3D durante la inicialización del contexto de
CUDA (que sí lo toca brevemente), y que después el trabajo real pasó
al motor "Cuda" que ni el Administrador de tareas ni mi propio contador
(sin filtrar por tipo de motor) estaban mostrando.

Con esto, **Iron Fish (IRON) queda confirmado en hardware real** —
`monedas.py` actualizado (`confirmado_en_hardware_real: True`), pasa a
mostrarse con ✅ en vez de 🧪. Ergo y Beam siguen sin confirmar (no se
han probado con wallet real todavía).

Lección para la próxima vez que algo "parezca" no funcionar mirando el
Administrador de tareas o un contador de rendimiento de Windows con
minado por GPU: comprobar primero el propio registro del motor de
minado (comparios aceptados, velocidad reportada) antes de fiarse de
una gráfica de uso — con CUDA, esa gráfica casi siempre está mirando
el motor equivocado por defecto.
