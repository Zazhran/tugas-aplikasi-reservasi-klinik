# Reservasi Klinik (booking dokter & antrian) — aplikasi MONOLITIK: semua kode ada di satu file ini.
# Tugas mahasiswa: pecah menjadi modul tanpa mengubah perilakunya (lihat README.md).
from flask import Flask, request, jsonify, render_template_string
import json, os, datetime
from repositori.json_repo import baca_data, simpan_data

app = Flask(__name__)
DATA = {}

STYLE = "<style>body{font-family:Verdana,sans-serif;margin:30px;background:#f4fbfb} .kartu{background:white;border-left:5px solid #1a8f8f;padding:10px 16px;margin:10px 0} a{margin-right:12px}</style>"
MENU = "<p><a href='/'>Dokter</a><a href='/reservasi'>Buat Reservasi</a><a href='/rekap'>Rekap Harian</a></p>"


def baca():
    global DATA
    DATA = baca_data()


def tulis():
    simpan_data(DATA)


@app.route("/")
def index():
    baca()
    poli = request.args.get("poli", "")
    html = "<html><head><title>Klinik Sehat</title>" + STYLE + "</head><body>" + MENU + "<h1>Dokter Kami</h1>"
    html += "<form>Poli: <select name='poli'><option value=''>semua</option>"
    for p in sorted(set(d["poli"] for d in DATA["dokter"])):
        html += "<option" + (" selected" if p == poli else "") + ">" + p + "</option>"
    html += "</select><button>Filter</button></form>"
    for d in DATA["dokter"]:
        if poli and d["poli"] != poli:
            continue
        jadwal = ", ".join(h.capitalize() + " " + j[0] + "–" + j[1] for h, j in d["jadwal"].items())
        html += "<div class='kartu'><b>" + d["nama"] + "</b> (" + d["id"] + ")<br>Poli " + d["poli"] + " · Tarif Rp " + "{:,}".format(d["tarif"]).replace(",", ".") + "<br><small>" + jadwal + "</small></div>"
    return html + "</body></html>"


@app.route("/reservasi", methods=["GET", "POST"])
def reservasi():
    baca()
    pesan = ""
    if request.method == "POST":
        no_rm = request.form.get("no_rm", "").strip().upper()
        id_dokter = request.form.get("dokter", "").strip().upper()
        tanggal = request.form.get("tanggal", "")
        jam = request.form.get("jam", "")
        pasien = None
        for p in DATA["pasien"]:
            if p["no_rm"] == no_rm:
                pasien = p
        dokter = None
        for d in DATA["dokter"]:
            if d["id"] == id_dokter:
                dokter = d
        if pasien is None:
            pesan = "No. rekam medis tidak terdaftar"
        elif dokter is None:
            pesan = "Dokter tidak ditemukan"
        else:
            try:
                tgl = datetime.date.fromisoformat(tanggal)
            except ValueError:
                tgl = None
            if tgl is None:
                pesan = "Tanggal tidak valid"
            else:
                hari = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"][tgl.weekday()]
                if hari not in dokter["jadwal"]:
                    pesan = dokter["nama"] + " tidak praktik hari " + hari
                else:
                    mulai = datetime.datetime.strptime(dokter["jadwal"][hari][0], "%H:%M")
                    selesai = datetime.datetime.strptime(dokter["jadwal"][hari][1], "%H:%M")
                    slot = []
                    while mulai < selesai:
                        slot.append(mulai.strftime("%H:%M"))
                        mulai += datetime.timedelta(minutes=20)
                    terisi = [r["jam"] for r in DATA["reservasi"] if r["dokter"] == id_dokter and r["tanggal"] == tanggal and r["status"] == "aktif"]
                    if jam not in slot:
                        pesan = "Jam " + jam + " di luar jadwal praktik"
                    elif jam in terisi:
                        pesan = "Jam " + jam + " sudah terisi"
                    else:
                        lahir = datetime.date.fromisoformat(pasien["tgl_lahir"])
                        umur = tgl.year - lahir.year - ((tgl.month, tgl.day) < (lahir.month, lahir.day))
                        if pasien["bpjs"]:
                            biaya = 0
                        else:
                            biaya = dokter["tarif"]
                            if umur >= 60:
                                biaya = biaya - biaya * 20 // 100
                            biaya = biaya + 5000
                        antrian = len([r for r in DATA["reservasi"] if r["dokter"] == id_dokter and r["tanggal"] == tanggal]) + 1
                        kode = "RSV-" + id_dokter + "-" + tanggal.replace("-", "") + "-" + str(antrian).zfill(2)
                        DATA["reservasi"].append({"kode": kode, "no_rm": no_rm, "dokter": id_dokter, "tanggal": tanggal, "jam": jam, "antrian": antrian, "biaya": biaya, "status": "aktif"})
                        tulis()
                        pesan = "Reservasi berhasil: " + kode + " · antrian " + str(antrian) + " · biaya Rp " + "{:,}".format(biaya).replace(",", ".")
    html = "<html><head><title>Reservasi</title>" + STYLE + "</head><body>" + MENU + "<h1>Buat Reservasi</h1>"
    html += "<p><b>{{ pesan }}</b></p><form method='post'>No. RM <input name='no_rm'> Dokter <select name='dokter'>"
    for d in DATA["dokter"]:
        html += "<option value='" + d["id"] + "'>" + d["nama"] + " (" + d["poli"] + ")</option>"
    html += "</select> Tanggal <input type='date' name='tanggal'> Jam <input name='jam' placeholder='08:20'> <button>Pesan</button></form></body></html>"
    return render_template_string(html, pesan=pesan)


