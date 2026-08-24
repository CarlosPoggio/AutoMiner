# RVN/kawpowminer no mina en esta GPU (Blackwell, "Compute 12.0") — para la siguiente sesión de Claude Code

**Esto es un problema distinto y nuevo, no el de las DLLs de NVRTC.**
Ese ya está resuelto (commit `f50777f`, verificado en esta máquina: las
DLLs se copian bien y `kawpowminer.exe --version` arranca sin problema).
Este es el **siguiente** obstáculo, ya con el motor arrancando de
verdad: la GPU no consigue minar.

## El error que vio Carlos (en un intento real de minado)

```
[GPU] ❌ cu 13:53:34 cuda-0 Unexpected error CUDA error in func
set_constants at line 180 calling cudaMemcpyToSymbol(d_dag, &_dag,
sizeof(hash64_t*)) failed with error invalid device symbol on CUDA
device 01:00.0
```

## Cómo se ha reproducido (sin conectarse a ningún pool)

kawpowminer trae un modo de benchmark/simulación pensado exactamente
para esto: `-M <bloque>` no necesita ningún `-P` (pool) — "no
connection specification is needed" (texto literal de
`kawpowminer --help-ext test`).

```
$ ./bin/kawpowminer.exe -U -M 0
...
cu 13:55:35 cuda-0    Using Pci Id : 01:00.0 NVIDIA GeForce RTX 5060 (Compute 12.0) Memory : 7.96 GB
 i 13:55:35 sim       Epoch : -1 Difficulty : 4.29 Gh
 i 13:55:35 sim       Job: ... block 0 localhost:0
 i 13:55:35 sim       Using block 0, difficulty 1
[el proceso termina en seco justo al generar el DAG en la GPU, mismo punto que el error de Carlos]
```

Se reproduce siempre, 100% de las veces, sin red y sin wallet real de
por medio — el fallo es anterior a cualquier dato del pool.

También se ha probado el otro camino que sabe usar kawpowminer, por si
esquivaba el problema: **OpenCL en vez de CUDA** (`-G` en lugar de
`-U`, mismo modo `-M 0` sin pool):

```
$ ./bin/kawpowminer.exe -G -M 0
No OpenCL platforms found
Error: No usable mining devices found
```

Esta máquina no tiene ningún ICD de OpenCL instalado/expuesto para la
GPU (problema aparte, de driver/sistema — ver más abajo). Así que hoy
por hoy **ninguno de los dos caminos de kawpowminer mina en esta GPU**.

## Causa raíz (ya no es un bug de este repo)

`kawpowminer.exe` reporta la tarjeta como **"Compute 12.0"** — la
GPU (NVIDIA GeForce RTX 5060, generación Blackwell) usa una
arquitectura de cómputo que solo empezó a soportarse de verdad a
partir de CUDA 13.0. Pero `kawpowminer` 1.2.4 (su última versión real,
de hace varios años) trae por dentro el compilador NVRTC de **CUDA
11.2** (las mismas DLLs `nvrtc64_112_0.dll` que arreglamos antes) —
esa versión de CUDA no conoce siquiera la arquitectura de esta tarjeta.

Este mismo error exacto — `invalid device symbol` en
`set_constants`/`cudaMemcpyToSymbol(d_dag...)` — es un fallo conocido
y repetido de kawpowminer/ethminer desde 2020-2021, cada vez que sale
una GPU NVIDIA más nueva que el CUDA que trae el binario (se ha
reportado con GTX 1660 Ti, RTX 2060/2080, RTX 3060/3090...). Con esta
GPU (la más nueva del mercado en 2026) pasa exactamente lo mismo, un
escalón más.

**Conclusión importante: esto no se arregla tocando código de
AutoMiner.** El bug de las DLLs (la vez anterior) sí era nuestro —
`instalador.py` no copiaba unos ficheros que debía. Este es distinto:
es una limitación del propio `kawpowminer.exe`, un binario de terceros
que no controlamos y que ya no se actualiza con esa frecuencia. No hay
ningún cambio en `src/` que le enseñe a un CUDA 11.2 ya compilado a
entender una arquitectura de GPU que no existía cuando se compiló.

## Caminos posibles (a decidir, no aplicado nada todavía)

