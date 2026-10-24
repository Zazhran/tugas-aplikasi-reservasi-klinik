import datetime
from config import BIAYA_ADMIN  # Pastikan config.py nanti menyediakan BIAYA_ADMIN = 5000

def hitung_umur(tgl_lahir_str, tgl_reservasi_str):
    """Menghitung umur pasien berdasarkan tanggal lahir dan tanggal reservasi"""
    tgl_lahir = datetime.date.fromisoformat(tgl_lahir_str)
    tgl_reservasi = datetime.date.fromisoformat(tgl_reservasi_str)
    
    umur = tgl_reservasi.year - tgl_lahir.year - ((tgl_reservasi.month, tgl_reservasi.day) < (tgl_lahir.month, tgl_lahir.day))
    return umur

def generate_slot_praktik(jam_mulai_str, jam_selesai_str):
    """Menghasilkan daftar slot waktu praktik dokter berdasarkan interval 20 menit"""
    mulai = datetime.datetime.strptime(jam_mulai_str, "%H:%M")
    selesai = datetime.datetime.strptime(jam_selesai_str, "%H:%M")
    slot = []
    while mulai < selesai:
        slot.append(mulai.strftime("%H:%M"))
        mulai += datetime.timedelta(minutes=20)
    return slot

def hitung_biaya_dan_aturan(pasien, dokter, umur):
    """Menghitung biaya berdasarkan status BPJS, tarif dokter, umur, dan biaya admin"""
    if pasien.get("bpjs", False):
        return 0
    
    biaya = dokter["tarif"]
    if umur >= 60:
        # Diskon lansia 20%
        biaya = biaya - (biaya * 20 // 100)
    
    biaya += BIAYA_ADMIN
    return biaya

def proses_buat_reservasi(semua_reservasi, pasien, dokter, tanggal, jam):
    """
    Fungsi utama murni untuk memvalidasi dan memproses reservasi baru.
    Mengembalikan dictionary data reservasi baru atau tuple (None, pesan_error).
    """
    # 1. Validasi tanggal
    try:
        tgl = datetime.date.fromisoformat(tanggal)
    except (ValueError, TypeError):
        return None, "Tanggal tidak valid"
    
    # 2. Cek hari praktik dokter
    daftar_hari = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]
    hari = daftar_hari[tgl.weekday()]
    
    if hari not in dokter["jadwal"]:
        return None, f"{dokter['nama']} tidak praktik hari {hari}"
    
    # 3. Cek validitas jam slot
    jam_praktik = dokter["jadwal"][hari]
    slot_tersedia = generate_slot_praktik(jam_praktik[0], jam_praktik[1])
    
    if jam not in slot_tersedia:
        return None, f"Jam {jam} di luar jadwal praktik"
    
    # 4. Cek apakah jam sudah terisi atau pasien sudah reservasi di tanggal/dokter yang sama
    for r in semua_reservasi:
        if r["dokter"] == dokter["id"] and r["tanggal"] == tanggal and r["status"] == "aktif":
            if r["jam"] == jam:
                return None, f"Jam {jam} sudah terisi"
            if r["no_rm"] == pasien["no_rm"]:
                return None, "Pasien sudah punya reservasi dengan dokter ini pada tanggal tersebut"
                
    # 5. Hitung umur & biaya
    umur = hitung_umur(pasien["tgl_lahir"], tanggal)
    biaya = hitung_biaya_dan_aturan(pasien, dokter, umur)
    
    # 6. Hitung nomor antrean
    antrian = len([r for r in semua_reservasi if r["dokter"] == dokter["id"] and r["tanggal"] == tanggal]) + 1
    
    # 7. Buat kode reservasi unik
    tgl_str_formatted = tanggal.replace("-", "")
    kode = f"RSV-{dokter['id']}-{tgl_str_formatted}-{str(antrian).zfill(2)}"
    
    # 8. Susun data hasil reservasi
    reservasi_baru = {
        "kode": kode,
        "no_rm": pasien["no_rm"],
        "dokter": dokter["id"],
        "tanggal": tanggal,
        "jam": jam,
        "antrian": antrian,
        "biaya": biaya,
        "status": "aktif"
    }
    
    return reservasi_baru, umur