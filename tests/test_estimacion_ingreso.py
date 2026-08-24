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
    "alephium": {"usd": 0.0335},
    "iron-fish": {"usd": 0.076174},
    "ergo": {"usd": 0.261442},
    "beam-2": {"usd": 0.00149559},
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

# Captura real de alephium.herominers.com/api/stats (2026-08-24, recortada).
# El campo antes de la dirección real (la penúltima parte) es la
# recompensa; el campo hexadecimal lleno de ceros justo antes NO debe
# confundirse con la dirección — es el bug real que se reprodujo y arregló.
ALPH_STATS = {
    "config": {"coinUnits": 1000000000000000000},
    "network": {"difficulty": 2877482810317808},
    "pool": {
        "stats": {"averageReward": None},  # visto así de verdad parte del tiempo
        "blocks": [
            "00000000000195b5b250d576ffc7caf655fbc9b8ee6f25f38555736319d2cda4:7342453:"
            "1787580539:2805561783436960:5760286446566350:5760286446566350:"
            "827b000000000000000000000000000000b2df86d31fb621:4:pending:"
            "143317807237549265:1CnmrpKQ9fm6ZEkpguiCUxTajxWastc5439qyRvqgfTkQ:na-us3:prop"
        ],
    },
}

# Capturas reales de HeroMiners para IRON/ERG/BEAM (2026-08-24, recortadas).
# A diferencia de ALPH, estos bloques SÍ funcionan con el parser genérico:
# no traen ningún campo extra que se confunda con la dirección del minero.
IRON_STATS = {
    "config": {"coinUnits": 100000000},
    "network": {"difficulty": 19794429814229},
    "pool": {"blocks": [
        "00000000000792c834bd4a3165ad57f99b1d1f4c0e38432ed945fc6f6fc429b1:1787577591:"
        "19685201431534:18645543414849:18618736654028:00cc317d742e7292:pending:"
        "1725000000:4f332240eb11954a94a57c67ef9e9f9d1a922de0bb82f50986e624b327d60da5:"
        "na-us2:prop"
    ]},
}

ERG_STATS = {
    "config": {"coinUnits": 1000000000},
    "network": {"difficulty": 75748543037440},
    "pool": {"blocks": [
        "4788f5bd18a30289b79ec2f865fdadd0e70a28214c573b326adca6fa107b338a:1787572756:"
        "75748543037439:11078579802013:11072298016748:bd2b67db440ca00a:pending:"
        "3007800000:9huiUrcSSr8N7hwwzD65N5nu13F3BdvZfoEiPKMhHHNCdUG5mL5:na-us2:prop:"
        "02eeec374f4e660e117fccbfec79e6fe5cdf44ac508fa228bfc654d2973f9bdc9a"
    ]},
}

BEAM_STATS = {
    "config": {"coinUnits": 100000000},
    "network": {"difficulty": 3236492.75},
    "pool": {"blocks": [
        "8d8c414c9ba2a569bc0e6ee2949844fb265b4e43c9d1c5a517a0cbb6825e8a81:1787567965:"
        "3202597.25:3137936:3122725:pending:2500000000:"
        "37f3131007a84edbb7fa737881209ee8176b830d238aa2d47954b628e0f9772baeb:eu-de:prop"
    ]},
}


def _resp(objeto):
    """Un urlopen falso: un context manager que devuelve JSON al leerlo."""
    contenido = json.dumps(objeto).encode("utf-8")

    class _FalsaRespuesta(io.BytesIO):
        def __enter__(self_inner):
            return self_inner

        def __exit__(self_inner, *a):
            return False

    return _FalsaRespuesta(contenido)


