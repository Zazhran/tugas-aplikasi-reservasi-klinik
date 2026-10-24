# Reservasi Klinik

**Tipe aplikasi:** Booking / penjadwalan · **Port:** http://localhost:5003

Pemesanan jadwal dokter: daftar dokter per poli, slot praktik, reservasi dengan nomor antrian dan biaya, pembatalan, rekap harian.

> ⚠️ Aplikasi ini **sengaja dibuat monolitik**: seluruh kode (akses data JSON, aturan bisnis, validasi, HTML, dan API) bercampur di satu file `app.py`. Tugas Anda adalah memecahnya menjadi modul **tanpa mengubah perilakunya**. Panduan lengkap: [`../README.md`](../README.md).

## Menjalankan

Aplikasi ini punya `docker-compose.yml` sendiri. Jalankan dari **folder ini**:

```bash
docker compose up --build
# buka http://localhost:5003
```

Tanpa Docker: `pip install -r requirements.txt`, lalu `python app.py` (port 5000).

## Cek Cepat Sebelum & Sesudah Dimodularisasi

Jalankan perintah berikut **sebelum** mengubah kode, catat hasilnya, lalu ulangi **sesudah** modularisasi. Hasilnya harus sama.

```bash
curl -s 'localhost:5003/api/slot?dokter=D01&tanggal=2026-10-26'
```
Hasil: hari `senin`, 11 slot kosong dimulai `08:20`

```bash
curl -s -X POST localhost:5003/api/reservasi -H 'Content-Type: application/json' \
  -d '{"no_rm":"RM0004","dokter":"D01","tanggal":"2026-10-26","jam":"10:00"}'
```
Hasil: `umur` 60, `biaya` 65000, `antrian` 3

Data contoh ikut berubah setiap ada transaksi. Kembalikan dengan `git checkout -- data.json` sebelum mengecek ulang.

## Aturan Bisnis

Semua aturan ini saat ini tertulis **langsung di dalam fungsi route** (sebagian tertulis lebih dari sekali).

1. Nama hari (senin … minggu) ditentukan dari tanggal; dokter hanya bisa dipesan pada hari praktiknya
2. Jadwal praktik dibagi menjadi **slot 20 menit**; slot terisi hanya dihitung dari reservasi berstatus aktif
3. Satu pasien hanya boleh punya satu reservasi aktif per dokter per tanggal
4. Umur pasien dihitung pada tanggal kunjungan
5. Biaya: pasien **BPJS gratis**; non-BPJS = tarif dokter, **lansia (≥ 60 th) diskon 20%**, ditambah **admin Rp 5.000**
6. Nomor antrian = jumlah reservasi dokter pada tanggal itu + 1
7. Kode reservasi `RSV-<dokter>-<YYYYMMDD>-<antrian>`
8. Pembatalan paling lambat **H-1**
9. Rekap harian per poli: jumlah pasien dan pendapatan

## Daftar Route

| Method | URL | Keterangan |
|--------|-----|------------|
| GET | `/?poli=` | Daftar dokter |
| GET, POST | `/reservasi` | Form reservasi |
| GET | `/rekap?tanggal=` | Rekap harian |
| GET | `/api/dokter?poli=` | Daftar dokter (JSON) |
| GET | `/api/slot?dokter=&tanggal=` | Slot kosong |
| POST | `/api/reservasi` | `{no_rm, dokter, tanggal, jam}` |
| POST | `/api/batal` | `{kode, hari_ini?}` |
| GET | `/api/rekap?tanggal=` | Rekap per poli (JSON) |

## File

| File | Isi |
|------|-----|
| `app.py` | Factory Flask dan registrasi blueprint |
| `data.json` | Data contoh (berubah setiap ada transaksi) |
| `Dockerfile`, `requirements.txt` | Image Python 3.12 + Flask |
| `docker-compose.yml` | Menjalankan aplikasi ini di port 5003; folder di-mount ke container sehingga perubahan kode langsung terbaca |

## Hasil Modularisasi

Struktur aplikasi setelah pemecahan:

```text
app.py
config.py
repositori/json_repo.py
layanan/jadwal.py
layanan/reservasi.py
rute/web.py
rute/api.py
templates/
utils/format.py
```

Arah ketergantungan dibuat satu arah: `rute -> layanan -> repositori`, sedangkan
template dipakai oleh route web dan konstanta aturan bisnis disimpan di `config.py`.
Dengan begitu, route hanya menangani HTTP, layanan tidak bergantung pada Flask,
dan detail penyimpanan JSON tersembunyi di `JsonRepository`.

Peta pemecahan aturan bisnis:

| Blok monolitik | Fungsi baru | Modul |
|---|---|---|
| Menentukan nama hari dari tanggal | `hari_dari_tanggal` | `layanan/jadwal.py` |
| Membuat slot 20 menit | `buat_slot` | `layanan/jadwal.py` |
| Mengambil slot yang belum terisi | `slot_kosong` | `layanan/jadwal.py` |
| Mencari pasien dan dokter | `cari_pasien`, `cari_dokter` | `layanan/reservasi.py` |
| Menghitung umur kunjungan | `hitung_umur` | `layanan/reservasi.py` |
| Menghitung biaya pasien | `hitung_biaya` | `layanan/reservasi.py` |
| Menentukan nomor antrean dan kode | `hitung_antrian`, `buat_kode` | `layanan/reservasi.py` |
| Membuat reservasi | `buat_reservasi` | `layanan/reservasi.py` |
| Membatalkan reservasi | `batalkan_reservasi` | `layanan/reservasi.py` |
| Membuat rekap per poli | `rekap_harian` | `layanan/reservasi.py` |

Web dan API memakai layanan yang sama. Perbedaan lama tetap dipertahankan:
API menolak reservasi ganda pasien pada dokter dan tanggal yang sama, sedangkan
route web lama tidak melakukan pemeriksaan tersebut.