@app.route("/rekap")
def rekap():
    baca()
    tanggal = request.args.get("tanggal", datetime.date.today().isoformat())
    per_poli = {}
    for r in DATA["reservasi"]:
        if r["tanggal"] == tanggal and r["status"] == "aktif":
            poli = [d["poli"] for d in DATA["dokter"] if d["id"] == r["dokter"]][0]
            if poli not in per_poli:
                per_poli[poli] = {"pasien": 0, "pendapatan": 0}
            per_poli[poli]["pasien"] += 1
            per_poli[poli]["pendapatan"] += r["biaya"]
    html = "<html><head><title>Rekap</title>" + STYLE + "</head><body>" + MENU + "<h1>Rekap " + tanggal + "</h1>"
    html += "<form><input type='date' name='tanggal' value='" + tanggal + "'><button>Lihat</button></form>"
    for poli, v in per_poli.items():
        html += "<div class='kartu'>Poli " + poli + ": " + str(v["pasien"]) + " pasien · Rp " + "{:,}".format(v["pendapatan"]).replace(",", ".") + "</div>"
    if not per_poli:
        html += "<p>Belum ada reservasi.</p>"
    return html + "</body></html>"


# ---------------- API JSON ----------------

@app.route("/api/dokter")
def api_dokter():
    baca()
    poli = request.args.get("poli")
    return jsonify([d for d in DATA["dokter"] if not poli or d["poli"] == poli])


@app.route("/api/slot")
def api_slot():
    baca()
    id_dokter = request.args.get("dokter", "").upper()
    tanggal = request.args.get("tanggal", "")
    dokter = None
    for d in DATA["dokter"]:
        if d["id"] == id_dokter:
            dokter = d
    if dokter is None:
        return jsonify({"error": "Dokter tidak ditemukan"}), 404
    tgl = datetime.date.fromisoformat(tanggal)
    hari = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"][tgl.weekday()]
    if hari not in dokter["jadwal"]:
        return jsonify({"dokter": id_dokter, "tanggal": tanggal, "hari": hari, "slot_kosong": []})
    mulai = datetime.datetime.strptime(dokter["jadwal"][hari][0], "%H:%M")
    selesai = datetime.datetime.strptime(dokter["jadwal"][hari][1], "%H:%M")
    terisi = [r["jam"] for r in DATA["reservasi"] if r["dokter"] == id_dokter and r["tanggal"] == tanggal and r["status"] == "aktif"]
    kosong = []
    while mulai < selesai:
        if mulai.strftime("%H:%M") not in terisi:
            kosong.append(mulai.strftime("%H:%M"))
        mulai += datetime.timedelta(minutes=20)
    return jsonify({"dokter": id_dokter, "tanggal": tanggal, "hari": hari, "slot_kosong": kosong})


