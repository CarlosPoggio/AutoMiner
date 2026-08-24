import io
import json
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import instalador  # noqa: E402


def _assets(nombres):
    return [{"name": n, "browser_download_url": f"https://example.test/{n}"} for n in nombres]


ASSETS_XMRIG = _assets([
    "xmrig-6.26.0-windows-x64.zip",
    "xmrig-6.26.0-windows-gcc-x64.zip",
    "xmrig-6.26.0-windows-arm64.zip",
    "xmrig-6.26.0-linux-static-x64.tar.gz",
    "xmrig-6.26.0-focal-x64.tar.gz",
    "xmrig-6.26.0-jammy-x64.tar.gz",
    "xmrig-6.26.0-noble-x64.tar.gz",
    "xmrig-6.26.0-macos-x64.tar.gz",
    "xmrig-6.26.0-macos-arm64.tar.gz",
    "SHA256SUMS",
])

ASSETS_KAWPOW = _assets([
    "kawpowminer-windows-1.2.4-opencl.zip",
    "kawpowminer-windows-cuda11-1.2.4.zip",
    "kawpowminer-ubuntu20-opencl-1.2.4.tar.gz",
    "kawpowminer-ubuntu20-cuda11-1.2.4.tar.gz",
    "kawpowminer-ubuntu18-cuda11-1.2.4.tar.gz",
])

ASSETS_LOL = _assets([
    "lolMiner_v1.98a_Win64.zip",
    "lolMiner_v1.98a_Win64_cln.zip",
    "lolMiner_v1.98a_Lin64.tar.gz",
])


class TestSeleccionAsset(unittest.TestCase):
    def _nombre(self, *args, **kwargs):
        return instalador.seleccionar_asset(*args, **kwargs)["name"]

    def test_xmrig_windows(self):
        self.assertEqual(self._nombre("xmrig", "Windows", ASSETS_XMRIG), "xmrig-6.26.0-windows-x64.zip")

    def test_xmrig_linux(self):
        self.assertEqual(self._nombre("xmrig", "Linux", ASSETS_XMRIG), "xmrig-6.26.0-linux-static-x64.tar.gz")

    def test_xmrig_macos_arm(self):
        self.assertEqual(self._nombre("xmrig", "Darwin", ASSETS_XMRIG, arch="arm64"), "xmrig-6.26.0-macos-arm64.tar.gz")

    def test_xmrig_macos_intel(self):
        self.assertEqual(self._nombre("xmrig", "Darwin", ASSETS_XMRIG, arch="x86_64"), "xmrig-6.26.0-macos-x64.tar.gz")

    def test_kawpow_windows_nvidia_usa_cuda(self):
        self.assertEqual(
            self._nombre("kawpowminer", "Windows", ASSETS_KAWPOW, fabricante_gpu="NVIDIA"),
            "kawpowminer-windows-cuda11-1.2.4.zip",
        )

    def test_kawpow_windows_amd_usa_opencl(self):
        self.assertEqual(
            self._nombre("kawpowminer", "Windows", ASSETS_KAWPOW, fabricante_gpu="AMD"),
            "kawpowminer-windows-1.2.4-opencl.zip",
        )

    def test_kawpow_linux_nvidia_usa_ubuntu20_cuda(self):
        self.assertEqual(
            self._nombre("kawpowminer", "Linux", ASSETS_KAWPOW, fabricante_gpu="NVIDIA"),
            "kawpowminer-ubuntu20-cuda11-1.2.4.tar.gz",
        )

    def test_kawpow_darwin_lanza_error(self):
        with self.assertRaises(instalador.InstaladorError):
            instalador.seleccionar_asset("kawpowminer", "Darwin", ASSETS_KAWPOW, fabricante_gpu="NVIDIA")

    def test_lolminer_windows_excluye_cln(self):
        self.assertEqual(self._nombre("lolminer", "Windows", ASSETS_LOL), "lolMiner_v1.98a_Win64.zip")

    def test_lolminer_linux(self):
        self.assertEqual(self._nombre("lolminer", "Linux", ASSETS_LOL), "lolMiner_v1.98a_Lin64.tar.gz")

    def test_lolminer_darwin_lanza_error(self):
        with self.assertRaises(instalador.InstaladorError):
            instalador.seleccionar_asset("lolminer", "Darwin", ASSETS_LOL)

    def test_sin_asset_valido_lanza_error(self):
        with self.assertRaises(instalador.InstaladorError):
            instalador.seleccionar_asset("xmrig", "Windows", _assets(["solo-linux.tar.gz"]))


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_targz(nombre_interno, contenido=b"#!/bin/sh\necho fake\n"):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        info = tarfile.TarInfo(name=nombre_interno)
        info.size = len(contenido)
        t.addfile(info, io.BytesIO(contenido))
    return buf.getvalue()


