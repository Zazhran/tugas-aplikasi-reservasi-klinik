import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as app_module


DATA_FILE = ROOT / "data.json"


class TestRouteWeb(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data = Path(self.temp_dir.name) / "data_web_test.json"
        shutil.copyfile(DATA_FILE, self.test_data)
        with patch.object(app_module, "DATA_FILE", self.test_data):
            self.app = app_module.create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_halaman_utama_dan_filter_poli(self):
        """Menguji halaman utama dan filter daftar dokter berdasarkan poli."""
        response = self.client.get("/?poli=gigi")
        isi = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("drg. Farhan Hakim", isi)
        self.assertNotIn("dr. Aulia Rahman", isi)

    def test_form_reservasi_menampilkan_pesan_sukses(self):
        """Menguji submit form reservasi web yang berhasil."""
        response = self.client.post(
            "/reservasi",
            data={
                "no_rm": "RM0004",
                "dokter": "D01",
                "tanggal": "2026-10-26",
                "jam": "10:00",
            },
        )
        isi = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Reservasi berhasil", isi)
        self.assertIn("RSV-D01-20261026-03", isi)
        self.assertIn("Rp 65.000", isi)

    def test_form_reservasi_menampilkan_pesan_kesalahan(self):
        """Menguji form reservasi web menampilkan error pasien tidak terdaftar."""
        response = self.client.post(
            "/reservasi",
            data={
                "no_rm": "RM9999",
                "dokter": "D01",
                "tanggal": "2026-10-26",
                "jam": "10:00",
            },
        )

        self.assertIn("No. rekam medis tidak terdaftar", response.get_data(as_text=True))

    def test_halaman_rekap_menampilkan_data(self):
        """Menguji halaman rekap web menampilkan pasien dan pendapatan per poli."""
        response = self.client.get("/rekap?tanggal=2026-10-26")
        isi = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Rekap 2026-10-26", isi)
        self.assertIn("Poli penyakit dalam", isi)
        self.assertIn("Rp 165.000", isi)


if __name__ == "__main__":
    unittest.main(verbosity=2)