1. **Arreglar el OpenCL de esta máquina y probar por ahí.** El "No
   OpenCL platforms found" sugiere que el driver de NVIDIA instalado
   aquí no tiene (o no expone) el componente ICD de OpenCL — sí es
   algo que en principio se podría reparar (reinstalando/reparando el
   driver de NVIDIA con ese componente). El runtime de OpenCL lo
   mantiene NVIDIA al día con cada driver nuevo (a diferencia del CUDA
   11.2 fijo que trae kawpowminer), así que tiene más probabilidad de
   funcionar en una GPU tan nueva — pero no hay garantía hasta
   probarlo, y tocar el driver del sistema es un cambio que no debería
   hacer sin que tú (o quien tenga esta sesión) lo autorice.
2. **Buscar un motor de minado KawPow alternativo, más mantenido, con
   soporte de CUDA moderno**, y registrarlo en `motores.py` siguiendo
   el proceso ya descrito en `CLAUDE.md` (investigar pool, formato de
   comando y comisión con fuentes fiables antes de nada).
3. **Probar primero las otras monedas de GPU que ya están
   implementadas (KAS, ALPH)**, que usan `lolMiner` en vez de
   `kawpowminer` — es un motor bastante más mantenido, así que podría
   no tener este problema en absoluto con una GPU tan nueva. Es la
   comprobación más barata de las tres (no hace falta escribir código
   nuevo, solo probar), y daría una respuesta rápida a si esta GPU
   puede minar algo de GPU hoy mismo mientras se decide qué hacer con
   RVN/kawpowminer.

Mi recomendación, si te preguntan: empezar por el punto 3 (barato de
probar, podría desbloquear minado de GPU ya mismo con otra moneda) y
tratar el problema de RVN/kawpowminer en esta GPU como una limitación
conocida a documentar, no algo urgente de arreglar ya.

## Fuentes consultadas

