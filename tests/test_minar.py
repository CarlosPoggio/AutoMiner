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

    def test_rvn_alph_estan_soportadas(self):
        # KAS se quitó el 2026-08-24: lolMiner ya no soporta su algoritmo
        # (ver docs/DECISIONS.md).
        for simbolo in ("RVN", "ALPH"):
            self.assertIn(simbolo, minar.MONEDAS_SOPORTADAS, msg=simbolo)
        self.assertNotIn("KAS", minar.MONEDAS_SOPORTADAS)

    def test_construir_comando_ravencoin_usa_kawpowminer(self):
        datos = {"wallet": "Rwallet", "moneda": "RVN"}
        cmd = minar.construir_comando("kawpowminer", "Rwallet", "RVN", datos)
        self.assertEqual(cmd, ["kawpowminer", "-P", "stratum+tcp://Rwallet.rig1@stratum.ravenminer.com:3838"])

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

    def test_velocidad_kawpowminer_se_reconoce(self):
        # Formato real de kawpowminer, capturado minando de verdad con una
        # GPU real (RTX 4060 Laptop) — no contiene la palabra "speed", así
        # que antes de este arreglo se perdía como "ruido" y el registro se
        # quedaba en silencio durante todo el minado por GPU.
        salida = minar.interpretar_linea(" m 15:39:19 <unknown> 0:00 A0 12.34 Mh - cu0 12.34")
        self.assertIn("Velocidad", salida)
        self.assertIn("12.34", salida)

    def test_generando_dag_da_aviso_de_progreso(self):
        salida = minar.interpretar_linea("cu 15:39:16 cuda-0    Generating DAG + Light : 5.78 GB")
        self.assertIn("Preparando", salida)

    def test_generado_dag_da_aviso_de_progreso(self):
        salida = minar.interpretar_linea("cu 15:39:32 cuda-0    Generated DAG + Light in 15.5 ms. 2.21 GB left.")
        self.assertIn("GPU lista", salida)

    def test_gpu_demasiado_nueva_da_explicacion_clara(self):
        # Caso real reportado en GPU_ERROR.md: kawpowminer contra una GPU
        # Blackwell (RTX 50). Debe explicarse en español simple, no dejar
        # pasar el mensaje críptico de CUDA sin más.
        linea = (
            "cu 13:53:34 cuda-0 Unexpected error CUDA error in func "
            "set_constants at line 180 calling cudaMemcpyToSymbol(d_dag, "
            "&_dag, sizeof(hash64_t*)) failed with error invalid device "
            "symbol on CUDA device 01:00.0"
        )
        salida = minar.interpretar_linea(linea)
        self.assertTrue(salida.startswith("❌"))
        self.assertIn("demasiado nueva", salida)
        self.assertNotIn("cudaMemcpyToSymbol", salida)

    def test_ruido_devuelve_none(self):
        self.assertIsNone(minar.interpretar_linea("* THREADS       8"))


class TestExtraerHashrateReal(unittest.TestCase):
    def test_xmrig_linea_real(self):
        # Formato real de xmrig (ver github.com/xmrig/xmrig, issues #872/#2624).
        linea = "[2019-12-07 03:46:07.280] speed 10s/60s/15m 7235.8 7465.3 7609.8 H/s max 9244.0 H/s"
        resultado = minar.extraer_hashrate_real(linea, "xmrig")
        self.assertIsNotNone(resultado)
        hz, texto = resultado
        self.assertAlmostEqual(hz, 7235.8)
        self.assertIn("H/s", texto)

    def test_xmrig_sin_datos_aun_da_none(self):
        linea = "speed 10s/60s/15m n/a n/a n/a H/s max n/a H/s"
        self.assertIsNone(minar.extraer_hashrate_real(linea, "xmrig"))

    def test_kawpowminer_linea_real(self):
        # Formato real: TelemetryType::str() en libethcore/Miner.h del repo
        # oficial RavenCommunity/kawpowminer (verificado en el código fuente).
        linea = "0:02 A3 12.34 Mh - cu0 12.34"
        resultado = minar.extraer_hashrate_real(linea, "kawpowminer")
        self.assertIsNotNone(resultado)
        hz, texto = resultado
        self.assertAlmostEqual(hz, 12.34 * 1e6)
        self.assertIn("Mh/s", texto)

    def test_kawpowminer_unidad_gh(self):
        linea = "1:15 A100 1.50 Gh - cu0 1.50"
        hz, _ = minar.extraer_hashrate_real(linea, "kawpowminer")
        self.assertAlmostEqual(hz, 1.50 * 1e9)

    def test_lolminer_linea_real(self):
        linea = "Average speed (30s): 34.27mh/s | 9.10mh/s Total: 43.37 mh/s"
        resultado = minar.extraer_hashrate_real(linea, "lolminer")
        self.assertIsNotNone(resultado)
        hz, texto = resultado
        self.assertAlmostEqual(hz, 43.37 * 1e6)

    def test_linea_sin_hashrate_da_none(self):
        self.assertIsNone(minar.extraer_hashrate_real("net accepted (1/0)", "xmrig"))

    def test_motor_desconocido_da_none(self):
        self.assertIsNone(minar.extraer_hashrate_real("Total: 10.0 mh/s", "motor-raro"))


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

    def test_proceso_que_muere_solo_avisa_con_un_error(self):
        # Caso real reproducido con una GPU real (RTX 4060 Laptop): kawpowminer
        # se cierra solo justo después de generar el DAG, sin decir nada más
        # por su cuenta. Antes, esto dejaba el registro en silencio total sin
        # ningún aviso — ver docs/DECISIONS.md.
        info = minar.MONEDAS_SOPORTADAS["RVN"]
        proceso_falso = MagicMock()
        proceso_falso.stdout.__iter__.return_value = iter(["Generated DAG + Light\n"])
        proceso_falso.wait.return_value = 3221226505  # 0xC0000409, visto de verdad
        lineas = []
        with patch("minar.subprocess.Popen", return_value=proceso_falso):
            sesion = minar.iniciar_minado(
                "gpu", info, "Rwallet", {}, Path("."), "kawpowminer", dry_run=False,
                on_linea=lambda b, l: lineas.append((b, l)),
            )
        sesion.hilo_lector.join(timeout=2)
        avisos = [l for _b, l in lineas if "3221226505" in l]
        self.assertEqual(len(avisos), 1)
        self.assertIn("error", avisos[0].lower())

    def test_proceso_que_termina_bien_no_avisa_de_nada(self):
        info = minar.MONEDAS_SOPORTADAS["XMR"]
        proceso_falso = MagicMock()
        proceso_falso.stdout.__iter__.return_value = iter([])
        proceso_falso.wait.return_value = 0
        lineas = []
        with patch("minar.subprocess.Popen", return_value=proceso_falso):
            sesion = minar.iniciar_minado(
                "cpu", info, "4wallet", {}, Path("."), "xmrig", dry_run=False,
                on_linea=lambda b, l: lineas.append((b, l)),
            )
        sesion.hilo_lector.join(timeout=2)
        self.assertEqual(lineas, [])


if __name__ == "__main__":
    unittest.main()
