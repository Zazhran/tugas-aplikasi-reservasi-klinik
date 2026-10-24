from datetime import date

from flask import Blueprint, jsonify, request

from layanan import (
    ReservasiError,
    batalkan_reservasi,
    buat_reservasi,
    cari_dokter,
    daftar_dokter,
    rekap_harian,
    slot_kosong,
)


api = Blueprint("api", __name__, url_prefix="/api")


@api.get("/dokter")
def api_dokter():
    data = api.repo.ambil_semua()
    return jsonify(daftar_dokter(data, request.args.get("poli")))


@api.get("/slot")
def api_slot():
    data = api.repo.ambil_semua()
    id_dokter = request.args.get("dokter", "").upper()
    tanggal = request.args.get("tanggal", "")
    dokter = cari_dokter(data, id_dokter)
    if dokter is None:
        return jsonify({"error": "Dokter tidak ditemukan"}), 404
    return jsonify(slot_kosong(dokter, tanggal, data["reservasi"]))


@api.post("/reservasi")
def api_reservasi():
    body = request.get_json(silent=True) or {}
    no_rm = str(body.get("no_rm", "")).upper()
    id_dokter = str(body.get("dokter", "")).upper()
    tanggal = body.get("tanggal", "")
    jam = body.get("jam", "")
    try:
        baru, umur = buat_reservasi(
            api.repo,
            no_rm,
            id_dokter,
            tanggal,
            jam,
            tolak_pasien_ganda=True,
        )
    except ReservasiError as error:
        return jsonify({"error": error.pesan}), error.status
    return jsonify(dict(baru, umur=umur)), 201


@api.post("/batal")
def api_batal():
    body = request.get_json(silent=True) or {}
    hari_ini = body.get("hari_ini") or date.today().isoformat()
    try:
        hasil = batalkan_reservasi(api.repo, body.get("kode"), hari_ini)
    except ReservasiError as error:
        return jsonify({"error": error.pesan}), error.status
    return jsonify(hasil)


@api.get("/rekap")
def api_rekap():
    tanggal = request.args.get("tanggal", date.today().isoformat())
    data = api.repo.ambil_semua()
    return jsonify({"tanggal": tanggal, "per_poli": rekap_harian(data, tanggal)})

