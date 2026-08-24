import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import hardware  # noqa: E402
import monedas  # noqa: E402
import recomendador  # noqa: E402
import ingresos  # noqa: E402
import config_writer  # noqa: E402


class TestCatalogoMonedas(unittest.TestCase):
    def test_sin_simbolos_duplicados_entre_cpu_y_gpu(self):
        comunes = set(monedas.MONEDAS_CPU) & set(monedas.MONEDAS_GPU)
        self.assertEqual(comunes, set())

    def test_todas_las_monedas_gpu_tienen_vram_minima(self):
        for simbolo, datos in monedas.MONEDAS_GPU.items():
            self.assertIn("vram_min_gb", datos, msg=simbolo)
            self.assertGreater(datos["vram_min_gb"], 0, msg=simbolo)

    def test_todas_las_monedas_tienen_orden_respaldo_unico_por_grupo(self):
        ordenes_cpu = [d["orden_respaldo"] for d in monedas.MONEDAS_CPU.values()]
        self.assertEqual(len(ordenes_cpu), len(set(ordenes_cpu)))
        ordenes_gpu = [d["orden_respaldo"] for d in monedas.MONEDAS_GPU.values()]
        self.assertEqual(len(ordenes_gpu), len(set(ordenes_gpu)))

    def test_monedas_soportadas_hoy_coinciden_con_minar(self):
        # KAS se quitó el 2026-08-24: lolMiner ya no soporta su algoritmo
        # (ver docs/DECISIONS.md).
        soportadas = {s for s, d in monedas.TODAS_LAS_MONEDAS.items() if d["soportado_por_minar_hoy"]}
        self.assertEqual(soportadas, {"XMR", "WOW", "ZEPH", "SAL", "RTM", "RVN", "ALPH"})
        # Todas las soportadas hoy deben estar también en minar.py.
        import minar

        for simbolo in soportadas:
            self.assertIsNotNone(minar.resolver_moneda(simbolo), msg=simbolo)

    def test_monedas_gpu_soportadas_tienen_comision_documentada(self):
        for simbolo in ("RVN", "ALPH"):
            self.assertIn("comision_pct", monedas.MONEDAS_GPU[simbolo], msg=simbolo)


class TestRecomendador(unittest.TestCase):
    def test_monedas_cpu_posibles_con_cpu_detectada(self):
        cpu = hardware.InfoCPU(modelo="CPU de prueba", nucleos_logicos=8)
        posibles = recomendador.monedas_cpu_posibles(cpu)
        self.assertIn("XMR", posibles)
        self.assertEqual(len(posibles), len(monedas.MONEDAS_CPU))

    def test_monedas_cpu_posibles_sin_cpu(self):
        self.assertEqual(recomendador.monedas_cpu_posibles(None), [])

    def test_monedas_gpu_posibles_filtra_por_vram(self):
        gpus = [hardware.InfoGPU(modelo="Tarjeta de 4GB", vram_gb=4.0, fabricante="NVIDIA")]
        posibles = recomendador.monedas_gpu_posibles(gpus)
        self.assertIn("KAS", posibles)  # necesita 2 GB
        self.assertIn("RVN", posibles)  # necesita 4 GB
        self.assertNotIn("ERG", posibles)  # necesita 6 GB

    def test_monedas_gpu_posibles_sin_gpu(self):
        self.assertEqual(recomendador.monedas_gpu_posibles([]), [])

    def test_monedas_gpu_posibles_vram_desconocida_muestra_todas(self):
        gpus = [hardware.InfoGPU(modelo="Tarjeta sin dato", vram_gb=None, fabricante="Desconocido")]
        posibles = recomendador.monedas_gpu_posibles(gpus)
        self.assertEqual(set(posibles), set(monedas.MONEDAS_GPU.keys()))

    @patch("recomendador.clasificar_por_ingreso")
    def test_recomendar_usa_el_primero_del_ranking(self, mock_clasificar):
        mock_clasificar.side_effect = lambda simbolos, catalogo: sorted(simbolos)
        cpu = hardware.InfoCPU(modelo="CPU", nucleos_logicos=4)
        opciones, recomendado = recomendador.recomendar(cpu, [])
        self.assertTrue(len(opciones) > 0)
        self.assertEqual(recomendado, sorted(m for m in monedas.MONEDAS_CPU)[0])

    def test_recomendar_sin_hardware_no_da_opciones(self):
        opciones, recomendado = recomendador.recomendar(None, [])
        self.assertEqual(opciones, [])
        self.assertIsNone(recomendado)