def _urlopen_por_url(peticion, timeout=None, **_kwargs):
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
    if "ironfish.herominers.com" in url:
        return _resp(IRON_STATS)
    if "ergo.herominers.com" in url:
        return _resp(ERG_STATS)
    if "beam.herominers.com" in url:
        return _resp(BEAM_STATS)
    if "alephium.herominers.com" in url:
        return _resp(ALPH_STATS)
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
    def test_alph_recompensa_desde_bloque_evita_el_campo_hex(self, _mock):
        # Reproduce el bug real: un parser genérico ("el primer token largo
        # alfanumérico es la dirección") se confundiría con el campo
        # hexadecimal y calcularía una recompensa completamente distinta.
        r = est.estimar_referencia("ALPH")
        self.assertIsNotNone(r)
        self.assertEqual(r.hashrate_referencia, "1 GH/s")
        recompensa = 143317807237549265 / 1e18
        esperado = 1e9 * recompensa * 3600 / 2877482810317808
        self.assertAlmostEqual(r.moneda_por_hora, esperado, places=12)
        self.assertIn("herominers", r.fuente)

    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_iron_recompensa_desde_bloque(self, _mock):
        r = est.estimar_referencia("IRON")
        self.assertIsNotNone(r)
        recompensa = 1725000000 / 1e8
        esperado = 1e7 * recompensa * 3600 / 19794429814229
        self.assertAlmostEqual(r.moneda_por_hora, esperado, places=10)
        self.assertIn("herominers", r.fuente)

    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_erg_recompensa_desde_bloque(self, _mock):
        r = est.estimar_referencia("ERG")
        self.assertIsNotNone(r)
        recompensa = 3007800000 / 1e9
        esperado = 1e8 * recompensa * 3600 / 75748543037440
        self.assertAlmostEqual(r.moneda_por_hora, esperado, places=8)

    @patch("urllib.request.urlopen", side_effect=_urlopen_por_url)
    def test_beam_recompensa_desde_bloque(self, _mock):
        r = est.estimar_referencia("BEAM")
        self.assertIsNotNone(r)
        self.assertEqual(r.hashrate_referencia, "30 Sol/s")
        recompensa = 2500000000 / 1e8
        esperado = 30.0 * recompensa * 3600 / 3236492.75
        self.assertAlmostEqual(r.moneda_por_hora, esperado, places=6)

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

        def urlopen(peticion, timeout=None, **_kwargs):
            url = peticion.full_url if hasattr(peticion, "full_url") else peticion
            if "coingecko" in url:
                return _resp(PRECIOS_COINGECKO)
            return _resp(stats_sin_reward)

        with patch("urllib.request.urlopen", side_effect=urlopen):
            self.assertIsNone(est.estimar_referencia("SAL"))

    def test_sin_precio_da_none(self):
        # Las fuentes de dificultad responden, pero CoinGecko no trae el precio.
        def urlopen(peticion, timeout=None, **_kwargs):
            url = peticion.full_url if hasattr(peticion, "full_url") else peticion
            if "coingecko" in url:
                return _resp({})  # sin precios
            return _urlopen_por_url(peticion, timeout)

        with patch("urllib.request.urlopen", side_effect=urlopen):
            self.assertIsNone(est.estimar_referencia("XMR"))


class TestCachePrecios(BaseEstimacion):
    def test_precio_se_cachea_una_sola_peticion(self):
        llamadas = {"coingecko": 0}

        def urlopen(peticion, timeout=None, **_kwargs):
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


class TestEscalarAHashrate(unittest.TestCase):
    def test_escala_proporcionalmente_sin_red(self):
        base = est.EstimacionReferencia(
            simbolo="XMR", hashrate_referencia="1 kH/s",
            moneda_por_hora=0.01, usd_por_hora=4.3, fuente="test",
        )
        # El doble de la referencia (1000 H/s) -> el doble de ingreso.
        moneda_h, usd_h = est.escalar_a_hashrate(base, 2000.0)
        self.assertAlmostEqual(moneda_h, 0.02)
        self.assertAlmostEqual(usd_h, 8.6)

    def test_no_hace_ninguna_peticion_de_red(self):
        base = est.EstimacionReferencia(
            simbolo="RVN", hashrate_referencia="10 MH/s",
            moneda_por_hora=1.0, usd_por_hora=0.5, fuente="test",
        )
        with patch("urllib.request.urlopen", side_effect=AssertionError("no debería llamar a la red")):
            est.escalar_a_hashrate(base, 5e6)  # no lanza AssertionError


if __name__ == "__main__":
    unittest.main()
