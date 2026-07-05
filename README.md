# 📱 CEK HARDWARE ANDROID v2.0

> **Script Python ringan untuk mengecek hardware Android secara lengkap**
> Tanpa library eksternal — baca langsung dari `/proc` & `/sys`

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue?logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Termux-green?logo=android)](https://termux.dev)
[![Dependency](https://img.shields.io/badge/Dependency-Zero-brightgreen)](.)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## ✨ Fitur (18 Fitur Lengkap)

| No | Fitur | Keterangan |
|----|-------|-----------|
| 1 | 🖥️ **Info CPU** | Model, core, frekuensi per-core, governor, BogoMIPS, load avg, usage real-time |
| 2 | 💾 **Info RAM** | Total, terpakai, tersedia, buffer, cache, swap, active/inactive |
| 3 | 💿 **Info Storage** | Semua mount point, I/O diskstats, persentase pemakaian |
| 4 | 🔋 **Info Baterai** | Persentase, voltage, arus, siklus charge, health, suhu baterai |
| 5 | 🌡️ **Suhu Hardware** | Semua thermal zone, hwmon sensor, status kritis/panas/normal |
| 6 | 🌐 **Info Jaringan** | IP lokal/publik, MAC, traffic RX/TX, latensi TCP ke 4 server |
| 7 | 📱 **Info Sistem & OS** | Android version, SDK, build info, uptime, getprop lengkap |
| 8 | ⚙️ **Proses Aktif** | Top 15 proses tertinggi CPU, RAM per proses, status |
| 9 | 📡 **Kecepatan Jaringan** | Download/upload real-time + uji download nyata dari Cloudflare |
| 10 | ⚡ **Benchmark CPU** | 4 tes: π Leibniz, float ops, multi-thread, memori bandwidth |
| 11 | 📊 **Monitor Real-time** | Live chart CPU%, RAM%, net speed setiap 1 detik selama 10 detik |
| 12 | 📋 **Laporan Lengkap** | Export JSON + TXT dengan semua data hardware |
| 13 | 🎮 **Info GPU** ⭐NEW | Adreno (kgsl), Mali, DevFreq, DRM — frekuensi, utilisasi, suhu GPU |
| 14 | 📶 **WiFi Detail** ⭐NEW | Signal level, link quality, iwconfig, iwgetid, Android WiFi props |
| 15 | 🔧 **Kernel & Modul** ⭐NEW | Versi kernel, 25 modul dimuat, kernel params, boot cmdline |
| 16 | 🧮 **Virtual Memory Stats** ⭐NEW | Page fault, swap I/O, OOM kill, context switch, activity rate/s |
| 17 | 🧭 **Sensor IIO** ⭐NEW | Akselerometer, giroskop, magnetometer, proximity, cahaya, suhu |
| 18 | 🤖 **Android Lanjut** ⭐NEW | dumpsys battery/cpu, pm list packages, wm size, settings system |

---

## 🚀 Cara Instalasi & Penggunaan

### Android (Termux) — DIREKOMENDASIKAN

**1. Install Termux**
```
Download dari F-Droid (bukan Play Store):
https://f-droid.org/packages/com.termux/
```

**2. Buka Termux dan update paket**
```bash
pkg update && pkg upgrade -y
```

**3. Install Python**
```bash
pkg install python -y
```

**4. Download script**

Cara A — clone dari GitHub:
```bash
pkg install git -y
git clone https://github.com/yanzzhshdb/Scan-hardware
```

Cara B — download langsung:
```bash
curl -O https://raw.githubusercontent.com/USERNAME/cek-hardware-android/main/cek_hardware_android.py
```

Cara C — copy manual ke Termux:
```bash
# Salin file ke folder Downloads Android, lalu di Termux:
cp /sdcard/Download/cek_hardware_android.py ~/
cd ~
```

**5. Jalankan**
```bash
python3 cek_hardware_android.py
```

---

### Linux / PC (Ubuntu, Debian, Arch, dll)

```bash
# Install Python jika belum ada
sudo apt install python3 -y        # Ubuntu/Debian
# atau
sudo pacman -S python              # Arch

# Jalankan langsung
python3 cek_hardware_android.py
```

---

### Windows (WSL / Git Bash)

```bash
# Di WSL Ubuntu:
python3 cek_hardware_android.py

# Catatan: Beberapa fitur tidak tersedia di Windows
# karena /proc dan /sys hanya ada di Linux/Android
```

---

## 🎮 Cara Pakai

Setelah dijalankan, akan muncul menu interaktif:

```
══════════════════════════════════════════════════════════════════
   CEK HARDWARE — ANDROID v2.0  ·  ZERO DEPENDENCY
   Baca /proc & /sys langsung — tanpa psutil
══════════════════════════════════════════════════════════════════
  1   🖥️   Info CPU ...
  2   💾   Info RAM ...
  ...
 18   🤖   Android Lanjut ...

    0   🚀 Jalankan Semua 18 Fitur
    q   ❌ Keluar
──────────────────────────────────────────────────────────────────
  Pilih [1-18 / 0=semua / q=keluar]:
```

| Input | Aksi |
|-------|------|
| `1` – `18` | Jalankan satu fitur spesifik |
| `0` | Jalankan semua 18 fitur sekaligus |
| `q` | Keluar dari program |
| `Ctrl+C` | Stop fitur yang sedang berjalan / keluar |

---

## 📤 Export Laporan (Fitur 12)

Pilih menu **12** untuk export otomatis ke:

| Format | Nama File | Isi |
|--------|-----------|-----|
| **JSON** | `laporan_YYYYMMDD_HHMMSS.json` | Data terstruktur lengkap (CPU, RAM, storage, baterai, thermal, jaringan) |
| **TXT**  | `laporan_YYYYMMDD_HHMMSS.txt`  | Teks ringkas siap dibaca / dikirim |

File tersimpan di folder saat script dijalankan.

---

## ⚙️ Sumber Data (Zero Dependency)

Script ini **tidak menggunakan library eksternal** apapun. Semua data dibaca langsung dari:

| Sumber | Data yang Dibaca |
|--------|-----------------|
| `/proc/cpuinfo` | Model, core, fitur CPU |
| `/proc/stat` | Penggunaan CPU real-time |
| `/proc/meminfo` | RAM, swap, buffer, cache |
| `/proc/mounts` | Daftar partisi dan mount point |
| `/proc/diskstats` | I/O disk (baca/tulis) |
| `/proc/net/dev` | Traffic jaringan RX/TX |
| `/proc/net/wireless` | Signal WiFi, link quality |
| `/proc/modules` | Modul kernel yang aktif |
| `/proc/vmstat` | Page fault, swap activity, OOM |
| `/proc/cmdline` | Kernel boot arguments |
| `/proc/version` | Versi kernel lengkap |
| `/sys/class/thermal/` | Suhu semua zona thermal |
| `/sys/class/power_supply/` | Info baterai detail |
| `/sys/class/kgsl/` | GPU Adreno (Qualcomm) |
| `/sys/class/devfreq/` | Frekuensi GPU/DSP/Bus |
| `/sys/class/net/wlan*/` | Detail interface WiFi |
| `/sys/bus/iio/devices/` | Sensor IIO (akselerometer, dll) |
| `/sys/class/hwmon/` | Hardware monitor sensor |
| `getprop` | Properties Android system |
| `dumpsys` | System service Android |
| `pm` | Package manager Android |
| `wm` | Window manager (resolusi, density) |
| `iwconfig` / `iw` | Info WiFi lanjut |

---

## 🔐 Permission & Akses Root

Sebagian besar fitur **tidak perlu root**. Tabel berikut menjelaskan kebutuhan akses:

| Fitur | Tanpa Root | Dengan Root | Catatan |
|-------|:----------:|:-----------:|---------|
| 1–9 (CPU, RAM, Storage, dll) | ✅ | ✅ | Berjalan penuh |
| 10 Benchmark | ✅ | ✅ | Pure Python |
| 11 Monitor | ✅ | ✅ | Berjalan penuh |
| 12 Laporan | ✅ | ✅ | Export normal |
| 13 GPU Adreno/Mali | ⚠️ Terbatas | ✅ | Root dapat lebih banyak data |
| 14 WiFi Detail | ✅ | ✅ | `iwconfig` butuh root untuk channel |
| 15 Kernel Modul | ⚠️ Terbatas | ✅ | `/proc/modules` sering dibatasi |
| 16 vmstat | ✅ | ✅ | Berjalan penuh |
| 17 Sensor IIO | ⚠️ Terbatas | ✅ | Bergantung device |
| 18 Android Lanjut | ⚠️ Terbatas | ✅ | dumpsys butuh permission |

---

## 🧩 Struktur File

```
cek-hardware-android/
├── cek_hardware_android.py    # Script utama (v2.0, 18 fitur)
├── requirements_android.txt   # Kosong — zero dependency
└── README.md                  # Dokumentasi ini
```

---

## 📋 Changelog

### v2.0 (Terbaru)
- ✅ **+6 fitur baru**: GPU Info, WiFi Detail, Kernel & Modul, vmstat, Sensor IIO, Android Lanjut
- ✅ Total 18 fitur (sebelumnya 12)
- ✅ Tambah export thermal ke laporan JSON/TXT
- ✅ Perbaikan helper `na()` untuk nilai kosong
- ✅ UI menu diperbarui dengan highlight fitur baru `[NEWv2]`
- ✅ Benchmark CPU: gunakan `_n_cores()` terpusat
- ✅ Fitur 6: tampilkan error count per interface

### v1.0
- ✅ 12 fitur dasar: CPU, RAM, Storage, Baterai, Suhu, Jaringan, OS, Proses, NetSpeed, Benchmark, Monitor, Laporan
- ✅ Zero dependency, baca langsung dari `/proc` dan `/sys`
- ✅ Support Android via `getprop`
- ✅ Export JSON + TXT

---

## 🛠️ Troubleshooting

**Script tidak jalan di Termux?**
```bash
# Pastikan Python sudah terinstall
python3 --version

# Jika belum:
pkg install python -y
```

**Fitur 13 (GPU) tidak tampil data?**
```
Normal — beberapa device menyembunyikan /sys/class/kgsl tanpa root.
Coba jalankan Termux dengan akses root jika device sudah di-root.
```

**Fitur 18 (dumpsys) tidak jalan?**
```
dumpsys butuh akses khusus. Di Termux biasa (non-root), beberapa
sub-command mungkin tidak tersedia. Gunakan Termux + Shizuku
atau ADB over WiFi untuk akses penuh.
```

**Warna tidak tampil di terminal?**
```bash
# Pastikan terminal support warna ANSI
echo -e "\033[92mTest warna\033[0m"
# Jika tidak ada warna, coba terminal lain (JuiceSSH, Termux, dll)
```

**Error `Permission denied` di /sys atau /proc?**
```
Beberapa path membutuhkan root. Fitur akan tetap berjalan
tapi menampilkan "—" untuk data yang tidak bisa diakses.
```

---

## 🤝 Kontribusi

Pull request dan issue sangat welcome!

1. Fork repository ini
2. Buat branch baru: `git checkout -b fitur-baru`
3. Commit perubahan: `git commit -m "Tambah fitur X"`
4. Push: `git push origin fitur-baru`
5. Buat Pull Request

---

## 📄 Lisensi

MIT License — bebas digunakan, dimodifikasi, dan didistribusikan.

---

<div align="center">
  <b>Dibuat dengan ❤️ untuk komunitas Android Indonesia</b><br>
  <i>Zero dependency · Pure Python · Baca langsung dari /proc & /sys</i>
</div>
