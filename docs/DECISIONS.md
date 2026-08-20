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

## 2026-08-20 — El ejecutable de XMRig no se guarda en el repositorio

XMRig es un programa grande y distinto para cada sistema operativo
(Windows, Mac, Linux). En vez de guardarlo dentro del repositorio, el
script lo busca en tu ordenador o en una carpeta `bin/` local que tú
rellenas tú mismo siguiendo las instrucciones de `bin/LEEME.md`.