- [CUDA Error with RTX 3060 · Issue #61 · RavenCommunity/kawpowminer](https://github.com/RavenCommunity/kawpowminer/issues/61)
- [DAG CUDA (ver 10.2) error: func set_constants at line 110 invalid device symbol · Issue #2047 · ethereum-mining/ethminer](https://github.com/ethereum-mining/ethminer/issues/2047)
- [Unexpected error CUDA error in func set_constants at line 124 invalid device symbol · Issue #2126 · ethereum-mining/ethminer](https://github.com/ethereum-mining/ethminer/issues/2126)
- [GeForce RTX 50 series (Wikipedia) — arquitectura Blackwell, compute capability 12.0](https://en.wikipedia.org/wiki/GeForce_RTX_50_series)

## Ficheros relevantes

- `bin/kawpowminer.exe` — se puede reproducir el fallo directamente,
  sin pasar por `minar.py`, con `./bin/kawpowminer.exe -U -M 0` (CUDA)
  o `-G -M 0` (OpenCL), ninguno de los dos necesita red ni wallet.
- `src/instalador.py` (`seleccionar_asset`) — hoy elige siempre la
  variante `cuda11` de kawpowminer para GPUs NVIDIA; si se decide el
  camino OpenCL (opción 1), este es el sitio a tocar.

---

# KAS/lolMiner tampoco mina — "--algo option 'KASPA' is not supported"

Siguiendo la recomendación del punto 3 de arriba, Carlos activó su
wallet de Kaspa en `wallets.md` y probó a minar KAS con la GPU. Falla
también, pero por un motivo totalmente distinto y ya con causa 100%
confirmada — no hace falta más investigación, solo decidir qué hacer.

## El error

```
[GPU] ❌ Error: --algo option "KASPA" is not supported, please choose a supported algorithm.
```

## Causa raíz (confirmada, sin ambigüedad)

`src/minar.py` (línea ~92) usa `"algo": "KASPA"` para KAS. Ese era el
nombre correcto del algoritmo en lolMiner — pero **lolMiner quitó el
soporte de Kaspa (kHeavyHash) de sus versiones recientes**, la que se
descarga hoy incluida (`bin/lolminer/1.98a/`, la última release
oficial). Comprobado ejecutando el propio binario, sin red ni wallet:

```
$ ./bin/lolMiner.exe --list-algos
...
Parameter        Algorithm               Fee %   Needs / Supports --pers
ALEPH            Blake3-Alephium         0.75    false
...
KARLSENV2        Karlsenhash V2          1.0     false
...
PYRIN            HeavyHash-Pyrin         1.0     false
PYRINV2          HeavyHash-Pyrin V2      1.0     false
...
```

**"KASPA" ya no aparece en absoluto** en la lista de algoritmos que
sabe minar esta versión de lolMiner. El motivo (confirmado por varios
issues de años seguidos en el repositorio oficial de lolMiner, y por
el propio autor): desde 2023-2024 la red de Kaspa está dominada por
ASICs dedicados (Bitmain Antminer KS, IceRiver...), así que minar
kHeavyHash con GPU ya no es rentable — gastas más luz de la que
ganarías. El propio autor de lolMiner quitó el algoritmo a propósito
en una versión posterior, para no confundir a nadie que lo siga
intentando y para aligerar el programa.

Sí quedan en la lista dos algoritmos "primos" de Kaspa (mismo tipo de
hash, pero son **monedas distintas**, no Kaspa): `KARLSENV2`
(Karlsenhash V2, para la moneda Karlsen/KLS) y `PYRIN`/`PYRINV2`
(HeavyHash-Pyrin, para la moneda Pyrin/PYI). No son Kaspa y no se
puede minar KAS con ellos.

**Conclusión: KAS, tal y como está definido hoy en `minar.py`
(algoritmo "KASPA" vía lolMiner), ya no se puede minar con GPU en
absoluto — con ninguna tarjeta, no es un problema de esta máquina.**
No es un bug de AutoMiner tampoco: cuando se implementó KAS, el
algoritmo sí existía en lolMiner; ha dejado de existir después,
porque dejó de tener sentido económico para cualquiera.

## Caminos posibles (a decidir, no aplicado nada todavía)

1. **Quitar KAS de las monedas de GPU soportadas** (marcar
   `soportado_por_minar_hoy = False` en `monedas.py`, o directamente
   retirar su entrada de `MONEDAS_SOPORTADAS` en `minar.py`) — ya no
   es minable con GPU de forma realista, con ningún hardware.
2. **Sustituir KAS por Karlsen (KLS) o Pyrin (PYI)** como moneda de
   GPU en su lugar, ya que usan un algoritmo hermano y SÍ siguen
   soportadas por lolMiner (`KARLSENV2` / `PYRIN`) — pero son monedas
   distintas, con su propio pool y comunidad; habría que investigarlas
   igual que se investigó cualquier moneda nueva (ver `CLAUDE.md`).

Mi recomendación: opción 1 (quitar KAS) es la más honesta y sencilla
— no tiene sentido mantener una moneda que ya no se puede minar con
GPU pase lo que pase. La opción 2 es válida si en algún momento se
quiere ampliar el catálogo de monedas de GPU, pero es una decisión
aparte, no una urgencia para arreglar esto.

## Fuentes consultadas (KAS/lolMiner)

- [v1.84 (Windows): Kaspa not supported ??? · Issue #2037 · Lolliedieb/lolMiner-releases](https://github.com/Lolliedieb/lolMiner-releases/issues/2037)
- [v1.79 (Windows): Kaspa is broken · Issue #1991 · Lolliedieb/lolMiner-releases](https://github.com/Lolliedieb/lolMiner-releases/issues/1991)
- [v1.78a (Windows): Error mining KASPA · Issue #1972 · Lolliedieb/lolMiner-releases](https://github.com/Lolliedieb/lolMiner-releases/issues/1972)
- [Kaspa ASIC Mining Explained (2026) — MiningReturns](https://miningreturns.com/news/kaspa-asic-mining-era-what-you-need-to-know)

## Ficheros relevantes (KAS/lolMiner)

- `bin/lolMiner.exe` — se puede confirmar la lista de algoritmos que
  soporta esta versión exacta, sin red ni wallet, con
  `./bin/lolMiner.exe --list-algos`.
- `src/minar.py` — entrada `"KAS"` en `MONEDAS_SOPORTADAS` (~línea 90),
  con `"algo": "KASPA"`.
- `src/monedas.py` — catálogo de monedas donde marcar KAS como no
  soportada, si se opta por el camino 1.
