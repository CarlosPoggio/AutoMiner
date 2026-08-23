import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import estimacion_ingreso as est  # noqa: E402


# --------------------------------------------------------------------------
# Respuestas de ejemplo (recortadas) tal cual devuelven las APIs reales.
# --------------------------------------------------------------------------

PRECIOS_COINGECKO = {
    "monero": {"usd": 430.0},
    "salvium": {"usd": 0.0047},
    "zephyr-protocol": {"usd": 0.40},
    "ravencoin": {"usd": 0.0033},
    "kaspa": {"usd": 0.029},
}

XMR_NETWORK = {"difficulty": 724364281448, "value": 625456300000, "height": 3746443}

# Bloque HeroMiners: campos ':' — la recompensa es el número justo antes de
# la dirección larga del minero.
SAL_STATS = {
    "config": {"coinUnits": 100000000, "symbol": "SAL"},
    "network": {"difficulty": 1228279404, "difficultyTarget": 137.63},
    "pool": {"blocks": [
        "f697c9:1787479039:1491814665:111678638:111678638:f31b0cfc:pending:5447639088:"
        "SC11bHvwab2TXSMzwfgnk1g1vpyiSwCVidbDV87NbgmRdBEzB6E95NmFi7sawFeiUEHstHVWMHTvFJme3yEBSecX1forprynpv:na-us2:prop"
    ]},
}

ZEPH_STATS = {
    "config": {"coinUnits": 1000000000000, "symbol": "ZEPH"},
    "network": {"difficulty": 5080578716, "difficultyTarget": 113.97},
    "pool": {"blocks": [
        "37f12c:1787480992:4311606737:1660658977:1655912389:fb1c1700:pending:4071803271877:"
        "ZEPHs8ZxhXVWTwmXYs3DnviGB3cjSDvKFiJK1gPhsujWj42ZeaJsJhxBa4TdP1xtWid5xf56yVRvBFxyin3rKzHiPrUkYt6dre4:as-kr:prop"
    ]},
}

RVN_STATS = {"nodes": [{"networkhashps": "844045822054.9", "avgBlockTime": "61.05"}]}
RVN_BLOCKS = {"matured": [{"height": 4506402, "reward": 125000000000, "orphan": False}]}

KAS_HASHRATE = {"hashrate": 319022.77}
KAS_REWARD = {"blockreward": 2.31246515}


def _resp(objeto):
    """Un urlopen falso: un context manager que devuelve JSON al leerlo."""
    contenido = json.dumps(objeto).encode("utf-8")

    class _FalsaRespuesta(io.BytesIO):
        def __enter__(self_inner):
            return self_inner

        def __exit__(self_inner, *a):
            return False

    return _FalsaRespuesta(contenido)


def _urlopen_por_url(peticion, timeout=None):
    """Despacha según la URL pedida, como hace el instalador en sus tests."""
    url = peticion.full_url if hasattr(peticion, "full_url") else peticion
    if "api.coingecko.com" in url:
        return _resp(PRECIOS_COINGECKO)
    if "supportxmr.com" in url:
        return _resp(XMR_NETWORK)
    if "salvium.herominers.com" in url:
        return _resp(SAL_STATS)
    if "zephyr.herominers.com" in url:
        return _resp(ZEPH_STATS)
    if "rvn.2miners.com/api/stats" in url:
        return _resp(RVN_STATS)
    if "rvn.2miners.com/api/blocks" in url:
        return _resp(RVN_BLOCKS)
    if "api.kaspa.org/info/hashrate" in url:
        return _resp(KAS_HASHRATE)
    if "api.kaspa.org/info/blockreward" in url:
        return _resp(KAS_REWARD)
    raise AssertionError(f"URL no esperada en el test: {url}")


class BaseEstimacion(unittest.TestCase):
    def setUp(self):
        # Vaciar la caché de precios entre tests para que cada uno controle
        # su propio escenario de red.
        est._cache_precios["ts"] = 0.0
        est._cache_precios["datos"] = {}