def _fake_targz_multi(archivos: dict):
    """Como _fake_targz, pero con varios ficheros dentro (nombre -> contenido)."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for nombre_interno, contenido in archivos.items():
            info = tarfile.TarInfo(name=nombre_interno)
            info.size = len(contenido)
            t.addfile(info, io.BytesIO(contenido))
    return buf.getvalue()


def _fake_zip_multi(archivos: dict):
    """Como _fake_targz_multi, pero en .zip (nombre -> contenido)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for nombre_interno, contenido in archivos.items():
            z.writestr(nombre_interno, contenido)
    return buf.getvalue()


class TestAsegurarMotor(unittest.TestCase):
    def test_no_descarga_si_ya_esta_en_bin(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            bin_dir = raiz / "bin"
            bin_dir.mkdir()
            (bin_dir / "xmrig").write_text("fake")
            # shutil.which mockeado a propósito: sin esto, el test depende
            # de que el PATH real de la máquina no tenga ningún "xmrig" —
            # cierto casi siempre, pero no garantizado (se vio fallar una
            # vez de forma no reproducible).
            with patch("motores.shutil.which", return_value=None), \
                 patch("instalador.urllib.request.urlopen") as mock_urlopen:
                ruta = instalador.asegurar_motor("xmrig", raiz)
            mock_urlopen.assert_not_called()
            self.assertTrue(ruta.endswith("xmrig"))

    def test_descarga_extrae_y_copia_binario(self):
        release = {"tag_name": "v6.26.0", "assets": ASSETS_XMRIG}
        targz = _fake_targz("xmrig-6.26.0/xmrig")

        def fake_urlopen(peticion, timeout=None, **_kwargs):
            url = getattr(peticion, "full_url", peticion)
            if "api.github.com" in url:
                return FakeResp(json.dumps(release).encode())
            return FakeResp(targz)

        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            with patch("instalador.platform.system", return_value="Linux"), \
                 patch("instalador.platform.machine", return_value="x86_64"), \
                 patch("motores.shutil.which", return_value=None), \
                 patch("instalador.urllib.request.urlopen", side_effect=fake_urlopen):
                ruta = instalador.asegurar_motor("xmrig", raiz)

            self.assertTrue(Path(ruta).exists())
            self.assertEqual(Path(ruta).name, "xmrig")
            self.assertEqual(Path(ruta).parent, raiz / "bin")

    def test_copia_ficheros_acompanantes_en_instalacion_nueva(self):
        release = {"tag_name": "v6.26.0", "assets": ASSETS_XMRIG}
        targz = _fake_targz_multi({
            "xmrig-6.26.0/xmrig": b"#!/bin/sh\necho fake\n",
            "xmrig-6.26.0/WinRing0x64.sys": b"contenido de mentira del driver",
        })

        def fake_urlopen(peticion, timeout=None, **_kwargs):
            url = getattr(peticion, "full_url", peticion)
            if "api.github.com" in url:
                return FakeResp(json.dumps(release).encode())
            return FakeResp(targz)

        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            with patch("instalador.platform.system", return_value="Linux"), \
                 patch("instalador.platform.machine", return_value="x86_64"), \
                 patch("motores.shutil.which", return_value=None), \
                 patch("instalador.urllib.request.urlopen", side_effect=fake_urlopen):
                instalador.asegurar_motor("xmrig", raiz)

            self.assertTrue((raiz / "bin" / "WinRing0x64.sys").exists())

    def test_autosana_ficheros_acompanantes_de_una_instalacion_previa(self):
        # Simula una instalación de antes de que existiera esta comprobación
        # (como la real, en Windows): el binario plano ya está en bin/ como
        # xmrig.exe, y la carpeta descomprimida bin/xmrig/ (mismo nombre que
        # el binario sin extensión, sin chocar con el .exe) sigue ahí con el
        # driver dentro, pero nunca se copió a bin/.
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            bin_dir = raiz / "bin"
            bin_dir.mkdir()
            (bin_dir / "xmrig.exe").write_text("fake")
            extraido = bin_dir / "xmrig" / "xmrig-6.26.0"
            extraido.mkdir(parents=True)
            (extraido / "WinRing0x64.sys").write_text("driver de mentira")

            # shutil.which mockeado a propósito: sin esto, el test depende de
            # que el PATH real de la máquina no tenga ningún "xmrig" — visto
            # fallar de forma no reproducible, igual que en
            # test_no_descarga_si_ya_esta_en_bin.
            with patch("motores.shutil.which", return_value=None), \
                 patch("instalador.urllib.request.urlopen") as mock_urlopen:
                instalador.asegurar_motor("xmrig", raiz)
            mock_urlopen.assert_not_called()  # no hace falta descargar nada

            self.assertTrue((bin_dir / "WinRing0x64.sys").exists())

    def test_kawpowminer_nvidia_copia_las_dll_de_nvrtc(self):
        # Reproduce el bug real reportado en GPU_ERROR.md: la build cuda11
        # de kawpowminer no arranca sin sus DLLs de NVRTC, y antes del
        # arreglo solo se copiaba el .exe a bin/.
        release = {"tag_name": "1.2.4", "assets": ASSETS_KAWPOW}
        zip_bytes = _fake_zip_multi({
            "kawpowminer-windows-cuda11-1.2.4/kawpowminer.exe": b"exe de mentira",
            "kawpowminer-windows-cuda11-1.2.4/nvrtc64_112_0.dll": b"dll de mentira",
            "kawpowminer-windows-cuda11-1.2.4/nvrtc-builtins64_112.dll": b"otra dll de mentira",
        })

        def fake_urlopen(peticion, timeout=None, **_kwargs):
            url = getattr(peticion, "full_url", peticion)
            if "api.github.com" in url:
                return FakeResp(json.dumps(release).encode())
            return FakeResp(zip_bytes)

        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            with patch("instalador.platform.system", return_value="Windows"), \
                 patch("motores.shutil.which", return_value=None), \
                 patch("instalador.urllib.request.urlopen", side_effect=fake_urlopen):
                instalador.asegurar_motor("kawpowminer", raiz, fabricante_gpu="NVIDIA")

            self.assertTrue((raiz / "bin" / "kawpowminer.exe").exists())
            self.assertTrue((raiz / "bin" / "nvrtc64_112_0.dll").exists())
            self.assertTrue((raiz / "bin" / "nvrtc-builtins64_112.dll").exists())

    def test_kawpowminer_darwin_no_toca_red(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            with patch("instalador.platform.system", return_value="Darwin"), \
                 patch("motores.shutil.which", return_value=None), \
                 patch("instalador.urllib.request.urlopen") as mock_urlopen:
                with self.assertRaises(instalador.InstaladorError):
                    instalador.asegurar_motor("kawpowminer", raiz, fabricante_gpu="NVIDIA")
            mock_urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
