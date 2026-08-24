import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import limpieza  # noqa: E402


class TestElementosBin(unittest.TestCase):
    def test_carpeta_bin_inexistente_da_lista_vacia(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(limpieza.elementos_bin_a_borrar(Path(d)), [])

    def test_conserva_leeme_pero_no_lo_demas(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            carpeta_bin = raiz / "bin"
            carpeta_bin.mkdir()
            (carpeta_bin / "LEEME.md").write_text("hola")
            (carpeta_bin / "xmrig.exe").write_text("binario")
            (carpeta_bin / "kawpowminer").mkdir()
            (carpeta_bin / "kawpowminer" / "algo.dll").write_text("dll")

            elementos = limpieza.elementos_bin_a_borrar(raiz)
            nombres = {p.name for p in elementos}

        self.assertEqual(nombres, {"xmrig.exe", "kawpowminer"})
        self.assertNotIn("LEEME.md", nombres)


class TestBorrarBin(unittest.TestCase):
    def _preparar(self, raiz: Path):
        carpeta_bin = raiz / "bin"
        carpeta_bin.mkdir()
        (carpeta_bin / "LEEME.md").write_text("hola")
        (carpeta_bin / "xmrig.exe").write_text("binario")
        (carpeta_bin / "lolminer").mkdir()
        (carpeta_bin / "lolminer" / "lolMiner.exe").write_text("binario")

    def test_dry_run_no_borra_nada(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            self._preparar(raiz)
            elementos = limpieza.borrar_bin(raiz, dry_run=True)
            self.assertEqual({p.name for p in elementos}, {"xmrig.exe", "lolminer"})
            # Sigue todo en su sitio.
            self.assertTrue((raiz / "bin" / "xmrig.exe").exists())
            self.assertTrue((raiz / "bin" / "lolminer").exists())
            self.assertTrue((raiz / "bin" / "LEEME.md").exists())

    def test_borra_de_verdad_pero_conserva_leeme(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            self._preparar(raiz)
            limpieza.borrar_bin(raiz, dry_run=False)
            self.assertFalse((raiz / "bin" / "xmrig.exe").exists())
            self.assertFalse((raiz / "bin" / "lolminer").exists())
            self.assertTrue((raiz / "bin" / "LEEME.md").exists())


class TestBorrarConfig(unittest.TestCase):
    def test_sin_config_devuelve_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(limpieza.borrar_config(Path(d), dry_run=False))

    def test_dry_run_no_borra(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "config.md").write_text("cpu_moneda: XMR")
            resultado = limpieza.borrar_config(raiz, dry_run=True)
            self.assertEqual(resultado.name, "config.md")
            self.assertTrue((raiz / "config.md").exists())

    def test_borra_de_verdad(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "config.md").write_text("cpu_moneda: XMR")
            limpieza.borrar_config(raiz, dry_run=False)
            self.assertFalse((raiz / "config.md").exists())


class TestLogsSueltos(unittest.TestCase):
    def test_encuentra_solo_logs_en_la_raiz(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "lolMiner.log").write_text("log")
            (raiz / "wallets.md").write_text("XMR: algo")
            (raiz / "bin").mkdir()
            (raiz / "bin" / "otro.log").write_text("no cuenta, esta en bin/")

            logs = limpieza.buscar_logs_sueltos(raiz)

        self.assertEqual([p.name for p in logs], ["lolMiner.log"])

    def test_borrar_logs_sueltos_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "a.log").write_text("log")
            limpieza.borrar_logs_sueltos(raiz, dry_run=True)
            self.assertTrue((raiz / "a.log").exists())

    def test_borrar_logs_sueltos_de_verdad(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "a.log").write_text("log")
            limpieza.borrar_logs_sueltos(raiz, dry_run=False)
            self.assertFalse((raiz / "a.log").exists())


class _ModuloFalso:
    """Simula aislamiento_nucleo.py / lista_controladores_vulnerables.py:
    misma forma (RUTA_MARCA, reactivar())."""

    def __init__(self, ruta_marca: Path, ok_al_reactivar=True):
        self.RUTA_MARCA = ruta_marca
        self._ok = ok_al_reactivar
        self.reactivado = False

    def reactivar(self):
        self.reactivado = True
        return self._ok, "reactivado" if self._ok else "fallo simulado"


class TestRevertirProteccionesSeguridad(unittest.TestCase):
    def test_sin_marca_no_hace_nada(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            falso1 = _ModuloFalso(raiz / "_marca1")
            falso2 = _ModuloFalso(raiz / "_marca2")
            with patch.object(limpieza, "aislamiento_nucleo", falso1), \
                 patch.object(limpieza, "lista_controladores_vulnerables", falso2):
                resultados = limpieza.revertir_protecciones_seguridad(raiz, dry_run=False)

        self.assertEqual(resultados, [])
        self.assertFalse(falso1.reactivado)
        self.assertFalse(falso2.reactivado)

    def test_con_marca_reactiva_y_borra_la_marca(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            marca = raiz / "_marca1"
            marca.write_text("la app desactivo esto")
            falso1 = _ModuloFalso(marca, ok_al_reactivar=True)
            falso2 = _ModuloFalso(raiz / "_marca2")
            with patch.object(limpieza, "aislamiento_nucleo", falso1), \
                 patch.object(limpieza, "lista_controladores_vulnerables", falso2):
                resultados = limpieza.revertir_protecciones_seguridad(raiz, dry_run=False)

        self.assertEqual(len(resultados), 1)
        self.assertTrue(falso1.reactivado)
        self.assertFalse(marca.exists())  # se borra la marca al reactivar bien

    def test_dry_run_no_reactiva_ni_borra_la_marca(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            marca = raiz / "_marca1"
            marca.write_text("la app desactivo esto")
            falso1 = _ModuloFalso(marca)
            falso2 = _ModuloFalso(raiz / "_marca2")
            with patch.object(limpieza, "aislamiento_nucleo", falso1), \
                 patch.object(limpieza, "lista_controladores_vulnerables", falso2):
                limpieza.revertir_protecciones_seguridad(raiz, dry_run=True)

            self.assertFalse(falso1.reactivado)
            self.assertTrue(marca.exists())

    def test_si_falla_reactivar_no_borra_la_marca(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            marca = raiz / "_marca1"
            marca.write_text("la app desactivo esto")
            falso1 = _ModuloFalso(marca, ok_al_reactivar=False)
            falso2 = _ModuloFalso(raiz / "_marca2")
            with patch.object(limpieza, "aislamiento_nucleo", falso1), \
                 patch.object(limpieza, "lista_controladores_vulnerables", falso2):
                resultados = limpieza.revertir_protecciones_seguridad(raiz, dry_run=False)

            self.assertFalse(resultados[0][1])  # ok == False
            self.assertTrue(marca.exists())  # no se borra si no se pudo reactivar


class TestRevocarHugePages(unittest.TestCase):
    def test_dry_run_no_llama_a_windows(self):
        with patch.object(limpieza.rendimiento_windows, "revocar_privilegio_huge_pages") as mock_revocar:
            ok, mensaje = limpieza.revocar_huge_pages(dry_run=True)
        self.assertTrue(ok)
        mock_revocar.assert_not_called()

    def test_de_verdad_delega_en_rendimiento_windows(self):
        with patch.object(
            limpieza.rendimiento_windows, "revocar_privilegio_huge_pages", return_value=(True, "hecho")
        ) as mock_revocar:
            ok, mensaje = limpieza.revocar_huge_pages(dry_run=False)
        self.assertTrue(ok)
        self.assertEqual(mensaje, "hecho")
        mock_revocar.assert_called_once()


class TestPasosMejorEsfuerzo(unittest.TestCase):
    """quitar_reglas_firewall / quitar_exclusion_defender /
    quitar_servicio_winring0: en dry-run no deben tocar nada; en real,
    nunca deben lanzar una excepción aunque el comando externo falle."""

    def test_dry_run_no_ejecuta_comandos(self):
        with tempfile.TemporaryDirectory() as d, \
             patch.object(limpieza, "_ejecutar_mejor_esfuerzo") as mock_ejecutar, \
             patch.object(limpieza.platform, "system", return_value="Windows"):
            limpieza.quitar_reglas_firewall(Path(d), dry_run=True)
            limpieza.quitar_exclusion_defender(Path(d), dry_run=True)
            limpieza.quitar_servicio_winring0(dry_run=True)
        mock_ejecutar.assert_not_called()

    def test_no_windows_no_hace_nada(self):
        with tempfile.TemporaryDirectory() as d, \
             patch.object(limpieza, "_ejecutar_mejor_esfuerzo") as mock_ejecutar, \
             patch.object(limpieza.platform, "system", return_value="Linux"):
            ok, _ = limpieza.quitar_reglas_firewall(Path(d), dry_run=False)
        self.assertTrue(ok)
        mock_ejecutar.assert_not_called()

    def test_fallo_del_comando_no_lanza_excepcion(self):
        with tempfile.TemporaryDirectory() as d, \
             patch.object(limpieza, "_ejecutar_mejor_esfuerzo", return_value=False), \
             patch.object(limpieza.platform, "system", return_value="Windows"):
            ok, mensaje = limpieza.quitar_servicio_winring0(dry_run=False)
        self.assertFalse(ok)
        self.assertIsInstance(mensaje, str)


if __name__ == "__main__":
    unittest.main()
