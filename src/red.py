"""
Contexto SSL compartido para las peticiones HTTPS de este proyecto
(descarga de motores de minado, consulta de ingresos y precios).

Por qué existe este fichero: en Windows, Python a veces no puede
verificar NINGÚN certificado HTTPS aunque la conexión sea perfectamente
válida — "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate". Hay dos causas distintas que
dan el mismo mensaje (ver docs/DECISIONS.md, entradas 11 y 12):

1. Un fallo conocido de Python (bugs.python.org/issue26313): si el
   almacén de certificados de Windows tiene aunque sea UN certificado
   que Python no sepa leer, la carga automática falla entera y se queda
   sin ninguno. Se arregla cargando el almacén uno a uno en vez de de
   golpe (ver más abajo).
2. En un Windows recién instalado, o en cualquier equipo donde nunca se
   ha usado un navegador, el almacén de certificados raíz de Windows
   puede estar casi vacío: Windows rellena las autoridades (CA)
   públicas BAJO DEMANDA, la primera vez que algo basado en Schannel
   (Edge, PowerShell, el propio `curl.exe` de Windows...) valida una
   web que las necesita. Python, vía OpenSSL, no usa Schannel y nunca
   dispara esa descarga. Por eso `Iniciar minado.bat` descarga con
   `curl` (que sí usa Schannel: eso ya "calienta" el almacén de Windows
   de paso) un paquete de certificados públicos de confianza
   (`bin/cacert.pem`, el mismo que usa Mozilla/`certifi`, publicado por
   el propio proyecto curl) antes de abrir la app. Si ese fichero existe,
   se usa aquí como respaldo, independiente del estado del almacén de
   Windows.

Sin depender de ningún paquete externo de Python (nada de
"pip install certifi", que además necesitaría la propia red para
instalarse, con el mismo problema si la verificación está rota).
"""

import platform
import ssl
from pathlib import Path

_contexto_ssl: "ssl.SSLContext | None" = None

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_CACERT = RAIZ_PROYECTO / "bin" / "cacert.pem"


def contexto_https() -> ssl.SSLContext:
    """
    Devuelve un ssl.SSLContext listo para pasar como `context=` a
    urllib.request.urlopen(). Se calcula una sola vez (cachea el
    resultado): construirlo recorre el almacén de certificados de
    Windows y el fichero cacert.pem, que no cambian mientras el
    programa está en marcha.
    """
    global _contexto_ssl
    if _contexto_ssl is not None:
        return _contexto_ssl

    contexto = ssl.create_default_context()

    if RUTA_CACERT.is_file():
        try:
            contexto.load_verify_locations(cafile=str(RUTA_CACERT))
        except ssl.SSLError:
            pass  # fichero corrupto o incompleto: seguimos con lo demás

    if platform.system() == "Windows":
        for almacen in ("CA", "ROOT"):
            try:
                certificados = ssl.enum_certificates(almacen)
            except OSError:
                continue
            for cert_der, encoding, _confianza in certificados:
                if encoding != "x509_asn":
                    continue
                try:
                    contexto.load_verify_locations(cadata=cert_der)
                except ssl.SSLError:
                    continue  # certificado dañado o duplicado: seguimos con el resto

    _contexto_ssl = contexto
    return _contexto_ssl