class TestEstimacionesConDatos(BaseEstimacion):
    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_xmr(self, _mock):
        r = est.estimar_referencia("XMR")
        self.assertIsNotNone(r)
        self.assertEqual(r.simbolo, "XMR")
        self.assertEqual(r.hashrate_referencia, "1 kH/s")
        # ref(1000) * recompensa(0.6254563) * 3600 / dificultad
        esperado = 1000 * (625456300000 / 1e12) * 3600 / 724364281448
        self.assertAlmostEqual(r.moneda_por_hora, esperado, places=12)
        self.assertAlmostEqual(r.usd_por_hora, esperado * 430.0, places=10)
        self.assertIn("supportxmr", r.fuente)

    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_sal_recompensa_desde_bloque(self, _mock):
        r = est.estimar_referencia("SAL")
        self.assertIsNotNone(r)
        recompensa = 5447639088 / 1e8
        esperado = 1000 * recompensa * 3600 / 1228279404
        self.assertAlmostEqual(r.moneda_por_hora, esperado, places=10)

    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_zeph(self, _mock):
        r = est.estimar_referencia("ZEPH")
        self.assertIsNotNone(r)
        recompensa = 4071803271877 / 1e12
        esperado = 1000 * recompensa * 3600 / 5080578716
        self.assertAlmostEqual(r.moneda_por_hora, esperado, places=12)

    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_rvn_usa_hashrate_directo(self, _mock):
        r = est.estimar_referencia("RVN")
        self.assertIsNotNone(r)
        self.assertEqual(r.hashrate_referencia, "10 MH/s")
        recompensa = 125000000000 / 1e8  # 1250 RVN
        esperado = (1e7 / 844045822054.9) * recompensa * (3600 / 61.05)
        self.assertAlmostEqual(r.moneda_por_hora, esperado, places=8)

    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_kas_usa_hashrate_directo(self, _mock):
        r = est.estimar_referencia("KAS")
        self.assertIsNotNone(r)
        self.assertEqual(r.hashrate_referencia, "1 GH/s")
        net_hr = 319022.77 * 1e12
        esperado = (1e9 / net_hr) * 2.31246515 * (10 * 3600)
        self.assertAlmostEqual(r.moneda_por_hora, esperado, places=12)

    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_simbolo_en_minusculas_y_espacios(self, _mock):
        r = est.estimar_referencia("  xmr ")
        self.assertIsNotNone(r)
        self.assertEqual(r.simbolo, "XMR")


class TestMonedasSinFuente(BaseEstimacion):
    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_wow_sin_fuente_da_none(self, _mock):
        # Wownero no cotiza en CoinGecko: nunca debe inventar un número.
        self.assertIsNone(est.estimar_referencia("WOW"))

    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_rtm_sin_fuente_da_none(self, _mock):
        self.assertIsNone(est.estimar_referencia("RTM"))

    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_alph_sin_fuente_da_none(self, _mock):
        self.assertIsNone(est.estimar_referencia("ALPH"))

    def test_none_da_none(self):
        self.assertIsNone(est.estimar_referencia(None))

    def test_desconocida_da_none(self):
        self.assertIsNone(est.estimar_referencia("NOEXISTE"))


class TestFuenteCaida(BaseEstimacion):
    @patch("urllib.request.urlopen", side_effect=urllib.error.URLError("sin red"))
    def test_sin_conexion_da_none_sin_reventar(self, _mock):
        self.assertIsNone(est.estimar_referencia("XMR"))
        self.assertIsNone(est.estimar_referencia("KAS"))

    def test_dato_de_dificultad_da_none(self):
        # La fuente responde, pero sin recompensa parseable en los bloques.
        stats_sin_reward = {
            "config": {"coinUnits": 100000000},
            "network": {"difficulty": 1228279404},
            "pool": {"blocks": []},
        }

        def urlopen(peticion, timeout=None):
            url = peticion.full_url if hasattr(peticion, "full_url") else peticion
            if "coingecko" in url:
                return _resp(PRECIOS_COINGECKO)
            return _resp(stats_sin_reward)

        with patch("urllib.request.urlopen", side_effect=urlopen):
            self.assertIsNone(est.estimar_referencia("SAL"))

    def test_sin_precio_da_none(self):
        # Las fuentes de dificultad responden, pero CoinGecko no trae el precio.
        def urlopen(peticion, timeout=None):
            url = peticion.full_url if hasattr(peticion, "full_url") else peticion
            if "coingecko" in url:
                return _resp({})  # sin precios
            return _urlopen_por_url(peticion, timeout)

        with patch("urllib.request.urlopen", side_effect=urlopen):
            self.assertIsNone(est.estimar_referencia("XMR"))


class TestCachePrecios(BaseEstimacion):
    def test_precio_se_cachea_una_sola_peticion(self):
        llamadas = {"coingecko": 0}

        def urlopen(peticion, timeout=None):
            url = peticion.full_url if hasattr(peticion, "full_url") else peticion
            if "coingecko" in url:
                llamadas["coingecko"] += 1
            return _urlopen_por_url(peticion, timeout)

        with patch("urllib.request.urlopen", side_effect=urlopen):
            est.estimar_referencia("XMR")
            est.estimar_referencia("SAL")
            est.estimar_referencia("ZEPH")
        # Tres monedas, pero CoinGecko se consulta una sola vez (caché).
        self.assertEqual(llamadas["coingecko"], 1)


if __name__ == "__main__":
    unittest.main()
