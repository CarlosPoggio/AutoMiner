import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import wallets_defecto  # noqa: E402


class TestCargarWalletsPorDefecto(unittest.TestCase):
    def test_fichero_inexistente_da_diccionario_vacio(self):
        self.assertEqual(wallets_defecto.cargar_wallets_por_defecto(Path("no_existe.md")), {})

    def test_parsea_lineas_validas_e_ignora_comentarios_y_mayusculas(self):
        contenido = (
            "# comentario\n"
            "\n"
            "xmr: 4wallet123\n"
            "RVN: Rwallet456\n"
            "# KAS: comentada, no cuenta\n"
        )
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "wallets.md"
            ruta.write_text(contenido, encoding="utf-8")
            resultado = wallets_defecto.cargar_wallets_por_defecto(ruta)
        self.assertEqual(resultado, {"XMR": "4wallet123", "RVN": "Rwallet456"})

    def test_ignora_lineas_con_valor_vacio(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "wallets.md"
            ruta.write_text("XMR:   \nRVN: Rwallet456\n", encoding="utf-8")
            resultado = wallets_defecto.cargar_wallets_por_defecto(ruta)
        self.assertEqual(resultado, {"RVN": "Rwallet456"})


if __name__ == "__main__":
    unittest.main()
