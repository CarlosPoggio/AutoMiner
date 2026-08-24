# Error minando RVN (GPU) — para la siguiente sesión de Claude Code

Carlos intentó minar Ravencoin (RVN) con su GPU desde `formulario.py`
("Comenzar a minar") y le dio un error. Esta sesión lo ha reproducido
**sin conectarse a ningún pool ni minar de verdad** (siguiendo la regla
de CLAUDE.md de no arrancar minado real por cuenta propia) y **sin
modificar nada** del repositorio: este fichero es solo diagnóstico.

## Resumen del error

El motor `kawpowminer.exe` no llega ni a arrancar: falla al cargar una
DLL antes de conectar con ningún pool. Es 100% reproducible en local,
sin red y sin wallet real de por medio.

```
$ ./bin/kawpowminer.exe --help
C:/proyectos/AutoMiner-develop/bin/kawpowminer.exe: error while loading
shared libraries: nvrtc64_112_0.dll: cannot open shared object file:
No such file or directory
$ echo $?
127
```

(Se reproduce igual con `--version` o cualquier otro argumento: el
proceso muere al cargar la DLL, antes de procesar argumentos.)

## Cómo se ha reproducido (pasos, sin minar de verdad)

1. `config.md` ya tenía un bloque `gpu_moneda: RVN` / `gpu_wallet: ...`
   escrito (por el propio intento de Carlos).
2. `bin/kawpowminer.exe` ya estaba descargado en `bin/` (por
   `src/instalador.py`, durante el intento real de Carlos) — la
   descarga en sí funcionó bien.
3. En vez de ejecutar `python src/minar.py` (que conectaría de verdad
   con el pool), se ha ejecutado el binario directamente:
   `./bin/kawpowminer.exe --help`. Falla igual, y sin tocar la red — el
   fallo ocurre al cargar la DLL, antes de cualquier conexión.
4. Si se ejecutara vía `minar.py` (flujo normal), pasaría lo mismo:
   `subprocess.Popen` arrancaría el proceso, pero `kawpowminer.exe`
   moriría al instante escribiendo esa línea a stderr; `minar.py` la
   mostraría como `[GPU] ❌ ...` (la contiene la palabra "error", ver
   `interpretar_linea` en `src/minar.py`).

## Causa raíz (ya localizada)

`src/instalador.py` (`asegurar_motor`, función `seleccionar_asset` en
la misma), para GPUs NVIDIA, descarga la variante **cuda11** de
kawpowminer (ver `src/instalador.py` línea ~108:
`variante = "cuda11" if fabricante_gpu == "NVIDIA" else "opencl"`).
Esa build necesita, junto al `.exe`, dos DLLs de NVRTC (el compilador
JIT de CUDA que usa kawpowminer para compilar el kernel de minado en
tiempo de ejecución):

- `nvrtc64_112_0.dll`
- `nvrtc-builtins64_112.dll`

Esas DLLs **sí vienen dentro del .zip** que se descarga — están en
`bin/kawpowminer/kawpowminer-windows-1.2.4/` junto al propio
`kawpowminer.exe` (comprobado en este repo: la carpeta descomprimida
las tiene las tres cosas: el exe y las dos DLLs). El problema es que
`asegurar_motor` (en `src/instalador.py`, pasos 6-7) solo copia a
`bin/` el **ejecutable** (vía `_buscar_binario_extraido` +
`shutil.copy2`), no las DLLs que lo acompañan. Existe un mecanismo
para ficheros acompañantes (`ficheros_acompanantes` en
`src/motores.py`, usado hoy por xmrig para `WinRing0x64.sys`, y
`_copiar_ficheros_acompanantes_si_faltan` en `instalador.py`), pero la
entrada de `kawpowminer` en `motores.py` (línea ~76) **no tiene
`ficheros_acompanantes`**, así que esa copia nunca se hace para las
DLLs de NVRTC.

Además se ha comprobado que este ordenador **no tiene el CUDA Toolkit
instalado** (no existe `C:\Program Files\NVIDIA GPU Computing
Toolkit`, ni `nvrtc64_112_0.dll` en `C:\Windows\System32`) — solo el
driver normal de NVIDIA (confirmado con `nvidia-smi`, driver 591.74).
Esa DLL de NVRTC no forma parte del driver estándar de NVIDIA, así que
en una máquina "normal" con solo el driver de tarjeta gráfica (como la
de Carlos, o la de cualquier usuario final de esta app) **nunca va a
estar disponible** salvo que la copie la propia app junto al `.exe`.
Es decir: no es un problema puntual de esta máquina, es un bug
reproducible para cualquier usuario NVIDIA con la build cuda11 de
kawpowminer.

## Dato aparte (no bloqueante, pero llamativo)

`nvidia-smi` en esta máquina informa la tarjeta como **"NVIDIA GeForce
RTX 5060"**, no "RTX 4060 Laptop, 8GB" como dice `CLAUDE.md` a día de
hoy. Puede que el hardware de Carlos haya cambiado, o que el dato de
`CLAUDE.md` estuviera desactualizado/equivocado desde el principio. No
afecta a este bug, pero conviene contrastarlo con Carlos y, si
corresponde, actualizar `CLAUDE.md`.

## Posible solución (no aplicada — a valorar por la siguiente sesión)

Añadir a `src/motores.py`, en la entrada `"kawpowminer"` de
`MOTORES`, una lista `ficheros_acompanantes` con las DLLs de NVRTC
(`nvrtc64_112_0.dll`, `nvrtc-builtins64_112.dll`), igual que ya existe
para `WinRing0x64.sys` en xmrig, y comprobar que
`_copiar_ficheros_acompanantes_si_faltan` (en `src/instalador.py`) las
copie tal cual sin más cambios. Puntos a decidir:

- Esas DLLs solo hacen falta en la variante `cuda11` (NVIDIA), no en
  `opencl` (AMD/Intel) — la lista de acompañantes tendría que
  depender del fabricante de GPU, no ser fija por motor como ahora
  (hoy `ficheros_acompanantes` es una lista fija en `MOTORES`, sin
  distinguir variante).
- Arreglo rápido manual, sin tocar código: como la carpeta
  `bin/kawpowminer/kawpowminer-windows-1.2.4/` ya tiene las DLLs
  descargadas en este repo, copiarlas a mano junto a
  `bin/kawpowminer.exe` desbloquearía a Carlos ahora mismo mientras se
  decide el arreglo definitivo en el código.
- Hay que confirmar además que, arreglado esto, kawpowminer realmente
  mina bien en la RTX detectada (siguiente paso tras esto: probar con
  `--dry-run` y luego, si Carlos lo pide explícitamente en ese
  momento, un minado real breve) — este bug es previo a poder validar
  nada de eso.

## Ficheros relevantes

- `src/instalador.py` — `asegurar_motor`, `seleccionar_asset` (~línea
  108 para la variante cuda11/opencl), `_copiar_ficheros_acompanantes_si_faltan`.
- `src/motores.py` — entrada `"kawpowminer"` en `MOTORES` (~línea 76).
- `bin/kawpowminer.exe` y `bin/kawpowminer/kawpowminer-windows-1.2.4/`
  — ya descargados en este repo, se pueden inspeccionar directamente.
