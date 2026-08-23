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


@unittest.skipUnless(TIENE_FORMULARIO, "tkinter no disponible en este entorno")
class TestTextoIngresoReal(unittest.TestCase):
    def test_moneda_no_disponible(self):
        texto = formulario.texto_ingreso_real("WOW", disponible=False)
        self.assertIn("WOW", texto)
        self.assertIn("no disponible", texto)

    def test_disponible_pero_sin_lectura_aun(self):
        texto = formulario.texto_ingreso_real("XMR", disponible=True)
        self.assertIn("XMR", texto)
        self.assertIn("calculando", texto.lower())

    def test_con_hashrate_real_incluye_todo(self):
        texto = formulario.texto_ingreso_real(
            "XMR", disponible=True, hashrate_texto="4500.0 H/s",
            moneda_por_hora=0.05, usd_por_hora=21.5,
        )
        self.assertIn("XMR", texto)
        self.assertIn("4500.0 H/s", texto)
        self.assertIn("XMR/hora", texto)
        self.assertIn("$/hora", texto)


@unittest.skipUnless(TIENE_FORMULARIO, "tkinter no disponible en este entorno")
class TestAutorrellenoWalletAlMarcarCasilla(unittest.TestCase):
    """
    Regresión: al abrir la app, el campo de wallet empieza deshabilitado
    (la casilla "Minar con la CPU/GPU" no está marcada todavía). Un
    ttk.Entry deshabilitado ignora insert()/delete() en silencio, así que
    el primer intento de autorrelleno (al construir la ventana) no hacía
    nada — y como ya se había registrado esa moneda como "última
    procesada", marcar la casilla después tampoco volvía a intentarlo.
    Resultado: el usuario tenía que escribir la wallet a mano aunque
    estuviera en wallets.md. Comprueba que, al marcar la casilla, el
    campo (que ya está vacío) se rellena de verdad.
    """

    def setUp(self):
        from unittest.mock import patch
        import ingresos
        # Sin esto, construir la App dispara una consulta real a
        # whattomine.com al calcular la recomendación — la anulamos para
        # que el test sea rápido y determinista.
        self._parche_ingresos = patch.object(ingresos, "obtener_ingresos_en_vivo", return_value=None)
        self._parche_ingresos.start()
        self._parche_wallets = patch(
            "formulario.cargar_wallets_por_defecto",
            return_value={"XMR": "wallet-de-prueba-xmr"},
        )
        self._parche_wallets.start()

    def tearDown(self):
        self._parche_ingresos.stop()
        self._parche_wallets.stop()

    def test_marcar_cpu_rellena_la_wallet_por_defecto(self):
        app = formulario.App()
        try:
            self.assertEqual(app.entry_wallet_cpu.get(), "")  # empieza deshabilitado y vacío
            app.cpu_activa.set(True)
            app._on_toggle()
            self.assertEqual(app.entry_wallet_cpu.get(), "wallet-de-prueba-xmr")
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
