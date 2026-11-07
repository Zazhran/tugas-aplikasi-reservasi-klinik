import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from layanan import (
    DataTidakDitemukan,
    ReservasiError,
    batalkan_reservasi,
    buat_reservasi,
    rekap_harian,
)
from repositori import JsonRepository

DATA_FILE = ROOT / "data.json"


class TestLayananReservasi(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data = Path(self.temp_dir.name) / "data_test.json"
        shutil.copyfile(DATA_FILE, self.test_data)
        self.repo = JsonRepository(self.test_data)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_buat_reservasi_menghitung_umur_biaya_antrian_dan_kode(self):
        """Menguji pembuatan reservasi lengkap, termasuk umur, biaya, antrean, dan kode."""
        baru, umur = buat_reservasi(
            self.repo, "RM0004", "D01", "2026-10-26", "10:00"
        )

        self.assertEqual(umur, 60)
        self.assertEqual(baru["biaya"], 65_000)
        self.assertEqual(baru["antrian"], 3)
        self.assertEqual(baru["kode"], "RSV-D01-20261026-03")
        self.assertEqual(baru["status"], "aktif")
        self.assertEqual(self.repo.ambil_semua()["reservasi"][-1], baru)

    def test_buat_reservasi_menolak_jam_terisi(self):
        """Memastikan layanan menolak jam yang sudah dipakai reservasi aktif."""
        with self.assertRaisesRegex(ReservasiError, "Jam 08:00 sudah terisi") as konteks:
            buat_reservasi(self.repo, "RM0001", "D01", "2026-10-26", "08:00")

        self.assertEqual(konteks.exception.status, 409)

    def test_buat_reservasi_menolak_pasien_ganda_dengan_mode_api(self):
        """Memastikan mode API menolak pasien yang sudah punya reservasi aktif."""
        with self.assertRaisesRegex(ReservasiError, "Pasien sudah punya reservasi"):
            buat_reservasi(
                self.repo,
                "RM0001",
                "D01",
                "2026-11-04",
                "08:20",
                tolak_pasien_ganda=True,
            )

    def test_validasi_data_reservasi_menolak_data_tidak_valid(self):
        """Menguji penolakan pasien, dokter, tanggal, hari, dan jam yang tidak valid."""
        kasus = [
            ("RM9999", "D01", "2026-10-26", "10:00", "No. rekam medis tidak terdaftar"),
            ("RM0001", "D99", "2026-10-26", "10:00", "Dokter tidak ditemukan"),
            ("RM0001", "D01", "bukan-tanggal", "10:00", "Tanggal tidak valid"),
            ("RM0001", "D01", "2026-10-27", "10:00", "tidak praktik hari selasa"),
            ("RM0001", "D01", "2026-10-26", "12:00", "di luar jadwal praktik"),
        ]
        for no_rm, dokter, tanggal, jam, pesan in kasus:
            with self.subTest(pesan=pesan):
                with self.assertRaisesRegex(ReservasiError, pesan):
                    buat_reservasi(self.repo, no_rm, dokter, tanggal, jam)

    def test_batalkan_reservasi_hanya_diperbolehkan_h_minus_satu(self):
        """Memastikan reservasi dapat dibatalkan paling lambat satu hari sebelumnya."""
        baru, _ = buat_reservasi(
            self.repo, "RM0001", "D01", "2026-11-09", "08:00"
        )

        hasil = batalkan_reservasi(self.repo, baru["kode"], "2026-11-08")

        self.assertEqual(hasil, {"kode": baru["kode"], "status": "batal"})
        self.assertEqual(self.repo.ambil_semua()["reservasi"][-1]["status"], "batal")

    def test_batalkan_reservasi_menolak_hari_ini_atau_sesudahnya(self):
        """Memastikan pembatalan pada hari-H atau setelahnya ditolak."""
        with self.assertRaisesRegex(ReservasiError, "paling lambat H-1"):
            batalkan_reservasi(
                self.repo, "RSV-D01-20261102-01", "2026-11-02"
            )

    def test_batalkan_reservasi_menolak_kode_tidak_ditemukan(self):
        """Memastikan kode reservasi yang tidak ada menghasilkan error 404."""
        with self.assertRaises(DataTidakDitemukan) as konteks:
            batalkan_reservasi(self.repo, "RSV-TIDAK-ADA", "2026-10-01")

        self.assertEqual(konteks.exception.status, 404)

    def test_rekap_harian_mengabaikan_reservasi_batal(self):
        """Memastikan rekap harian hanya memuat reservasi berstatus aktif."""
        data = self.repo.ambil_semua()

        self.assertEqual(
            rekap_harian(data, "2026-10-26"),
            {
                "umum": {"pasien": 1, "pendapatan": 0},
                "penyakit dalam": {"pasien": 1, "pendapatan": 165_000},
            },
        )

    def test_repository_menyimpan_json_yang_dapat_dibaca_kembali(self):
        """Memastikan repository dapat menyimpan dan membaca kembali JSON."""
        data = self.repo.ambil_semua()
        data["catatan_test"] = "sementara"
        self.repo.simpan_semua(data)

        with self.test_data.open(encoding="utf-8") as file:
            tersimpan = json.load(file)
        self.assertEqual(tersimpan["catatan_test"], "sementara")


if __name__ == "__main__":
    unittest.main(verbosity=2)
