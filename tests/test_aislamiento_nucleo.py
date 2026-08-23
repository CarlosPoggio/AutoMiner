import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import aislamiento_nucleo as an  # noqa: E402


class _ProcesoFalso:
    def __init__(self, returncode=0, stdout=""):
        self.returncode = returncode
        self.stdout = stdout


class TestEstaActivo(unittest.TestCase):
    def test_fuera_de_windows_da_none(self):
        with patch.object(an.platform, "system", return_value="Linux"):
            self.assertIsNone(an.esta_activo())

    def test_memory_integrity_corriendo_da_true(self):
        with patch.object(an.platform, "system", return_value="Windows"), \
             patch.object(an.subprocess, "run", return_value=_ProcesoFalso(0, "[2]")):
            self.assertTrue(an.esta_activo())

    def test_solo_credential_guard_da_false(self):
        # Valor 1 = Credential Guard, no memory integrity (2).
        with patch.object(an.platform, "system", return_value="Windows"), \
             patch.object(an.subprocess, "run", return_value=_ProcesoFalso(0, "[1]")):
            self.assertFalse(an.esta_activo())

    def test_un_solo_valor_sin_lista_tambien_funciona(self):
        # ConvertTo-Json no mete en lista si solo hay un elemento.
        with patch.object(an.platform, "system", return_value="Windows"), \
             patch.object(an.subprocess, "run", return_value=_ProcesoFalso(0, "2")):
            self.assertTrue(an.esta_activo())

    def test_sin_nada_corriendo_da_false(self):
        with patch.object(an.platform, "system", return_value="Windows"), \
             patch.object(an.subprocess, "run", return_value=_ProcesoFalso(0, "")):
            self.assertFalse(an.esta_activo())

    def test_powershell_falla_da_none(self):
        with patch.object(an.platform, "system", return_value="Windows"), \
             patch.object(an.subprocess, "run", side_effect=OSError("no powershell")):
            self.assertIsNone(an.esta_activo())

    def test_json_invalido_da_none(self):
        with patch.object(an.platform, "system", return_value="Windows"), \
             patch.object(an.subprocess, "run", return_value=_ProcesoFalso(0, "esto no es json")):
            self.assertIsNone(an.esta_activo())


def _winreg_falso():
    falso = types.SimpleNamespace(
        HKEY_LOCAL_MACHINE=object(),
        KEY_SET_VALUE=0x0002,
        REG_DWORD=4,
        CreateKeyEx=MagicMock(return_value=MagicMock()),
        SetValueEx=MagicMock(),
    )
    return falso


class TestFijarActivado(unittest.TestCase):
    def test_fuera_de_windows_no_hace_nada(self):
        with patch.object(an.platform, "system", return_value="Linux"):
            ok, mensaje = an.desactivar()
        self.assertFalse(ok)
        self.assertIn("Windows", mensaje)

    def test_desactivar_llama_al_registro_con_0(self):
        falso = _winreg_falso()
        with patch.object(an.platform, "system", return_value="Windows"), \
             patch.dict(sys.modules, {"winreg": falso}):
            ok, mensaje = an.desactivar()
        self.assertTrue(ok)
        self.assertIn("reiniciar", mensaje.lower())
        falso.SetValueEx.assert_called_once()
        # Último argumento posicional: el valor (0 = desactivado).
        self.assertEqual(falso.SetValueEx.call_args[0][-1], 0)

    def test_reactivar_llama_al_registro_con_1(self):
        falso = _winreg_falso()
        with patch.object(an.platform, "system", return_value="Windows"), \
             patch.dict(sys.modules, {"winreg": falso}):
            ok, _mensaje = an.reactivar()
        self.assertTrue(ok)
        self.assertEqual(falso.SetValueEx.call_args[0][-1], 1)

    def test_fallo_de_permisos_da_mensaje_claro(self):
        falso = _winreg_falso()
        falso.CreateKeyEx.side_effect = OSError("acceso denegado")
        with patch.object(an.platform, "system", return_value="Windows"), \
             patch.dict(sys.modules, {"winreg": falso}):
            ok, mensaje = an.desactivar()
        self.assertFalse(ok)
        self.assertIn("administrador", mensaje)


if __name__ == "__main__":
    unittest.main()
