import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# formulario importa tkinter en la cabecera. En un entorno sin tkinter
# (algunos servidores sin interfaz) el import falla; en ese caso saltamos
# estos tests de lógica en vez de romper la suite. En un ordenador normal
# (Windows/Mac/Linux con escritorio) tkinter sí se importa y los tests
# corren de verdad.
try:
    import formulario  # noqa: E402
    TIENE_FORMULARIO = True
except Exception as _e:  # pragma: no cover - depende del entorno
    TIENE_FORMULARIO = False
    RAZON = str(_e)


@unittest.skipUnless(TIENE_FORMULARIO, "tkinter no disponible en este entorno")
class TestBotonHabilitado(unittest.TestCase):
    def test_nada_marcado_deshabilitado(self):
        self.assertFalse(formulario.boton_habilitado(False, "", False, ""))

    def test_cpu_marcada_sin_wallet_deshabilitado(self):
        self.assertFalse(formulario.boton_habilitado(True, "   ", False, ""))

    def test_cpu_marcada_con_wallet_habilitado(self):
        self.assertTrue(formulario.boton_habilitado(True, "4wallet", False, ""))

    def test_gpu_marcada_con_wallet_habilitado(self):
        self.assertTrue(formulario.boton_habilitado(False, "", True, "Rwallet"))

    def test_ambas_con_wallet_habilitado(self):
        self.assertTrue(formulario.boton_habilitado(True, "4wallet", True, "Rwallet"))


@unittest.skipUnless(TIENE_FORMULARIO, "tkinter no disponible en este entorno")
class TestConstruirBloquesConfig(unittest.TestCase):
    def test_solo_cpu(self):
        cpu, gpu = formulario.construir_bloques_config(True, "XMR", "4wallet", False, "RVN", "Rwallet")
        self.assertEqual(cpu, {"simbolo": "XMR", "wallet": "4wallet"})
        self.assertIsNone(gpu)

    def test_solo_gpu(self):
        cpu, gpu = formulario.construir_bloques_config(False, "XMR", "4wallet", True, "RVN", "Rwallet")
        self.assertIsNone(cpu)
        self.assertEqual(gpu, {"simbolo": "RVN", "wallet": "Rwallet"})

    def test_ambos(self):
        cpu, gpu = formulario.construir_bloques_config(True, "XMR", " 4wallet ", True, "RVN", "Rwallet")
        self.assertEqual(cpu, {"simbolo": "XMR", "wallet": "4wallet"})  # se recorta el espacio
        self.assertEqual(gpu, {"simbolo": "RVN", "wallet": "Rwallet"})

    def test_activa_pero_sin_wallet_da_none(self):
        cpu, gpu = formulario.construir_bloques_config(True, "XMR", "  ", False, None, "")
        self.assertIsNone(cpu)
        self.assertIsNone(gpu)

    def test_activa_pero_sin_simbolo_da_none(self):
        cpu, gpu = formulario.construir_bloques_config(True, None, "4wallet", False, None, "")
        self.assertIsNone(cpu)


if __name__ == "__main__":
    unittest.main()
