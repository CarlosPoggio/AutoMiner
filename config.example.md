# Configuración de minado

Copia este fichero como `config.md` (ese nombre está en .gitignore, para
que tu wallet nunca se suba a git) y rellena tus datos. Guarda el fichero
y luego ejecuta:

    python3 src/minar.py

Líneas admitidas:

wallet: TU_DIRECCION_DE_WALLET_AQUI
moneda: XMR

# Monedas soportadas hoy: XMR, WOW, ZEPH, SAL, RTM (CPU) y RVN, KAS, ALPH
# (GPU — implementadas pero sin confirmar todavía en una tarjeta gráfica
# real, ver docs/DECISIONS.md).

# Opcionales:
# pool: pool.ejemplo.com:3333
# hilos: 4
# worker: mi-pc (usado por RVN/KAS/ALPH; por defecto "rig1")
# donate_level: 1 (solo XMR/WOW/ZEPH/SAL/RTM; comisión de xmrig, 0-100)
