"""Aturan bisnis yang berkaitan dengan hari praktik dan slot dokter."""

import datetime as dt

from config import INTERVAL_SLOT_MENIT, NAMA_HARI


def hari_dari_tanggal(tanggal: dt.date) -> str:
    return NAMA_HARI[tanggal.weekday()]


def buat_slot(jadwal: dict, hari: str) -> list[str]:
    if hari not in jadwal:
        return []
    mulai = dt.datetime.strptime(jadwal[hari][0], "%H:%M")
    selesai = dt.datetime.strptime(jadwal[hari][1], "%H:%M")
    slot = []
    while mulai < selesai:
        slot.append(mulai.strftime("%H:%M"))
        mulai += dt.timedelta(minutes=INTERVAL_SLOT_MENIT)
    return slot


def slot_kosong(dokter: dict, tanggal: str, reservasi: list[dict]) -> dict:
    tgl = dt.date.fromisoformat(tanggal)
    hari = hari_dari_tanggal(tgl)
    semua_slot = buat_slot(dokter["jadwal"], hari)
    terisi = {
        item["jam"]
        for item in reservasi
        if item["dokter"] == dokter["id"]
        and item["tanggal"] == tanggal
        and item["status"] == "aktif"
    }
    return {
        "dokter": dokter["id"],
        "tanggal": tanggal,
        "hari": hari,
        "slot_kosong": [jam for jam in semua_slot if jam not in terisi],
    }

