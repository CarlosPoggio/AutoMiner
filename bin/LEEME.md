# Carpeta para los motores de minado

Normalmente no tienes que tocar esta carpeta: cuando pulsas "Comenzar a
minar" en `python3 src/formulario.py`, si falta el programa de minado
que hace falta para tu moneda, la app lo descarga sola desde la página
oficial del proyecto correspondiente y lo deja aquí (ver
`src/instalador.py`).

Si prefieres instalarlo tú a mano (por ejemplo, sin conexión a internet
en ese momento, o para usar una versión concreta), puedes colocar aquí
el ejecutable descargado y `minar.py` lo encontrará igual, sin
descargar nada:

- **xmrig** (Monero, Wownero, Zephyr, Salvium, Raptoreum): desde
  "xmrig/xmrig" en GitHub, sección Releases.
- **kawpowminer** (Ravencoin): desde
  github.com/RavenCommunity/kawpowminer, sección Releases.
- **lolMiner** (Kaspa, Alephium): desde
  github.com/Lolliedieb/lolMiner-releases, sección Releases.

En Windows el nombre del fichero debe terminar en `.exe` (por ejemplo
`xmrig.exe`); en Linux/Mac, sin extensión.

Esta carpeta no sube nada a git (ni lo que descargues tú, ni lo que
descargue la app sola): son ficheros grandes y distintos para cada
sistema operativo.
