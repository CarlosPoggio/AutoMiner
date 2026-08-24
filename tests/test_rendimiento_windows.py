import ctypes
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import rendimiento_windows as rw  # noqa: E402


class TestPrepararLsaString(unittest.TestCase):
    def test_longitudes_en_bytes_utf16(self):
        estructura, buffer = rw._preparar_lsa_string("SeLockMemoryPrivilege")
        # UTF-16: 2 bytes por carácter. MaximumLength incluye el nulo final.
        self.assertEqual(estructura.Length, len("SeLockMemoryPrivilege") * 2)
        self.assertEqual(estructura.MaximumLength, estructura.Length + 2)

    def test_buffer_contiene_el_texto_real(self):
        estructura, buffer = rw._preparar_lsa_string("hola")
        # El Buffer de la estructura debe apuntar al mismo texto.
        self.assertEqual(ctypes.wstring_at(estructura.Buffer), "hola")


class TestGuardas(unittest.TestCase):
    def test_no_windows_da_false_con_mensaje_claro(self):
        with patch.object(rw.os, "name", "posix"):
            ok, mensaje = rw.conceder_privilegio_huge_pages()
        self.assertFalse(ok)
        self.assertIn("Windows", mensaje)

    def test_sin_usuario_da_false(self):
        with patch.object(rw.os, "name", "nt"), \
             patch.object(rw.os.environ, "get", return_value=""):
            ok, mensaje = rw.conceder_privilegio_huge_pages(nombre_usuario="")
        self.assertFalse(ok)


class TestFlujoConWinapiSimulada(unittest.TestCase):
    """
    No se puede (ni se debe) llamar a la API real de Windows en cada
    ejecución de los tests: el resultado se verificó a mano una vez, en
    la máquina real, con `secedit /export` (ver docs/DECISIONS.md).
    Aquí se simula advapi32 para comprobar que el código interpreta bien
    los resultados de éxito y de error, sin tocar la política de
    seguridad de verdad.
    """

    def _advapi32_falso(self, estado_open_policy=0, estado_add_rights=0, estado_remove_rights=0):
        falso = MagicMock()

        def lookup_account(*args, **kwargs):
            # args: (system, nombre, sid_buf, cb_sid, dominio_buf, cch_dominio, tipo)
            cb_sid = args[3]
            cch_dominio = args[5]
            if args[2] is None:  # primera llamada: solo pide tamaños
                cb_sid._obj.value = 16
                cch_dominio._obj.value = 8
                ctypes.set_last_error(122)  # ERROR_INSUFFICIENT_BUFFER
                return False
            return True  # segunda llamada: éxito

        falso.LookupAccountNameW.side_effect = lookup_account
        falso.LsaOpenPolicy.return_value = estado_open_policy
        falso.LsaAddAccountRights.return_value = estado_add_rights
        falso.LsaRemoveAccountRights.return_value = estado_remove_rights
        falso.LsaClose.return_value = 0
        falso.LsaNtStatusToWinError.side_effect = lambda estado: 5  # ACCESS_DENIED-like
        return falso

    def test_exito(self):
        falso = self._advapi32_falso(estado_open_policy=0, estado_add_rights=0)
        with patch.object(rw.ctypes, "WinDLL", return_value=falso), \
             patch.object(rw.os, "name", "nt"):
            ok, mensaje = rw.conceder_privilegio_huge_pages(nombre_usuario="prueba")
        self.assertTrue(ok)
        self.assertIn("prueba", mensaje)
        falso.LsaClose.assert_called_once()

    def test_fallo_al_abrir_politica(self):
        falso = self._advapi32_falso(estado_open_policy=-1)
        with patch.object(rw.ctypes, "WinDLL", return_value=falso), \
             patch.object(rw.os, "name", "nt"):
            ok, mensaje = rw.conceder_privilegio_huge_pages(nombre_usuario="prueba")
        self.assertFalse(ok)
        self.assertIn("administrador", mensaje)

    def test_fallo_al_conceder_el_permiso(self):
        falso = self._advapi32_falso(estado_open_policy=0, estado_add_rights=-1)
        with patch.object(rw.ctypes, "WinDLL", return_value=falso), \
             patch.object(rw.os, "name", "nt"):
            ok, mensaje = rw.conceder_privilegio_huge_pages(nombre_usuario="prueba")
        self.assertFalse(ok)
        falso.LsaClose.assert_called_once()  # se cierra el handle aunque falle

    def test_revocar_exito(self):
        falso = self._advapi32_falso(estado_open_policy=0, estado_remove_rights=0)
        with patch.object(rw.ctypes, "WinDLL", return_value=falso), \
             patch.object(rw.os, "name", "nt"):
            ok, mensaje = rw.revocar_privilegio_huge_pages(nombre_usuario="prueba")
        self.assertTrue(ok)
        self.assertIn("prueba", mensaje)
        falso.LsaClose.assert_called_once()

    def test_revocar_fallo_al_abrir_politica(self):
        falso = self._advapi32_falso(estado_open_policy=-1)
        with patch.object(rw.ctypes, "WinDLL", return_value=falso), \
             patch.object(rw.os, "name", "nt"):
            ok, mensaje = rw.revocar_privilegio_huge_pages(nombre_usuario="prueba")
        self.assertFalse(ok)
        self.assertIn("administrador", mensaje)

    def test_revocar_fallo_al_quitar_el_permiso(self):
        falso = self._advapi32_falso(estado_open_policy=0, estado_remove_rights=-1)
        with patch.object(rw.ctypes, "WinDLL", return_value=falso), \
             patch.object(rw.os, "name", "nt"):
            ok, mensaje = rw.revocar_privilegio_huge_pages(nombre_usuario="prueba")
        self.assertFalse(ok)
        falso.LsaClose.assert_called_once()

    def test_revocar_no_windows_da_false(self):
        with patch.object(rw.os, "name", "posix"):
            ok, mensaje = rw.revocar_privilegio_huge_pages()
        self.assertFalse(ok)
        self.assertIn("Windows", mensaje)


if __name__ == "__main__":
    unittest.main()
