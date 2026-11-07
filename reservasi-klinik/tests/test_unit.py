import datetime as dt
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from layanan import (
    buat_slot,
    cari_dokter,
    cari_pasien,
    daftar_dokter,
    hari_dari_tanggal,
    hitung_antrian,
    hitung_biaya,
    hitung_umur,
    rekap_harian,
    slot_kosong,
)
from utils import format_rupiah


class TestJadwal(unittest.TestCase):
    def test_hari_dari_tanggal(self):
        """Memastikan tanggal dikonversi ke nama hari berbahasa Indonesia."""
        self.assertEqual(hari_dari_tanggal(dt.date(2026, 10, 26)), "senin")
        self.assertEqual(hari_dari_tanggal(dt.date(2026, 10, 31)), "sabtu")

    def test_buat_slot_setiap_dua_puluh_menit(self):
        """Memastikan jadwal dipecah menjadi slot praktik 20 menit."""
        jadwal = {"senin": ["08:00", "09:00"]}

        self.assertEqual(
            buat_slot(jadwal, "senin"),
            ["08:00", "08:20", "08:40"],
        )
        self.assertEqual(buat_slot(jadwal, "minggu"), [])

    def test_slot_kosong_hanya_menghitung_reservasi_aktif(self):
        """Memastikan reservasi batal tidak menutup slot jadwal."""
        dokter = {
            "id": "D01",
            "jadwal": {"senin": ["08:00", "09:00"]},
        }
        reservasi = [
            {"dokter": "D01", "tanggal": "2026-10-26", "jam": "08:00", "status": "aktif"},
            {"dokter": "D01", "tanggal": "2026-10-26", "jam": "08:20", "status": "batal"},
        ]

        hasil = slot_kosong(dokter, "2026-10-26", reservasi)

        self.assertEqual(hasil["hari"], "senin")
        self.assertEqual(hasil["slot_kosong"], ["08:20", "08:40"])


class TestFungsiBisnisMurni(unittest.TestCase):
    def setUp(self):
        self.data = {
            "dokter": [
                {"id": "D01", "nama": "Dokter Umum", "poli": "umum", "tarif": 75_000},
                {"id": "D02", "nama": "Dokter Anak", "poli": "anak", "tarif": 150_000},
            ],
            "pasien": [
                {"no_rm": "RM0001", "tgl_lahir": "1990-05-12", "bpjs": False},
                {"no_rm": "RM0002", "tgl_lahir": "1960-11-02", "bpjs": False},
                {"no_rm": "RM0003", "tgl_lahir": "2019-03-08", "bpjs": True},
            ],
            "reservasi": [
                {"dokter": "D01", "tanggal": "2026-10-26", "status": "aktif"},
                {"dokter": "D01", "tanggal": "2026-10-26", "status": "batal"},
            ],
        }

    def test_pencarian_dan_filter_dokter(self):
        """Memastikan pencarian pasien/dokter dan filter poli bekerja."""
        self.assertEqual(cari_pasien(self.data, "RM0001")["no_rm"], "RM0001")
        self.assertIsNone(cari_pasien(self.data, "RM9999"))
        self.assertEqual(cari_dokter(self.data, "D01")["poli"], "umum")
        self.assertEqual([d["id"] for d in daftar_dokter(self.data, "anak")], ["D02"])
        self.assertEqual(len(daftar_dokter(self.data)), 2)

    def test_hitung_umur_memperhatikan_hari_ulang_tahun(self):
        """Memastikan umur berubah tepat pada hari ulang tahun."""
        self.assertEqual(hitung_umur("1990-05-12", dt.date(2026, 5, 11)), 35)
        self.assertEqual(hitung_umur("1990-05-12", dt.date(2026, 5, 12)), 36)

    def test_hitung_biaya_bpjs_reguler_dan_lansia(self):
        """Memastikan biaya BPJS gratis, tarif normal, dan diskon lansia."""
        dokter = {"tarif": 75_000}
        reguler = {"bpjs": False}
        bpjs = {"bpjs": True}

        self.assertEqual(hitung_biaya(bpjs, dokter, 20), 0)
        self.assertEqual(hitung_biaya(reguler, dokter, 35), 80_000)
        self.assertEqual(hitung_biaya(reguler, dokter, 60), 65_000)

    def test_hitung_antrian_menghasilkan_nomor_berikutnya(self):
        """Memastikan nomor antrean mengikuti jumlah reservasi dokter dan tanggal."""
        self.assertEqual(hitung_antrian(self.data["reservasi"], "D01", "2026-10-26"), 3)
        self.assertEqual(hitung_antrian(self.data["reservasi"], "D02", "2026-10-26"), 1)

    def test_rekap_hanya_memasukkan_reservasi_aktif(self):
        """Memastikan rekap menghitung pasien dan pendapatan aktif saja."""
        self.data["reservasi"][0].update({"dokter": "D01", "no_rm": "RM0001", "biaya": 80_000})
        self.data["reservasi"][1].update({"dokter": "D01", "no_rm": "RM0002", "biaya": 65_000})

        self.assertEqual(
            rekap_harian(self.data, "2026-10-26"),
            {"umum": {"pasien": 1, "pendapatan": 80_000}},
        )

    def test_format_rupiah(self):
        """Memastikan angka biaya diformat dengan pemisah ribuan Indonesia."""
        self.assertEqual(format_rupiah(65_000), "65.000")
        self.assertEqual(format_rupiah(0), "0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
