# 📱 CEK HARDWARE ANDROID v3.0

> **Script Python untuk mengecek hardware Android — tanpa root, tanpa library eksternal**
> Support Android 10, 11, 12, 13, 14+ termasuk HP Oppo, Samsung, Xiaomi, Vivo, dll.

[![Python](https://img.shields.io/badge/Python-3.6%2B-blue?logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Termux-green?logo=android)](https://termux.dev)
[![Dependency](https://img.shields.io/badge/Dependency-Zero-brightgreen)](.)
[![Root](https://img.shields.io/badge/Root-Tidak%20Perlu-orange)](.)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## ✨ 18 Fitur Lengkap

| No | Ikon | Fitur | Data yang Ditampilkan |
|----|------|-------|----------------------|
| 1 | 🖥️ | **Info CPU** | Model, core, frekuensi per-core, governor, load average, usage real-time |
| 2 | 💾 | **Info RAM** | Total, terpakai, tersedia, buffer, cache, swap, zRAM ratio |
| 3 | 💿 | **Info Storage** | Semua partisi, persentase, df -h output |
| 4 | 🔋 | **Info Baterai** | Persentase, voltage, arus, health, siklus charge, suhu |
| 5 | 🌡️ | **Suhu Hardware** | Semua thermal zone + suhu baterai |
| 6 | 🌐 | **Info Jaringan** | IP, statistik RX/TX, latensi TCP |
| 7 | 📱 | **Info Sistem & OS** | Brand, model, Android version, SDK, build info via getprop |
| 8 | ⚙️ | **Proses Aktif** | Top proses via `top`/`ps` — compatible Android 10+ |
| 9 | 📡 | **Kecepatan Jaringan** | Download/upload real-time + speed test Cloudflare |
| 10 | ⚡ | **Benchmark CPU** | 4 tes: π, float ops, multi-thread, memori bandwidth |
| 11 | 📊 | **Monitor Real-time** | CPU%, RAM%, suhu, net speed live setiap 1 detik |
| 12 | 📋 | **Laporan Lengkap** | Export JSON + TXT semua data hardware |
| 13 | 🎮 | **Info GPU** | Identifikasi via getprop + devfreq (Adreno/Mali) |
| 14 | 📶 | **WiFi Detail** | Interface, IP, statistik, DNS, getprop WiFi |
| 15 | 🔧 | **Kernel & Sistem** | Versi kernel, parameter /proc/sys, SELinux |
| 16 | 🧮 | **Virtual Memory Stats** | Page fault, swap I/O, OOM kill, activity rate/s |
| 17 | 🧭 | **Sensor Hardware** | dumpsys sensorservice, IIO, input devices |
| 18 | 🤖 | **Android Lanjut** | pm packages, wm display, settings, getprop++ |

---

## 🚀 Cara Instalasi (Termux di Android)

### Langkah 1 — Install Termux
```
Download dari F-Droid (BUKAN dari Play Store — versi Play Store sudah tidak diupdate):
https://f-droid.org/packages/com.termux/
```

### Langkah 2 — Buka Termux, update paket
```bash
pkg update && pkg upgrade -y
```

### Langkah 3 — Install Python
```bash
pkg install python -y
```

### Langkah 4 — Download script

**Cara A — Clone dari GitHub (direkomendasikan):**
```bash
pkg install git -y
git clone https://github.com/yanzzhshdb/Scan-hardware
```

**Cara B — Download file langsung:**
```bash
curl -O https://raw.githubusercontent.com/USERNAME/cek-hardware-android/main/cek_hardware_android.py
```

**Cara C — Copy dari penyimpanan HP:**
```bash
# Salin file ke folder Downloads HP, lalu di Termux:
cp /sdcard/Download/cek_hardware_android.py ~/
cd ~
```

### Langkah 5 — Jalankan
```bash
python3 cek_hardware_android.py
```

Selesai! Tidak perlu `pip install` apapun.

---

## 🎮 Cara Pakai

Setelah dijalankan akan muncul menu:

```
════════════════════════════════════════════════════════════════════
   CEK HARDWARE ANDROID v3.0  ·  ZERO DEPENDENCY
   Support Android 10+ · Tanpa root · Tanpa psutil
════════════════════════════════════════════════════════════════════
  1  🖥️  Info CPU ...
  2  💾  Info RAM ...
  ...
 18  🤖  Android Lanjut ...

    0  🚀 Jalankan Semua 18 Fitur
    q  ❌ Keluar
────────────────────────────────────────────────────────────────────
  Pilih [1-18 / 0=semua / q=keluar]:
```

| Input | Aksi |
|-------|------|
| `1` hingga `18` | Jalankan fitur tertentu |
| `0` | Jalankan semua 18 fitur sekaligus |
| `q` atau `keluar` | Keluar dari program |
| `Ctrl+C` | Stop fitur yang sedang jalan |

---

## 📤 Export Laporan (Fitur 12)

Pilih `12` untuk export otomatis:

| Format | Nama File | Isi |
|--------|-----------|-----|
| **JSON** | `laporan_YYYYMMDD_HHMMSS.json` | Data lengkap terstruktur |
| **TXT** | `laporan_YYYYMMDD_HHMMSS.txt` | Ringkasan siap dibaca |

File disimpan di folder saat script dijalankan (biasanya `~/`).

---

## 🛡️ Kompatibilitas Android 10+

Script ini dirancang untuk menangani **pembatasan keamanan Android 10+** secara elegan:

| Path / Fitur | Android < 10 | Android 10+ | Solusi v3.0 |
|---|:---:|:---:|---|
| `/proc/net/dev` (traffic) | ✅ | ❌ Blocked | Gunakan `/sys/class/net/*/statistics/` |
| `/proc/net/wireless` (WiFi) | ✅ | ❌ Blocked | Gunakan `getprop` + `dumpsys wifi` |
| `/proc/[pid]/*` (proses lain) | ✅ | ❌ Blocked | Gunakan `top` / `ps` |
| `/proc/modules` (kernel) | ✅ | ❌ Blocked | Tampilkan pesan informatif |
| MAC Address | ✅ Real | ❌ Randomized | Deteksi dan beri label "(privasi)" |
| `/sys/class/kgsl/` (GPU) | Parsial | ❌ Blocked | Identifikasi via `getprop` + devfreq |
| `/sys/bus/iio/` (sensor) | Parsial | ❌ Blocked | Gunakan `dumpsys sensorservice` |
| `/proc/cpuinfo` | ✅ | ✅ | Tetap digunakan |
| `/proc/meminfo` | ✅ | ✅ | Tetap digunakan |
| `/proc/stat` (CPU%) | ✅ | ✅ | Tetap digunakan |
| `/sys/class/thermal/` (suhu) | ✅ | ✅ Parsial | Dengan fallback graceful |
| `/sys/class/power_supply/` | ✅ | ✅ Parsial | Dengan fallback ke `dumpsys` |
| `getprop` | ✅ | ✅ | Digunakan secara luas |

> **Prinsip v3.0:** Setiap path dicoba dulu. Jika blocked → coba alternatif → jika tidak ada → tampilkan pesan jelas, **tidak pernah crash**.

---

## ⚙️ Sumber Data (Zero Dependency)

Tidak ada library eksternal. Semua dari built-in Python + sistem file Android:

| Sumber | Data |
|--------|------|
| `/proc/cpuinfo` | Model CPU, core, ABI |
| `/proc/stat` | CPU usage real-time |
| `/proc/meminfo` | RAM, swap, buffer, cache |
| `/proc/mounts` | Daftar partisi |
| `/proc/uptime` | Uptime sistem |
| `/proc/vmstat` | Page fault, swap I/O, OOM |
| `/proc/version` | Versi kernel |
| `/sys/class/net/*/statistics/` | Traffic jaringan (RX/TX) ← pengganti `/proc/net/dev` |
| `/sys/class/thermal/*/temp` | Suhu semua zone |
| `/sys/class/power_supply/*` | Data baterai |
| `/sys/class/devfreq/` | Frekuensi GPU/DSP |
| `/sys/devices/system/cpu/*/cpufreq/` | Frekuensi CPU per-core |
| `/sys/block/zram*/mm_stat` | Info kompresi zRAM |
| `getprop` | Semua Android properties (brand, model, OS, dll) |
| `dumpsys battery` | Info baterai via Android service |
| `dumpsys wifi` | Koneksi WiFi aktif |
| `dumpsys sensorservice` | Daftar sensor hardware |
| `pm list packages` | Daftar aplikasi terinstall |
| `wm size/density` | Resolusi dan density layar |
| `top` / `ps` | Proses aktif |
| `df -h` | Info storage |

---

## 🧩 Struktur File

```
cek-hardware-android/
├── cek_hardware_android.py    # Script utama — 18 fitur, v3.0
├── requirements_android.txt   # Kosong (zero dependency)
└── README.md                  # Dokumentasi ini
```

---

## 🛠️ Troubleshooting

**❓ "Permission denied" di banyak tempat**
```
Normal di Android 10+! Script sudah dirancang untuk ini.
Fitur tetap berjalan dengan data yang tersedia.
Tidak perlu root untuk fitur-fitur utama.
```

**❓ Python tidak ditemukan**
```bash
pkg install python -y
```

**❓ Warna tidak muncul di terminal**
```bash
# Test terminal support ANSI:
echo -e "\033[92mHijau\033[0m"
# Gunakan Termux (bukan JuiceSSH untuk koneksi lokal)
```

**❓ Fitur 8 (Proses) tidak tampil proses sistem**
```
Normal di Android 10+. Hanya proses milik Termux yang bisa dilihat.
Script menggunakan top/ps sebagai alternatif.
```

**❓ Fitur 13 (GPU) tidak tampil detail**
```
GPU detail membutuhkan root di Android 10+.
Script menampilkan identifikasi GPU dari SoC (getprop) sebagai alternatif.
```

**❓ Fitur 17 (Sensor) kosong**
```bash
# Coba jalankan dumpsys manual:
dumpsys sensorservice | head -50
# Jika kosong, sensor membutuhkan akses yang lebih tinggi.
```

**❓ dumpsys tidak bisa diakses**
```
Di Termux tanpa Shizuku/ADB, beberapa dumpsys sub-command terbatas.
Cara bypass: gunakan Shizuku app + Termux permission.
```

---

## 📋 Changelog

### v3.0 — Android 10+ Full Support (Terbaru)
- ✅ **Rewrite total** untuk compatibility Android 10, 11, 12, 13, 14+
- ✅ **Network stats**: ganti `/proc/net/dev` → `/sys/class/net/*/statistics/` (tidak blocked)
- ✅ **Proses**: ganti direct `/proc/<pid>` → `top`/`ps` (Android 10+ compatible)
- ✅ **GPU**: gunakan `getprop` + devfreq sebagai alternatif kgsl
- ✅ **WiFi**: fokus pada `getprop` + `dumpsys wifi` + `/sys/class/net/wlan*/`
- ✅ **Sensor**: gunakan `dumpsys sensorservice` sebagai sumber utama
- ✅ **MAC address**: deteksi randomisasi Android 10+, beri label informatif
- ✅ **Zero crash**: setiap path/command dibungkus try/except + pesan alternatif
- ✅ **Monitor (Fitur 11)**: tambah kolom suhu real-time
- ✅ **Storage**: tambah fallback `df -h`
- ✅ **zRAM**: tampilkan rasio kompresi

### v2.0
- ✅ 18 fitur (dari 12)
- ✅ GPU, WiFi, Kernel, vmstat, Sensor IIO, Android Lanjut

### v1.0
- ✅ 12 fitur dasar, zero dependency, zero psutil

---

## 🤝 Kontribusi

1. Fork repository
2. Buat branch: `git checkout -b fitur-baru`
3. Commit: `git commit -m "Tambah fitur X"`
4. Push: `git push origin fitur-baru`
5. Buat Pull Request

---

## 📄 Lisensi

MIT License — bebas digunakan, dimodifikasi, dan didistribusikan.

---

<div align="center">
  <b>Dibuat untuk komunitas Android Indonesia 🇮🇩</b><br>
  <i>v3.0 · Zero dependency · Zero root · Tanpa psutil · Support Android 10+</i>
</div>
