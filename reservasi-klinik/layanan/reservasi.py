"""Layanan inti reservasi klinik tanpa ketergantungan pada Flask."""

import datetime as dt

from config import BIAYA_ADMIN, DISKON_LANSIA_PERSEN, USIA_LANSIA
from .jadwal import buat_slot, hari_dari_tanggal


class ReservasiError(Exception):
    """Kesalahan aturan bisnis dengan pesan yang ditampilkan ke pengguna."""

    def __init__(self, pesan: str, status: int = 400):
        super().__init__(pesan)
        self.pesan = pesan
        self.status = status


class DataTidakDitemukan(ReservasiError):
    pass


def cari_pasien(data: dict, no_rm: str) -> dict | None:
    return next((pasien for pasien in data["pasien"] if pasien["no_rm"] == no_rm), None)


def cari_dokter(data: dict, id_dokter: str) -> dict | None:
    return next((dokter for dokter in data["dokter"] if dokter["id"] == id_dokter), None)


def daftar_dokter(data: dict, poli: str = "") -> list[dict]:
    return [dokter for dokter in data["dokter"] if not poli or dokter["poli"] == poli]


def hitung_umur(tanggal_lahir: str, tanggal_kunjungan: dt.date) -> int:
    lahir = dt.date.fromisoformat(tanggal_lahir)
    return tanggal_kunjungan.year - lahir.year - (
        (tanggal_kunjungan.month, tanggal_kunjungan.day) < (lahir.month, lahir.day)
    )


def hitung_biaya(pasien: dict, dokter: dict, umur: int) -> int:
    if pasien["bpjs"]:
        return 0
    biaya = dokter["tarif"]
    if umur >= USIA_LANSIA:
        biaya -= biaya * DISKON_LANSIA_PERSEN // 100
    return biaya + BIAYA_ADMIN


def hitung_antrian(reservasi: list[dict], id_dokter: str, tanggal: str) -> int:
    jumlah = sum(
        item["dokter"] == id_dokter and item["tanggal"] == tanggal
        for item in reservasi
    )
    return jumlah + 1


def buat_kode(id_dokter: str, tanggal: str, antrian: int) -> str:
    return f"RSV-{id_dokter}-{tanggal.replace('-', '')}-{antrian:02d}"


def _validasi_data_reservasi(
    data: dict,
    no_rm: str,
    id_dokter: str,
    tanggal: str,
    jam: str,
) -> tuple[dict, dict, dt.date]:
    pasien = cari_pasien(data, no_rm)
    dokter = cari_dokter(data, id_dokter)
    if pasien is None:
        raise DataTidakDitemukan("No. rekam medis tidak terdaftar", 404)
    if dokter is None:
        raise DataTidakDitemukan("Dokter tidak ditemukan", 404)
    try:
        tgl = dt.date.fromisoformat(tanggal)
    except (ValueError, TypeError):
        raise ReservasiError("Tanggal tidak valid")
    hari = hari_dari_tanggal(tgl)
    if hari not in dokter["jadwal"]:
        raise ReservasiError(f"{dokter['nama']} tidak praktik hari {hari}")
    if jam not in buat_slot(dokter["jadwal"], hari):
        raise ReservasiError(f"Jam {jam} di luar jadwal praktik")
    return pasien, dokter, tgl


def buat_reservasi(
    repo,
    no_rm: str,
    id_dokter: str,
    tanggal: str,
    jam: str,
    *,
    tolak_pasien_ganda: bool = False,
) -> tuple[dict, int]:
    data = repo.ambil_semua()
    pasien, dokter, tgl = _validasi_data_reservasi(data, no_rm, id_dokter, tanggal, jam)
    aktif = [
        item for item in data["reservasi"]
        if item["dokter"] == id_dokter
        and item["tanggal"] == tanggal
        and item["status"] == "aktif"
    ]
    if any(item["jam"] == jam for item in aktif):
        raise ReservasiError(f"Jam {jam} sudah terisi", 409)
    if tolak_pasien_ganda and any(item["no_rm"] == no_rm for item in aktif):
        raise ReservasiError(
            "Pasien sudah punya reservasi dengan dokter ini pada tanggal tersebut", 409
        )
    umur = hitung_umur(pasien["tgl_lahir"], tgl)
    antrian = hitung_antrian(data["reservasi"], id_dokter, tanggal)
    baru = {
        "kode": buat_kode(id_dokter, tanggal, antrian),
        "no_rm": no_rm,
        "dokter": id_dokter,
        "tanggal": tanggal,
        "jam": jam,
        "antrian": antrian,
        "biaya": hitung_biaya(pasien, dokter, umur),
        "status": "aktif",
    }
    data["reservasi"].append(baru)
    repo.simpan_semua(data)
    return baru, umur


def batalkan_reservasi(repo, kode: str, hari_ini: str) -> dict:
    data = repo.ambil_semua()
    for reservasi in data["reservasi"]:
        if reservasi["kode"] != kode:
            continue
        if reservasi["status"] != "aktif":
            raise ReservasiError("Reservasi sudah dibatalkan")
        if reservasi["tanggal"] <= hari_ini:
            raise ReservasiError("Pembatalan paling lambat H-1")
        reservasi["status"] = "batal"
        repo.simpan_semua(data)
        return {"kode": reservasi["kode"], "status": "batal"}
    raise DataTidakDitemukan("Kode reservasi tidak ditemukan", 404)


def rekap_harian(data: dict, tanggal: str) -> dict:
    per_poli = {}
    for reservasi in data["reservasi"]:
        if reservasi["tanggal"] != tanggal or reservasi["status"] != "aktif":
            continue
        dokter = cari_dokter(data, reservasi["dokter"])
        poli = dokter["poli"]
        nilai = per_poli.setdefault(poli, {"pasien": 0, "pendapatan": 0})
        nilai["pasien"] += 1
        nilai["pendapatan"] += reservasi["biaya"]
    return per_poli

