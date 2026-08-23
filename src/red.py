"""
Contexto SSL compartido para las peticiones HTTPS de este proyecto
(descarga de motores de minado, consulta de ingresos y precios).

Por qué existe este fichero: en Windows, Python a veces no puede
verificar NINGÚN certificado HTTPS aunque la conexión sea perfectamente
válida — "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate". La causa es un fallo conocido
de Python (bugs.python.org/issue26313): si el almacén de certificados
de Windows tiene aunque sea UN certificado que Python no sepa leer, la
carga automática de certificados falla entera y se queda sin ninguno —
en un Windows completamente normal y recién instalado, no algo raro.

La solución, sin depender de ningún paquete externo (nada de
"pip install certifi", que además necesitaría la propia red para
instalarse): cargar los certificados del almacén de Windows UNO A UNO,
para que uno dañado no tire abajo a todos los demás.
"""

import platform
import ssl

_contexto_ssl: "ssl.SSLContext | None" = None


def contexto_https() -> ssl.SSLContext:
    """
    Devuelve un ssl.SSLContext listo para pasar como `context=` a
    urllib.request.urlopen(). Se calcula una sola vez (cachea el
    resultado): construirlo recorre el almacén de certificados de
    Windows, que no cambia mientras el programa está en marcha.
    """
    global _contexto_ssl
    if _contexto_ssl is not None:
        return _contexto_ssl

    contexto = ssl.create_default_context()
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
