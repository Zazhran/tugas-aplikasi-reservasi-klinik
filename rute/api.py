from flask import Blueprint, request, jsonify
from repositori.json_repo import baca_data
from layanan.jadwal import cari_slot_kosong

# Inisialisasi Blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route("/api/slot", methods=["GET"])
def api_slot():
    data = baca_data()
    id_dokter = request.args.get("dokter", "").upper()
    tanggal = request.args.get("tanggal", "")

    hasil = cari_slot_kosong(data["dokter"], data["reservasi"], id_dokter, tanggal)
    return jsonify(hasil)