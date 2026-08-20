import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import minar  # noqa: E402


class TestMinar(unittest.TestCase):
    def test_parsear_config(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "config.md"
            f.write_text("wallet: 4Abc123\nmoneda: XMR\n# comentario\n")
            datos = minar.parsear_config(f)
            self.assertEqual(datos["wallet"], "4Abc123")
            self.assertEqual(datos["moneda"], "XMR")

    def test_resolver_moneda_alias(self):
        self.assertEqual(minar.resolver_moneda("monero"), "XMR")
        self.assertEqual(minar.resolver_moneda("xmr"), "XMR")
        self.assertIsNone(minar.resolver_moneda("BTC"))

    def test_validar_falta_wallet(self):
        with self.assertRaises(ValueError) as ctx:
            minar.validar({"moneda": "XMR"})
        self.assertIn("wallet", str(ctx.exception))

    def test_validar_moneda_no_soportada(self):
        with self.assertRaises(ValueError) as ctx:
            minar.validar({"wallet": "algo", "moneda": "BTC"})
        self.assertIn("no está soportada", str(ctx.exception))

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

    def test_validar_wallet_raptoreum_formato_correcto_sin_aviso(self):
        # No debe lanzar excepción; solo comprobamos que no falla.
        wallet, moneda, _ = minar.validar({"wallet": "RUZb2pp45x5qAjbS3usXAGW8BzK1fvKJBo", "moneda": "RTM"})
        self.assertEqual(moneda, "RTM")


if __name__ == "__main__":
    unittest.main()
