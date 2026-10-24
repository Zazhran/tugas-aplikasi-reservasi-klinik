from datetime import date

from flask import Blueprint, render_template, request

from layanan import (
    ReservasiError,
    buat_reservasi,
    daftar_dokter,
    rekap_harian,
)
from utils import format_rupiah


web = Blueprint("web", __name__)


def _data(repo):
    return repo.ambil_semua()


@web.get("/")
def index():
    data = _data(web.repo)
    poli = request.args.get("poli", "")
    dokter = daftar_dokter(data, poli)
    semua_poli = sorted({item["poli"] for item in data["dokter"]})
    return render_template(
        "index.html",
        dokter=dokter,
        poli=poli,
        semua_poli=semua_poli,
    )


@web.route("/reservasi", methods=["GET", "POST"])
def reservasi():
    data = _data(web.repo)
    pesan = ""
    if request.method == "POST":
        no_rm = request.form.get("no_rm", "").strip().upper()
        id_dokter = request.form.get("dokter", "").strip().upper()
        tanggal = request.form.get("tanggal", "")
        jam = request.form.get("jam", "")
        try:
            baru, _ = buat_reservasi(
                web.repo,
                no_rm,
                id_dokter,
                tanggal,
                jam,
                # Perilaku web lama tidak memeriksa pasien ganda.
                tolak_pasien_ganda=False,
            )
            pesan = (
                f"Reservasi berhasil: {baru['kode']} ﾂｷ antrian {baru['antrian']} ﾂｷ "
                f"biaya Rp {format_rupiah(baru['biaya'])}"
            )
        except ReservasiError as error:
            pesan = error.pesan
        data = _data(web.repo)
    return render_template("reservasi.html", dokter=data["dokter"], pesan=pesan)


@web.get("/rekap")
def rekap():
    tanggal = request.args.get("tanggal", date.today().isoformat())
    data = _data(web.repo)
    per_poli = rekap_harian(data, tanggal)
    return render_template("rekap.html", tanggal=tanggal, per_poli=per_poli)