@app.route("/api/reservasi", methods=["POST"])
def api_reservasi():
    baca()
    b = request.get_json(silent=True) or {}
    no_rm = str(b.get("no_rm", "")).upper()
    id_dokter = str(b.get("dokter", "")).upper()
    tanggal = b.get("tanggal", "")
    jam = b.get("jam", "")
    pasien = next((p for p in DATA["pasien"] if p["no_rm"] == no_rm), None)
    dokter = next((d for d in DATA["dokter"] if d["id"] == id_dokter), None)
    if pasien is None:
        return jsonify({"error": "No. rekam medis tidak terdaftar"}), 404
    if dokter is None:
        return jsonify({"error": "Dokter tidak ditemukan"}), 404
    try:
        tgl = datetime.date.fromisoformat(tanggal)
    except (ValueError, TypeError):
        return jsonify({"error": "Tanggal tidak valid"}), 400
    hari = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"][tgl.weekday()]
    if hari not in dokter["jadwal"]:
        return jsonify({"error": dokter["nama"] + " tidak praktik hari " + hari}), 400
    mulai = datetime.datetime.strptime(dokter["jadwal"][hari][0], "%H:%M")
    selesai = datetime.datetime.strptime(dokter["jadwal"][hari][1], "%H:%M")
    slot = []
    while mulai < selesai:
        slot.append(mulai.strftime("%H:%M"))
        mulai += datetime.timedelta(minutes=20)
    if jam not in slot:
        return jsonify({"error": "Jam " + str(jam) + " di luar jadwal praktik"}), 400
    for r in DATA["reservasi"]:
        if r["dokter"] == id_dokter and r["tanggal"] == tanggal and r["status"] == "aktif":
            if r["jam"] == jam:
                return jsonify({"error": "Jam " + jam + " sudah terisi"}), 409
            if r["no_rm"] == no_rm:
                return jsonify({"error": "Pasien sudah punya reservasi dengan dokter ini pada tanggal tersebut"}), 409
    lahir = datetime.date.fromisoformat(pasien["tgl_lahir"])
    umur = tgl.year - lahir.year - ((tgl.month, tgl.day) < (lahir.month, lahir.day))
    biaya = 0
    if not pasien["bpjs"]:
        biaya = dokter["tarif"]
        if umur >= 60:
            biaya = biaya - biaya * 20 // 100
        biaya += 5000
    antrian = len([r for r in DATA["reservasi"] if r["dokter"] == id_dokter and r["tanggal"] == tanggal]) + 1
    baru = {"kode": "RSV-" + id_dokter + "-" + tanggal.replace("-", "") + "-" + str(antrian).zfill(2), "no_rm": no_rm, "dokter": id_dokter,
            "tanggal": tanggal, "jam": jam, "antrian": antrian, "biaya": biaya, "status": "aktif"}
    DATA["reservasi"].append(baru)
    tulis()
    return jsonify(dict(baru, umur=umur)), 201


@app.route("/api/batal", methods=["POST"])
def api_batal():
    baca()
    b = request.get_json(silent=True) or {}
    hari_ini = b.get("hari_ini") or datetime.date.today().isoformat()
    for r in DATA["reservasi"]:
        if r["kode"] == b.get("kode"):
            if r["status"] != "aktif":
                return jsonify({"error": "Reservasi sudah dibatalkan"}), 400
            if r["tanggal"] <= hari_ini:
                return jsonify({"error": "Pembatalan paling lambat H-1"}), 400
            r["status"] = "batal"
            tulis()
            return jsonify({"kode": r["kode"], "status": "batal"})
    return jsonify({"error": "Kode reservasi tidak ditemukan"}), 404


@app.route("/api/rekap")
def api_rekap():
    baca()
    tanggal = request.args.get("tanggal", datetime.date.today().isoformat())
    per_poli = {}
    for r in DATA["reservasi"]:
        if r["tanggal"] == tanggal and r["status"] == "aktif":
            poli = [d["poli"] for d in DATA["dokter"] if d["id"] == r["dokter"]][0]
            per_poli.setdefault(poli, {"pasien": 0, "pendapatan": 0})
            per_poli[poli]["pasien"] += 1
            per_poli[poli]["pendapatan"] += r["biaya"]
    return jsonify({"tanggal": tanggal, "per_poli": per_poli})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
