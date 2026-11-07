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


class TestApiReservasi(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data = Path(self.temp_dir.name) / "data_api_test.json"
        shutil.copyfile(DATA_FILE, self.test_data)
        with patch.object(app_module, "DATA_FILE", self.test_data):
            self.app = app_module.create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_dokter_dapat_memfilter_poli(self):
        """Menguji GET /api/dokter dengan filter poli anak."""
        response = self.client.get("/api/dokter?poli=anak")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.get_json()], ["D02"])

    def test_get_slot_mengembalikan_slot_kosong(self):
        """Menguji GET /api/slot dan memastikan slot aktif tidak tersedia."""
        response = self.client.get("/api/slot?dokter=D01&tanggal=2026-10-26")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["hari"], "senin")
        self.assertEqual(len(payload["slot_kosong"]), 11)
        self.assertNotIn("08:00", payload["slot_kosong"])
        self.assertIn("08:40", payload["slot_kosong"])

    def test_post_reservasi_mengembalikan_detail_reservasi(self):
        """Menguji POST /api/reservasi untuk reservasi yang berhasil."""
        response = self.client.post(
            "/api/reservasi",
            json={"no_rm": "RM0004", "dokter": "D01", "tanggal": "2026-10-26", "jam": "10:00"},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["umur"], 60)
        self.assertEqual(payload["biaya"], 65_000)
        self.assertEqual(payload["antrian"], 3)
        self.assertEqual(payload["kode"], "RSV-D01-20261026-03")

    def test_post_reservasi_menolak_pasien_ganda(self):
        """Menguji POST /api/reservasi menolak pasien ganda dengan status 409."""
        response = self.client.post(
            "/api/reservasi",
            json={"no_rm": "RM0001", "dokter": "D01", "tanggal": "2026-11-04", "jam": "08:20"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.get_json()["error"],
            "Pasien sudah punya reservasi dengan dokter ini pada tanggal tersebut",
        )

    def test_post_reservasi_menolak_dokter_tidak_ditemukan(self):
        """Menguji POST /api/reservasi untuk dokter yang tidak terdaftar."""
        response = self.client.post(
            "/api/reservasi",
            json={"no_rm": "RM0001", "dokter": "D99", "tanggal": "2026-10-26", "jam": "10:00"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "Dokter tidak ditemukan")

    def test_batal_dan_rekap_api(self):
        """Menguji pembatalan reservasi dan pembacaan rekap melalui API."""
        dibuat = self.client.post(
            "/api/reservasi",
            json={"no_rm": "RM0001", "dokter": "D01", "tanggal": "2026-11-09", "jam": "08:00"},
        ).get_json()

        dibatalkan = self.client.post(
            "/api/batal",
            json={"kode": dibuat["kode"], "hari_ini": "2026-11-08"},
        )
        rekap = self.client.get("/api/rekap?tanggal=2026-10-26")

        self.assertEqual(dibatalkan.status_code, 200)
        self.assertEqual(dibatalkan.get_json()["status"], "batal")
        self.assertEqual(rekap.status_code, 200)
        self.assertEqual(rekap.get_json()["per_poli"]["umum"]["pasien"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
