import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import minar  # noqa: E402


class TestParseoYValidacion(unittest.TestCase):
    def test_parsear_config(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "config.md"
            f.write_text("cpu_wallet: 4Abc123\ncpu_moneda: XMR\n# comentario\n")
            datos = minar.parsear_config(f)
            self.assertEqual(datos["cpu_wallet"], "4Abc123")
            self.assertEqual(datos["cpu_moneda"], "XMR")

    def test_resolver_moneda_alias(self):
        self.assertEqual(minar.resolver_moneda("monero"), "XMR")
        self.assertEqual(minar.resolver_moneda("xmr"), "XMR")
        self.assertIsNone(minar.resolver_moneda("BTC"))

    def test_validar_solo_cpu(self):
        bloques = minar.validar({"cpu_wallet": "4wallet", "cpu_moneda": "XMR"})
        self.assertIn("cpu", bloques)
        self.assertNotIn("gpu", bloques)
        wallet, moneda, sub = bloques["cpu"]
        self.assertEqual(wallet, "4wallet")
        self.assertEqual(moneda, "XMR")

    def test_validar_ambos_bloques(self):
        bloques = minar.validar({
            "cpu_wallet": "4wallet", "cpu_moneda": "XMR",
            "gpu_wallet": "Rwallet", "gpu_moneda": "RVN",
        })
        self.assertEqual(set(bloques), {"cpu", "gpu"})

    def test_validar_bloque_a_medias_falta_wallet(self):
        with self.assertRaises(ValueError) as ctx:
            minar.validar({"cpu_moneda": "XMR"})
        self.assertIn("cpu_wallet", str(ctx.exception))

    def test_validar_sin_ningun_bloque(self):
        with self.assertRaises(ValueError) as ctx:
            minar.validar({"algo": "otra"})
        self.assertIn("ningún bloque", str(ctx.exception))

    def test_validar_moneda_no_soportada(self):
        with self.assertRaises(ValueError) as ctx:
            minar.validar({"cpu_wallet": "algo", "cpu_moneda": "BTC"})
        self.assertIn("no está soportada", str(ctx.exception))

    def test_validar_moneda_gpu_en_bloque_cpu_falla(self):
        with self.assertRaises(ValueError) as ctx:
            minar.validar({"cpu_wallet": "Rwallet", "cpu_moneda": "RVN"})
        self.assertIn("GPU", str(ctx.exception))

    def test_validar_moneda_cpu_en_bloque_gpu_falla(self):
        with self.assertRaises(ValueError) as ctx:
            minar.validar({"gpu_wallet": "4wallet", "gpu_moneda": "XMR"})
        self.assertIn("CPU", str(ctx.exception))

    def test_subdatos_bloque_quita_prefijo(self):
        bloques = minar.validar({
            "cpu_wallet": "4wallet", "cpu_moneda": "XMR",
            "cpu_pool": "mi-pool.com:1234", "cpu_hilos": "3",
        })
        _, _, sub = bloques["cpu"]
        self.assertEqual(sub.get("pool"), "mi-pool.com:1234")
        self.assertEqual(sub.get("hilos"), "3")


class TestConstruirComando(unittest.TestCase):
    def test_construir_comando_incluye_wallet_y_pool(self):
        datos = {"wallet": "4wallet", "moneda": "XMR"}
        cmd = minar.construir_comando("xmrig", "4wallet", "XMR", datos)
        self.assertIn("xmrig", cmd[0])
        self.assertIn("4wallet", cmd)
        self.assertIn("pool.supportxmr.com:3333", cmd)

    def test_construir_comando_pool_personalizado(self):
        datos = {"wallet": "4wallet", "moneda": "XMR", "pool": "mi-pool.com:1234", "hilos": "2"}
        cmd = minar.construir_comando("xmrig", "4wallet", "XMR", datos)
        self.assertIn("mi-pool.com:1234", cmd)
        self.assertIn("2", cmd)

    def test_wow_zeph_sal_rtm_estan_soportadas(self):
        for simbolo in ("WOW", "ZEPH", "SAL", "RTM"):
            self.assertIn(simbolo, minar.MONEDAS_SOPORTADAS, msg=simbolo)

    def test_construir_comando_wownero_usa_rx_wow(self):
        datos = {"wallet": "Wo3wallet", "moneda": "WOW"}
        cmd = minar.construir_comando("xmrig", "Wo3wallet", "WOW", datos)
        self.assertIn("rx/wow", cmd)
        self.assertIn("wownero.ingest.cryptoknight.cc:50901", cmd)

    def test_construir_comando_raptoreum_incluye_tls(self):
        datos = {"wallet": "Rwallet", "moneda": "RTM"}
        cmd = minar.construir_comando("xmrig", "Rwallet", "RTM", datos)
        self.assertIn("gr", cmd)
        self.assertIn("--tls", cmd)
        self.assertIn("rtm.suprnova.cc:4273", cmd)

    def test_validar_wallet_raptoreum_formato_correcto(self):
        bloques = minar.validar({"cpu_wallet": "RUZb2pp45x5qAjbS3usXAGW8BzK1fvKJBo", "cpu_moneda": "RTM"})
        self.assertEqual(bloques["cpu"][1], "RTM")

    def test_rvn_kas_alph_estan_soportadas(self):
        for simbolo in ("RVN", "KAS", "ALPH"):
            self.assertIn(simbolo, minar.MONEDAS_SOPORTADAS, msg=simbolo)

    def test_construir_comando_ravencoin_usa_kawpowminer(self):
        datos = {"wallet": "Rwallet", "moneda": "RVN"}
        cmd = minar.construir_comando("kawpowminer", "Rwallet", "RVN", datos)
        self.assertEqual(cmd, ["kawpowminer", "-P", "stratum+tcp://Rwallet.rig1@stratum.ravenminer.com:3838"])

    def test_construir_comando_kaspa_usa_lolminer_algo_kaspa(self):
        datos = {"wallet": "kaspa:qwallet", "moneda": "KAS"}
        cmd = minar.construir_comando("lolMiner", "kaspa:qwallet", "KAS", datos)
        self.assertIn("--algo", cmd)
        self.assertIn("KASPA", cmd)
        self.assertIn("de.kaspa.herominers.com:1206", cmd)

    def test_construir_comando_alephium_usa_lolminer_algo_aleph(self):
        datos = {"wallet": "alphwallet", "moneda": "ALPH"}
        cmd = minar.construir_comando("lolMiner", "alphwallet", "ALPH", datos)
        self.assertIn("ALEPH", cmd)
        self.assertIn("de.alephium.herominers.com:1199", cmd)

    def test_construir_comando_xmrig_respeta_donate_level(self):
        datos = {"wallet": "4wallet", "moneda": "XMR", "donate_level": "0"}
        cmd = minar.construir_comando("xmrig", "4wallet", "XMR", datos)
        self.assertIn("--donate-level", cmd)
        self.assertIn("0", cmd)

    def test_motor_de_moneda_no_soportada_da_error_util(self):
        with self.assertRaises(KeyError):
            minar.MONEDAS_SOPORTADAS["ERG"]


class TestInterpretarLinea(unittest.TestCase):
    def test_accepted(self):
        self.assertIn("aceptado", minar.interpretar_linea("net accepted (1/0)"))

    def test_rejected(self):
        self.assertIn("rechazado", minar.interpretar_linea("net REJECTED share"))

    def test_new_job(self):
        self.assertIn("Nuevo trabajo", minar.interpretar_linea("net new job from pool"))

    def test_speed_incluye_info(self):
        salida = minar.interpretar_linea("miner speed 10s/60s 1234.5 H/s")
        self.assertIn("Velocidad", salida)
        self.assertIn("1234.5", salida)

    def test_connect(self):
        self.assertIn("Conectado", minar.interpretar_linea("net use pool connect ok"))

    def test_error_mantiene_texto_original(self):
        salida = minar.interpretar_linea("connection ERROR: timeout on host")
        self.assertTrue(salida.startswith("❌"))
        self.assertIn("timeout on host", salida)

    def test_fail(self):
        self.assertTrue(minar.interpretar_linea("login failed").startswith("❌"))

    def test_ruido_devuelve_none(self):
        self.assertIsNone(minar.interpretar_linea("* THREADS       8"))


class TestIniciarMinado(unittest.TestCase):
    def test_dry_run_no_arranca_proceso(self):
        info = minar.MONEDAS_SOPORTADAS["XMR"]
        lineas = []
        with patch("minar.subprocess.Popen") as mock_popen:
            sesion = minar.iniciar_minado(
                "cpu", info, "4wallet", {}, Path("."), "xmrig", dry_run=True,
                on_linea=lambda b, l: lineas.append((b, l)),
            )
        self.assertIsNone(sesion)
        mock_popen.assert_not_called()
        self.assertEqual(len(lineas), 1)
        self.assertEqual(lineas[0][0], "cpu")
        self.assertIn("dry-run", lineas[0][1])

    def test_modo_real_usa_popen_y_devuelve_sesion(self):
        info = minar.MONEDAS_SOPORTADAS["XMR"]
        proceso_falso = MagicMock()
        proceso_falso.stdout.__iter__.return_value = iter([])  # sin salida
        with patch("minar.subprocess.Popen", return_value=proceso_falso) as mock_popen:
            sesion = minar.iniciar_minado(
                "cpu", info, "4wallet", {}, Path("."), "xmrig", dry_run=False,
                on_linea=lambda b, l: None,
            )
        mock_popen.assert_called_once()
        self.assertIsInstance(sesion, minar.SesionMinado)
        sesion.hilo_lector.join(timeout=2)

    def test_detener_termina_proceso_en_marcha(self):
        proceso_falso = MagicMock()
        proceso_falso.poll.return_value = None  # sigue vivo
        sesion = minar.SesionMinado(proceso_falso, None, "cpu")
        sesion.detener()
        proceso_falso.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
