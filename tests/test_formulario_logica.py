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
    from recomendador import OpcionMoneda  # noqa: E402
    TIENE_FORMULARIO = True
except Exception as _e:  # pragma: no cover - depende del entorno
    TIENE_FORMULARIO = False
    RAZON = str(_e)


def _opcion(simbolo, soportada):
    return OpcionMoneda(
        simbolo=simbolo, nombre=simbolo, algoritmo="algo", tipo="cpu",
        soportado_por_minar_hoy=soportada,
    )


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


@unittest.skipUnless(TIENE_FORMULARIO, "tkinter no disponible en este entorno")
class TestFiltrarSoloSoportadas(unittest.TestCase):
    def test_quita_las_no_soportadas_y_conserva_orden(self):
        opciones = [_opcion("ERG", False), _opcion("RVN", True), _opcion("ETC", False), _opcion("KAS", True)]
        filtradas, recomendado = formulario.filtrar_solo_soportadas(opciones)
        self.assertEqual([o.simbolo for o in filtradas], ["RVN", "KAS"])
        self.assertEqual(recomendado, "RVN")

    def test_ninguna_soportada_da_lista_vacia(self):
        filtradas, recomendado = formulario.filtrar_solo_soportadas([_opcion("ERG", False)])
        self.assertEqual(filtradas, [])
        self.assertIsNone(recomendado)

    def test_lista_vacia(self):
        filtradas, recomendado = formulario.filtrar_solo_soportadas([])
        self.assertEqual(filtradas, [])
        self.assertIsNone(recomendado)


@unittest.skipUnless(TIENE_FORMULARIO, "tkinter no disponible en este entorno")
class TestTextoEstimacion(unittest.TestCase):
    def test_none_da_mensaje_neutro(self):
        self.assertEqual(
            formulario.texto_estimacion(None),
            "Estimación no disponible ahora mismo",
        )

    def test_con_estimacion_incluye_moneda_usd_y_referencia(self):
        from estimacion_ingreso import EstimacionReferencia
        est = EstimacionReferencia(
            simbolo="XMR", hashrate_referencia="1 kH/s",
            moneda_por_hora=0.0143, usd_por_hora=1.20, fuente="test",
        )
        texto = formulario.texto_estimacion(est)
        self.assertIn("XMR/hora", texto)
        self.assertIn("$/hora", texto)
        self.assertIn("1 kH/s", texto)
        self.assertIn("no es la velocidad real", texto)

    def test_valores_diminutos_no_se_muestran_como_cero(self):
        from estimacion_ingreso import EstimacionReferencia
        est = EstimacionReferencia(
            simbolo="KAS", hashrate_referencia="1 GH/s",
            moneda_por_hora=0.00026, usd_por_hora=7.5e-06, fuente="test",
        )
        texto = formulario.texto_estimacion(est)
        # No debe quedar como "0.00 $": se usa notación adecuada al tamaño.
        self.assertNotIn("0.00 $", texto)


if __name__ == "__main__":
    unittest.main()