class TestIngresos(unittest.TestCase):
    def test_sin_conexion_devuelve_none(self):
        # Simulamos que no hay salida a internet (urlopen falla) y
        # comprobamos que el camino "sin conexión" devuelve None sin reventar.
        # Se mockea para que el test sea determinista y no dependa de si la
        # máquina donde corre tiene o no conexión.
        with patch("ingresos.urllib.request.urlopen", side_effect=urllib.error.URLError("sin red")):
            resultado = ingresos.obtener_ingresos_en_vivo()
        self.assertIsNone(resultado)

    def test_clasificar_por_ingreso_usa_reserva_sin_conexion(self):
        with patch("ingresos.obtener_ingresos_en_vivo", return_value=None):
            orden = ingresos.clasificar_por_ingreso(["WOW", "XMR", "RTM"], monedas.MONEDAS_CPU)
        # orden_respaldo: XMR=1, RTM=2, WOW=4 -> de mayor a menor ingreso
        self.assertEqual(orden, ["XMR", "RTM", "WOW"])

    def test_clasificar_por_ingreso_usa_datos_en_vivo_si_hay(self):
        falsos_ingresos = {"WOW": 10.0, "XMR": 5.0, "RTM": 1.0}
        with patch("ingresos.obtener_ingresos_en_vivo", return_value=falsos_ingresos):
            orden = ingresos.clasificar_por_ingreso(["WOW", "XMR", "RTM"], monedas.MONEDAS_CPU)
        self.assertEqual(orden, ["WOW", "XMR", "RTM"])

    def test_clasificar_por_ingreso_cobertura_parcial_usa_reserva(self):
        # whattomine.com no incluye todas las monedas de este proyecto (por
        # ejemplo, hoy no trae ninguna de CPU). Si los datos en vivo no
        # cubren TODAS las monedas comparadas, no hay que mezclar: se cae
        # entera a la reserva, para no hundir con un valor inventado a la
        # que falta (antes de arreglar esto, RTM se iba siempre al fondo
        # aunque en la reserva vaya la primera).
        falsos_ingresos = {"WOW": 10.0}  # falta XMR y RTM
        with patch("ingresos.obtener_ingresos_en_vivo", return_value=falsos_ingresos):
            orden = ingresos.clasificar_por_ingreso(["WOW", "XMR", "RTM"], monedas.MONEDAS_CPU)
        # orden_respaldo: XMR=1, RTM=2, WOW=4
        self.assertEqual(orden, ["XMR", "RTM", "WOW"])

    def test_parseo_de_json_de_ejemplo(self):
        json_de_ejemplo = {
            "coins": {
                "Monero": {"tag": "XMR", "estimated_rewards": "0.01", "exchange_rate": "0.005"},
                "SinDatos": {"tag": "ZZZ"},
            }
        }
        with patch("ingresos.urllib.request.urlopen") as mock_urlopen:
            import io
            import json as json_mod

            class FalsaRespuesta(io.BytesIO):
                def __enter__(self_):
                    return self_

                def __exit__(self_, *a):
                    return False

            mock_urlopen.return_value = FalsaRespuesta(json_mod.dumps(json_de_ejemplo).encode())
            resultado = ingresos.obtener_ingresos_en_vivo()
        self.assertIsNotNone(resultado)
        self.assertAlmostEqual(resultado["XMR"], 0.01 * 0.005)
        self.assertNotIn("ZZZ", resultado)  # sin datos suficientes, se descarta


