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
