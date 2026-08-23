import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import motores  # noqa: E402


class TestMotores(unittest.TestCase):
    def test_encontrar_motor_desconocido_devuelve_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(motores.encontrar_motor("motor-que-no-existe", Path(d)))

    def test_encontrar_motor_en_carpeta_bin_del_proyecto(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            bin_dir = raiz / "bin"
            bin_dir.mkdir()
            falso_kawpowminer = bin_dir / "kawpowminer"
            falso_kawpowminer.write_text("#!/bin/sh\necho hola\n")
            falso_kawpowminer.chmod(falso_kawpowminer.stat().st_mode | stat.S_IEXEC)

            encontrado = motores.encontrar_motor("kawpowminer", raiz)
        self.assertIsNotNone(encontrado)
        self.assertTrue(encontrado.endswith("kawpowminer"))

    def test_ignora_una_carpeta_con_el_mismo_nombre_que_el_binario(self):
        # Regresión: src/instalador.py extrae cada motor descargado en
        # bin/<nombre_motor>/ (por ejemplo bin/xmrig/), que se llama igual
        # que uno de los nombres candidatos sin extensión ("xmrig"). Antes
        # de arreglar esto, esa carpeta "ganaba" al ejecutable real
        # (bin/xmrig.exe) porque solo se comprobaba candidato.exists(), y
        # arrancar una carpeta como si fuera un programa fallaba en Windows
        # con PermissionError (WinError 5).
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            bin_dir = raiz / "bin"
            bin_dir.mkdir()
            (bin_dir / "xmrig").mkdir()  # carpeta de extracción, mismo nombre
            (bin_dir / "xmrig" / "xmrig-6.26.0").mkdir()
            binario_real = bin_dir / "xmrig.exe"
            binario_real.write_text("contenido de mentira")

            encontrado = motores.encontrar_motor("xmrig", raiz)
        self.assertEqual(encontrado, str(binario_real))

    def test_todos_los_motores_referenciados_tienen_constructor(self):
        for nombre, info in motores.MOTORES.items():
            self.assertTrue(callable(info["construir_comando"]), msg=nombre)
            self.assertIn("comision_pct", info, msg=nombre)
            self.assertIn("nombres_binario", info, msg=nombre)


if __name__ == "__main__":
    unittest.main()
