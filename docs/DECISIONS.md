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

## 2026-08-20 — El ejecutable de XMRig no se guarda en el repositorio

XMRig es un programa grande y distinto para cada sistema operativo
(Windows, Mac, Linux). En vez de guardarlo dentro del repositorio, el
script lo busca en tu ordenador o en una carpeta `bin/` local que tú
rellenas tú mismo siguiendo las instrucciones de `bin/LEEME.md`.