class TestRecomendarPorComponente(unittest.TestCase):
    def test_recomendar_cpu_da_opciones_cpu(self):
        cpu = hardware.InfoCPU(modelo="CPU", nucleos_logicos=8)
        with patch("recomendador.clasificar_por_ingreso", side_effect=lambda s, c: sorted(s)):
            opciones, recomendado = recomendador.recomendar_cpu(cpu)
        self.assertTrue(all(o.tipo == "cpu" for o in opciones))
        self.assertIsNotNone(recomendado)

    def test_recomendar_cpu_sin_cpu(self):
        self.assertEqual(recomendador.recomendar_cpu(None), ([], None))

    def test_recomendar_gpu_filtra_y_recomienda(self):
        gpus = [hardware.InfoGPU(modelo="4GB", vram_gb=4.0, fabricante="NVIDIA")]
        with patch("recomendador.clasificar_por_ingreso", side_effect=lambda s, c: sorted(s)):
            opciones, recomendado = recomendador.recomendar_gpu(gpus)
        simbolos = {o.simbolo for o in opciones}
        self.assertIn("RVN", simbolos)
        self.assertNotIn("ERG", simbolos)  # necesita 6 GB
        self.assertIsNotNone(recomendado)

    def test_recomendar_gpu_sin_gpu(self):
        self.assertEqual(recomendador.recomendar_gpu([]), ([], None))


class TestConfigWriter(unittest.TestCase):
    def test_guardar_config_cpu_soportada(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "config.md"
            config_writer.guardar_config(ruta, "2026-08-20", {"simbolo": "XMR", "wallet": "mi-wallet-123"}, None)
            contenido = ruta.read_text(encoding="utf-8")
        self.assertIn("cpu_wallet: mi-wallet-123", contenido)
        self.assertIn("cpu_moneda: XMR", contenido)
        self.assertNotIn("Aviso", contenido)
        self.assertNotIn("gpu_", contenido)

    def test_guardar_config_moneda_no_soportada_incluye_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "config.md"
            config_writer.guardar_config(ruta, "2026-08-20", None, {"simbolo": "ERG", "wallet": "mi-wallet-123"})
            contenido = ruta.read_text(encoding="utf-8")
        self.assertIn("gpu_moneda: ERG", contenido)
        self.assertIn("Aviso", contenido)

    def test_guardar_config_gpu_soportada_incluye_aviso_sin_confirmar(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "config.md"
            config_writer.guardar_config(ruta, "2026-08-20", None, {"simbolo": "RVN", "wallet": "mi-wallet-123"})
            contenido = ruta.read_text(encoding="utf-8")
        self.assertIn("gpu_moneda: RVN", contenido)
        self.assertIn("nunca contra una tarjeta gráfica real", contenido)

    def test_guardar_config_ambos_bloques(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "config.md"
            config_writer.guardar_config(
                ruta, "2026-08-20",
                {"simbolo": "XMR", "wallet": "wallet-cpu"},
                {"simbolo": "RVN", "wallet": "wallet-gpu"},
            )
            contenido = ruta.read_text(encoding="utf-8")
        self.assertIn("cpu_moneda: XMR", contenido)
        self.assertIn("cpu_wallet: wallet-cpu", contenido)
        self.assertIn("gpu_moneda: RVN", contenido)
        self.assertIn("gpu_wallet: wallet-gpu", contenido)

    def test_guardar_config_ambos_none_lanza_valueerror(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "config.md"
            with self.assertRaises(ValueError):
                config_writer.guardar_config(ruta, "2026-08-20", None, None)

    def test_config_generado_es_compatible_con_minar(self):
        import minar

        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "config.md"
            config_writer.guardar_config(
                ruta, "2026-08-20",
                {"simbolo": "XMR", "wallet": "4walletdeejemplo"},
                {"simbolo": "RVN", "wallet": "RwalletdeejemploGPU"},
            )
            datos = minar.parsear_config(ruta)
            bloques = minar.validar(datos)
        self.assertIn("cpu", bloques)
        self.assertIn("gpu", bloques)
        self.assertEqual(bloques["cpu"][0], "4walletdeejemplo")
        self.assertEqual(bloques["cpu"][1], "XMR")


if __name__ == "__main__":
    unittest.main()
