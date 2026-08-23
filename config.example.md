# Configuración de minado

Lo más fácil es NO escribir este fichero a mano: ejecuta

    python3 src/formulario.py

y la aplicación detecta tu hardware, te deja elegir moneda(s) y genera
`config.md` por ti (ese nombre está en .gitignore, para que tu wallet
nunca se suba a git). Si prefieres hacerlo a mano, copia este fichero
como `config.md` y rellena tus datos. Luego ejecuta:

    python3 src/minar.py

Formato (dos bloques, CPU y GPU; ambos opcionales pero al menos uno
obligatorio). Puedes usar solo la CPU, solo la GPU, o las dos a la vez:

cpu_moneda: XMR
cpu_wallet: TU_DIRECCION_DE_WALLET_AQUI

gpu_moneda: RVN
gpu_wallet: TU_DIRECCION_DE_WALLET_AQUI

# Monedas soportadas hoy: XMR, WOW, ZEPH, SAL, RTM (CPU) y RVN, KAS, ALPH
# (GPU — implementadas pero sin confirmar todavía en una tarjeta gráfica
# real, ver docs/DECISIONS.md).

# Opcionales del bloque CPU:
# cpu_pool: pool.ejemplo.com:3333
# cpu_hilos: 4
# cpu_donate_level: 1 (comisión de xmrig, 0-100)

# Opcionales del bloque GPU:
# gpu_pool: pool.ejemplo.com:3838
# gpu_worker: mi-pc (por defecto "rig1")
