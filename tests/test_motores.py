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

    def test_todos_los_motores_referenciados_tienen_constructor(self):
        for nombre, info in motores.MOTORES.items():
            self.assertTrue(callable(info["construir_comando"]), msg=nombre)
            self.assertIn("comision_pct", info, msg=nombre)
            self.assertIn("nombres_binario", info, msg=nombre)


if __name__ == "__main__":
    unittest.main()
