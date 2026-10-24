"""Konfigurasi aplikasi dan konstanta aturan bisnis."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

NAMA_HARI = ("senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu")
INTERVAL_SLOT_MENIT = 20
USIA_LANSIA = 60
DISKON_LANSIA_PERSEN = 20
BIAYA_ADMIN = 5_000

