# Tus wallets por defecto

Una línea por moneda, formato `SIMBOLO: direccion`. Cuando abras
`python3 src/formulario.py` y elijas una moneda en el desplegable de CPU
o de GPU, si aparece aquí, el campo de wallet se rellena solo con la
dirección de abajo (puedes cambiarla a mano si quieres usar otra). Si
una moneda no está en esta lista, el campo se queda vacío y tienes que
escribirla tú.

Este fichero SÍ se sube a git y se comparte sin problema en GitHub: una
dirección de wallet es la que RECIBE el dinero minado, así que es
pública por diseño (en cuanto te llega un pago, cualquiera puede verlo
en la cadena de bloques). **Nunca pongas aquí una clave privada ni una
frase semilla** — eso sí debe permanecer secreto, y no tiene nada que
ver con la dirección de recibir.

Monedas soportadas hoy (ver README.md para la lista completa):
XMR, WOW, ZEPH, SAL, RTM (CPU) y RVN, ALPH, IRON, ERG, BEAM (GPU). KAS
ya no se puede minar con GPU (lolMiner retiró su algoritmo, ver
docs/DECISIONS.md), así que aunque dejes una wallet suya abajo, no
aparecerá en el formulario.

Ejemplo (borra el # para activar la línea y pon tu dirección real):

XMR: 49d9CfsFivt9pGRV1T6XZzMtKHLnZknpZHHTwZSUK5ZRUdpJZ8xffdkSa6L3KDBVjWMasm5YZeqM7dCYwaf5nNiJQ8Z8GUg
# WOW: tu_direccion_de_wownero_aqui
# ZEPH: tu_direccion_de_zephyr_aqui
# SAL: tu_direccion_de_salvium_aqui
# RTM: tu_direccion_de_raptoreum_aqui
RVN: RUryKpxJLtbMj9AYfZMBv4QMS1cFK3kNtz
KAS: kaspa:qpdrsp4mkxvn2v3kse27d6jv7e7syghhmyrl58dp3mhjga4my0r8yna99st5q
ALPH: 3cUriAoQzZBybHYUNmKGHJroLBYAoJUhMa3QPkXH4M49hMp6NhSEa
# IRON: tu_direccion_de_iron_fish_aqui
# ERG: tu_direccion_de_ergo_aqui
# BEAM: tu_direccion_de_beam_aqui
