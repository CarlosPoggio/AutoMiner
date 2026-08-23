import ssl
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import red  # noqa: E402


class TestContextoHttps(unittest.TestCase):
    def setUp(self):
        # El contexto se cachea a nivel de módulo; cada test parte de cero.
        red._contexto_ssl = None

    def test_devuelve_un_sslcontext(self):
        contexto = red.contexto_https()
        self.assertIsInstance(contexto, ssl.SSLContext)

    def test_se_cachea_entre_llamadas(self):
        primero = red.contexto_https()
        segundo = red.contexto_https()
        self.assertIs(primero, segundo)

    def test_en_windows_un_certificado_danado_no_rompe_el_resto(self):
        # Regresión: en Windows, ssl.create_default_context() puede fallar
        # a cargar TODOS los certificados si el almacén tiene uno dañado
        # (bugs.python.org/issue26313) — así se reprodujo el "unable to
        # get local issuer certificate" en un Windows recién instalado.
        # contexto_https() carga uno a uno para no perderlos todos.
        certificados_falsos = [
            (b"esto-no-es-un-certificado-valido", "x509_asn", True),
            (b"tampoco-esto", "x509_asn", True),
        ]
        with patch("red.platform.system", return_value="Windows"), \
             patch("red.ssl.enum_certificates", return_value=certificados_falsos, create=True):
            contexto = red.contexto_https()  # no debe lanzar excepción
        self.assertIsInstance(contexto, ssl.SSLContext)

    def test_en_windows_ignora_encodings_que_no_son_x509(self):
        certificados = [(b"algo", "auth_root", True)]
        with patch("red.platform.system", return_value="Windows"), \
             patch("red.ssl.enum_certificates", return_value=certificados, create=True) as mock_enum:
            red.contexto_https()
        mock_enum.assert_called()  # se intentó, aunque no haya nada que cargar


# No hay test de "en Linux no se enumeran certificados de Windows": en esta
# máquina (Windows real), ssl.create_default_context() ya intenta cargar el
# almacén de Windows por su cuenta, aparte de nuestro bucle explícito — así
# que ese caso no se puede aislar de forma fiable con mocks aquí.


if __name__ == "__main__":
    unittest.main()
