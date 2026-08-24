import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import lista_controladores_vulnerables as lcv  # noqa: E402


def _winreg_falso(valor_leido=1, fallo_lectura=None):
    clave_falsa = MagicMock()
    clave_falsa.__enter__ = MagicMock(return_value=clave_falsa)
    clave_falsa.__exit__ = MagicMock(return_value=False)

    def _query_value_ex(_clave, _nombre):
        if fallo_lectura is not None:
            raise fallo_lectura
        return (valor_leido, 4)

    falso = types.SimpleNamespace(
        HKEY_LOCAL_MACHINE=object(),
        KEY_SET_VALUE=0x0002,
        REG_DWORD=4,
        OpenKey=MagicMock(return_value=clave_falsa),
        QueryValueEx=MagicMock(side_effect=_query_value_ex),
        CreateKeyEx=MagicMock(return_value=clave_falsa),
        SetValueEx=MagicMock(),
    )
    return falso


class TestEstaActivo(unittest.TestCase):
    def test_fuera_de_windows_da_none(self):
        with patch.object(lcv.platform, "system", return_value="Linux"):
            self.assertIsNone(lcv.esta_activo())

    def test_valor_1_da_true(self):
        falso = _winreg_falso(valor_leido=1)
        with patch.object(lcv.platform, "system", return_value="Windows"), \
             patch.dict(sys.modules, {"winreg": falso}):
            self.assertTrue(lcv.esta_activo())

    def test_valor_0_da_false(self):
        falso = _winreg_falso(valor_leido=0)
        with patch.object(lcv.platform, "system", return_value="Windows"), \
             patch.dict(sys.modules, {"winreg": falso}):
            self.assertFalse(lcv.esta_activo())

    def test_valor_ausente_da_none(self):
        falso = _winreg_falso(fallo_lectura=FileNotFoundError())
        with patch.object(lcv.platform, "system", return_value="Windows"), \
             patch.dict(sys.modules, {"winreg": falso}):
            self.assertIsNone(lcv.esta_activo())


class TestFijarActivado(unittest.TestCase):
    def test_fuera_de_windows_no_hace_nada(self):
        with patch.object(lcv.platform, "system", return_value="Linux"):
            ok, mensaje = lcv.desactivar()
        self.assertFalse(ok)
        self.assertIn("Windows", mensaje)

    def test_desactivar_llama_al_registro_con_0(self):
        falso = _winreg_falso()
        with patch.object(lcv.platform, "system", return_value="Windows"), \
             patch.dict(sys.modules, {"winreg": falso}):
            ok, mensaje = lcv.desactivar()
        self.assertTrue(ok)
        self.assertIn("reiniciar", mensaje.lower())
        falso.SetValueEx.assert_called_once()
        self.assertEqual(falso.SetValueEx.call_args[0][-1], 0)

    def test_reactivar_llama_al_registro_con_1(self):
        falso = _winreg_falso()
        with patch.object(lcv.platform, "system", return_value="Windows"), \
             patch.dict(sys.modules, {"winreg": falso}):
            ok, _mensaje = lcv.reactivar()
        self.assertTrue(ok)
        self.assertEqual(falso.SetValueEx.call_args[0][-1], 1)

    def test_fallo_de_permisos_da_mensaje_claro(self):
        falso = _winreg_falso()
        falso.CreateKeyEx.side_effect = OSError("acceso denegado")
        with patch.object(lcv.platform, "system", return_value="Windows"), \
             patch.dict(sys.modules, {"winreg": falso}):
            ok, mensaje = lcv.desactivar()
        self.assertFalse(ok)
        self.assertIn("administrador", mensaje)


if __name__ == "__main__":
    unittest.main()
