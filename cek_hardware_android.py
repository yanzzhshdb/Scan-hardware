"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      CEK HARDWARE ANDROID v3.0  —  ZERO DEPENDENCY                          ║
║      Support semua versi Android (termasuk Android 10+, 13, 14)             ║
║      Tanpa root · Tanpa psutil · Tanpa library eksternal                    ║
║      Jalankan : python3 cek_hardware_android.py                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

18 FITUR:
  1  Info CPU          7  Info Sistem & OS    13  Info GPU
  2  Info RAM          8  Proses Aktif        14  WiFi Detail
  3  Info Storage      9  Kecepatan Jaringan  15  Kernel & Sistem
  4  Info Baterai     10  Benchmark CPU       16  Virtual Memory Stats
  5  Suhu Hardware    11  Monitor Real-time   17  Sensor Hardware
  6  Info Jaringan    12  Laporan (JSON+TXT)  18  Android Lanjut
"""

import os, sys, time, socket, subprocess, datetime, json, re, platform
from pathlib import Path

# ─── WARNA ANSI ───────────────────────────────────────────────────────────────
class C:
    RST  = "\033[0m";  BOLD = "\033[1m";  DIM = "\033[2m"
    RED  = "\033[91m"; GRN  = "\033[92m"; YLW = "\033[93m"
    BLU  = "\033[94m"; MAG  = "\033[95m"; CYN = "\033[96m"
    WHT  = "\033[97m"; GRY  = "\033[90m"

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def hdr(title, icon="◉"):
    print(f"\n{C.BOLD}{C.CYN}{'═'*64}{C.RST}")
    print(f"  {icon}  {C.BOLD}{C.WHT}{title}{C.RST}")
    print(f"{C.BOLD}{C.CYN}{'─'*64}{C.RST}")

def row(label, value, w=30):
    print(f"    {C.GRY}{str(label):<{w}}{C.RST}{C.WHT}{value}{C.RST}")

def sec(label):
    print(f"\n    {C.BOLD}{C.YLW}▸ {label}{C.RST}")

def warn(msg):
    print(f"    {C.YLW}⚠  {msg}{C.RST}")

def info(msg):
    print(f"    {C.GRY}ℹ  {msg}{C.RST}")

def ok(msg):
    print(f"    {C.GRN}✓  {msg}{C.RST}")

def bar(pct, width=32):
    pct = max(0.0, min(100.0, float(pct)))
    col = C.RED if pct >= 85 else C.YLW if pct >= 60 else C.GRN
    f   = int(width * pct / 100)
    return f"{col}{'█'*f}{'░'*(width-f)}{C.RST} {pct:5.1f}%"

def b2h(n):
    n = float(n)
    for u in ("B","KB","MB","GB","TB"):
        if abs(n) < 1024: return f"{n:.2f} {u}"
        n /= 1024
    return f"{n:.2f} PB"

def safe_read(path, default=""):
    """Baca file dengan catch semua error (PermissionError, OSError, dll)."""
    try:
        return Path(path).read_text(errors="replace").strip()
    except Exception:
        return default

def run_cmd(cmd, timeout=5, default=""):
    """Jalankan command dengan catch semua error."""
    try:
        return subprocess.check_output(
            cmd, stderr=subprocess.DEVNULL,
            timeout=timeout).decode(errors="replace").strip()
    except Exception:
        return default

def safe_iterdir(path):
    """Iterasi direktori — return [] jika tidak bisa diakses."""
    try:
        return sorted(Path(path).iterdir())
    except Exception:
        return []

def getprop(key, default=""):
    """Baca Android property via getprop."""
    val = run_cmd(["getprop", key], timeout=3)
    return val if val and val not in ("[]","") else default

def safe_int(s, default=0):
    try:    return int(s.strip())
    except: return default

def safe_float(s, default=0.0):
    try:    return float(s.strip())
    except: return default

# ─── DATA SOURCES ─────────────────────────────────────────────────────────────
def _parse_meminfo():
    d = {}
    for ln in safe_read("/proc/meminfo").split("\n"):
        if ":" in ln:
            k, v = ln.split(":", 1)
            nums = re.findall(r"\d+", v)
            d[k.strip()] = int(nums[0]) * 1024 if nums else 0
    return d

def _parse_cpuinfo():
    info = {}
    for ln in safe_read("/proc/cpuinfo").split("\n"):
        if ":" in ln:
            k, v = ln.split(":", 1)
            k = k.strip(); v = v.strip()
            if k not in info:
                info[k] = v
    return info

def _n_cores():
    try:
        return len([l for l in safe_read("/proc/cpuinfo").split("\n")
                    if l.startswith("processor")])
    except: return 1

def _cpu_usage(interval=1.0):
    """Hitung CPU usage dari /proc/stat (selalu tersedia)."""
    def read_stat():
        try:
            line = safe_read("/proc/stat").split("\n")[0]
            vals = list(map(int, line.split()[1:]))
            idle  = vals[3] + (vals[4] if len(vals) > 4 else 0)
            total = sum(vals)
            return idle, total
        except: return 0, 1
    i1, t1 = read_stat()
    time.sleep(interval)
    i2, t2 = read_stat()
    return 100.0 * (1 - (i2 - i1) / ((t2 - t1) or 1))

# ─── NET STATS (compatible Android 10+) ───────────────────────────────────────
def _net_iface_stats():
    """
    Baca statistik jaringan dari /sys/class/net/*/statistics/ —
    pengganti /proc/net/dev yang diblokir di Android 10+.
    """
    result = {}
    for iface_dir in safe_iterdir("/sys/class/net"):
        iface = iface_dir.name
        stats_dir = iface_dir / "statistics"
        if not stats_dir.exists():
            continue
        try:
            result[iface] = {
                "rx_bytes":   safe_int(safe_read(stats_dir/"rx_bytes")),
                "tx_bytes":   safe_int(safe_read(stats_dir/"tx_bytes")),
                "rx_packets": safe_int(safe_read(stats_dir/"rx_packets")),
                "tx_packets": safe_int(safe_read(stats_dir/"tx_packets")),
                "rx_errors":  safe_int(safe_read(stats_dir/"rx_errors")),
                "tx_errors":  safe_int(safe_read(stats_dir/"tx_errors")),
                "rx_dropped": safe_int(safe_read(stats_dir/"rx_dropped")),
                "tx_dropped": safe_int(safe_read(stats_dir/"tx_dropped")),
            }
        except Exception:
            continue
    return result

def _get_ip_for(iface):
    """Dapatkan IP dari nama interface."""
    try:
        import fcntl, struct
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(), 0x8915,
            struct.pack("256s", iface[:15].encode()))[20:24])
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 1 — CPU
# ══════════════════════════════════════════════════════════════════════════════
def fitur_cpu():
    hdr("FITUR 1 · INFO CPU", "🖥️")
    info    = _parse_cpuinfo()
    n_cores = _n_cores()

    # Model — beberapa device taruh di Hardware, bukan model name
    model = (info.get("model name") or info.get("Hardware") or
             getprop("ro.hardware") or getprop("ro.board.platform") or "?")
    row("Model / Hardware",  model[:60])
    row("Arsitektur",        info.get("CPU architecture", platform.machine()))
    row("Implementasi",      info.get("CPU implementer", "—"))
    row("Varian / Part",     f"{info.get('CPU variant','—')} / {info.get('CPU part','—')}")
    row("Jumlah Core",       n_cores or "?")
    row("BogoMIPS",          info.get("BogoMIPS", "—"))

    fitur_list = info.get("Features", "")
    if fitur_list:
        row("Fitur CPU", fitur_list[:64])

    # Frekuensi — beberapa path mungkin blocked, coba semuanya
    sec("Frekuensi CPU:")
    for path, label in [
        ("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "Saat Ini"),
        ("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq",  "Maksimum"),
        ("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq",  "Minimum"),
    ]:
        val = safe_read(path)
        if val and val.isdigit():
            mhz = int(val) / 1000
            row(label, f"{mhz:.0f} MHz  ({mhz/1000:.2f} GHz)")
        else:
            # Fallback ke cpuinfo
            if label == "Saat Ini":
                mhz_s = info.get("cpu MHz", "")
                if mhz_s:
                    row(label, f"{safe_float(mhz_s):.0f} MHz")
                else:
                    row(label, "Tidak tersedia")

    gov = safe_read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    if gov: row("Governor", gov)

    # Per-core freq
    sec("Frekuensi Per Core:")
    any_core = False
    for i in range(min(n_cores or 0, 8)):
        f = safe_read(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_cur_freq")
        if f and f.isdigit():
            row(f"Core {i}", f"{int(f)//1000} MHz")
            any_core = True
    if not any_core:
        info("Frekuensi per-core tidak tersedia (perlu akses lebih di Android 10+)")

    # Load average
    sec("Load Average & Penggunaan:")
    la = safe_read("/proc/loadavg").split()
    if la: row("Load Avg (1/5/15 menit)", f"{la[0]}  {la[1]}  {la[2]}")

    print(f"\n    {C.GRY}Mengukur penggunaan CPU 1 detik...{C.RST}", end="", flush=True)
    usage = _cpu_usage(1.0)
    print(f"\r{' '*40}\r", end="")
    print(f"    {bar(usage)}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 2 — RAM
# ══════════════════════════════════════════════════════════════════════════════
def fitur_ram():
    hdr("FITUR 2 · INFO RAM / MEMORI", "💾")
    m = _parse_meminfo()
    if not m:
        warn("/proc/meminfo tidak bisa dibaca."); return

    total    = m.get("MemTotal", 0)
    free     = m.get("MemFree",  0)
    avail    = m.get("MemAvailable", free)
    buffers  = m.get("Buffers", 0)
    cached   = m.get("Cached",  0) + m.get("SReclaimable", 0)
    used     = total - free - buffers - cached
    pct      = (max(used,0) / total * 100) if total else 0
    swap_tot = m.get("SwapTotal", 0)
    swap_use = swap_tot - m.get("SwapFree", swap_tot)

    row("Total RAM",     b2h(total))
    row("Terpakai",      b2h(max(used, 0)))
    row("Tersedia",      b2h(avail))
    row("Bebas (murni)", b2h(free))
    row("Buffer",        b2h(buffers))
    row("Cache",         b2h(cached))
    row("Active",        b2h(m.get("Active",   0)))
    row("Inactive",      b2h(m.get("Inactive", 0)))
    print(f"\n    {bar(pct)}")

    sec("SWAP / zRAM:")
    if swap_tot:
        row("Total",    b2h(swap_tot))
        row("Terpakai", b2h(swap_use))
        row("Bebas",    b2h(swap_tot - swap_use))
        print(f"    {bar(swap_use / swap_tot * 100 if swap_tot else 0)}")
    else:
        info("Tidak ada SWAP / zRAM aktif.")

    # zRAM device
    for zram in safe_iterdir("/sys/block"):
        if not zram.name.startswith("zram"): continue
        mm_s   = safe_read(zram/"mm_stat")
        orig   = safe_int(mm_s.split()[0] if mm_s else "0")
        compr  = safe_int(mm_s.split()[1] if mm_s and len(mm_s.split())>1 else "0")
        if orig:
            ratio = orig / compr if compr else 0
            row(f"zRAM ({zram.name})", f"orig {b2h(orig)} → compr {b2h(compr)}  ratio {ratio:.1f}x")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 3 — STORAGE
# ══════════════════════════════════════════════════════════════════════════════
def _statvfs(path):
    try:
        s = os.statvfs(path)
        total = s.f_blocks * s.f_frsize
        free  = s.f_bfree  * s.f_frsize
        avail = s.f_bavail * s.f_frsize
        used  = total - free
        pct   = (used / total * 100) if total else 0
        return total, used, avail, pct
    except: return None

SKIP_FS = {"tmpfs","proc","sysfs","devtmpfs","cgroup","cgroup2","pstore",
           "devpts","debugfs","securityfs","configfs","hugetlbfs","mqueue",
           "fusectl","bpf","tracefs","none","overlay","rootfs"}

def fitur_storage():
    hdr("FITUR 3 · INFO STORAGE / PENYIMPANAN", "💿")
    mounts_raw = safe_read("/proc/mounts")
    seen = set()

    if not mounts_raw:
        # Fallback: df
        df_out = run_cmd(["df","-h"], timeout=5)
        if df_out:
            sec("Dari perintah df:")
            for ln in df_out.split("\n"):
                print(f"    {C.WHT}{ln}{C.RST}")
        else:
            warn("Tidak bisa membaca info storage.")
        return

    for ln in mounts_raw.split("\n"):
        parts = ln.split()
        if len(parts) < 3: continue
        dev, mpt, fs = parts[0], parts[1], parts[2]
        if fs in SKIP_FS: continue
        if mpt in seen:  continue
        seen.add(mpt)
        res = _statvfs(mpt)
        if not res: continue
        total, used, avail, pct = res
        if total < 1024 * 1024: continue   # skip yg sangat kecil
        sec(f"{dev}  →  {mpt}  [{fs}]")
        row("Total",    b2h(total))
        row("Terpakai", b2h(used))
        row("Tersedia", b2h(avail))
        print(f"    {bar(pct)}")

    # /proc/diskstats — blocked di Android 10+, gunakan df sebagai pelengkap
    sec("Ringkasan df -h:")
    df_out = run_cmd(["df", "-h"], timeout=5)
    if df_out:
        lines = df_out.split("\n")
        print(f"    {C.GRY}{lines[0]}{C.RST}")  # header
        for ln in lines[1:]:
            parts = ln.split()
            if len(parts) < 5: continue
            # Tampilkan hanya yg signifikan (bukan tmpfs kecil)
            try:
                pct_str = [p for p in parts if p.endswith("%")]
                if pct_str: print(f"    {C.WHT}{ln}{C.RST}")
            except: pass
    else:
        info("/proc/diskstats & df tidak tersedia di perangkat ini.")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 4 — BATERAI
# ══════════════════════════════════════════════════════════════════════════════
def fitur_baterai():
    hdr("FITUR 4 · INFO BATERAI", "🔋")
    base = Path("/sys/class/power_supply")
    found = False

    for supply in safe_iterdir(base):
        stype = safe_read(supply / "type")
        if stype not in ("Battery","USB","Mains") and "bat" not in supply.name.lower():
            continue

        sec(f"Supply: {supply.name}  [{stype}]")
        found = True

        # Kapasitas
        cap = safe_read(supply / "capacity")
        if cap and cap.isdigit():
            pct = float(cap)
            row("Persentase", f"{pct:.0f}%")
            print(f"\n    {bar(pct)}\n")

        # Status
        status = safe_read(supply / "status")
        if status:
            col = C.GRN if status == "Charging" else C.YLW if status == "Discharging" else C.GRY
            row("Status", f"{col}{status}{C.RST}")

        # Fields teknis — masing-masing di-try sendiri
        fields = [
            ("technology",         "Teknologi",            ""),
            ("health",             "Kondisi (Health)",     ""),
            ("temp",               "Suhu",                 "temp"),
            ("voltage_now",        "Tegangan",             "voltage"),
            ("voltage_max_design", "Tegangan Desain",      "voltage"),
            ("current_now",        "Arus Saat Ini",        "current"),
            ("charge_now",         "Charge Saat Ini",      "charge"),
            ("charge_full",        "Charge Penuh",         "charge"),
            ("charge_full_design", "Charge Desain",        "charge"),
            ("energy_now",         "Energi Saat Ini",      "energy"),
            ("energy_full",        "Energi Penuh",         "energy"),
            ("cycle_count",        "Siklus Charge",        ""),
            ("manufacturer",       "Produsen",             ""),
            ("model_name",         "Model",                ""),
        ]
        for fname, label, ftype in fields:
            val = safe_read(supply / fname)
            if not val: continue
            try:
                if ftype == "temp" and val.lstrip("-").isdigit():
                    val = f"{int(val)/10:.1f}°C"
                elif ftype == "voltage" and val.lstrip("-").isdigit():
                    v_uv = int(val)
                    val = f"{v_uv/1_000_000:.3f} V"
                elif ftype == "current" and val.lstrip("-").isdigit():
                    c_ua = int(val)
                    val = f"{abs(c_ua)/1000:.0f} mA  ({'Keluar' if c_ua < 0 else 'Masuk'})"
                elif ftype == "charge" and val.isdigit():
                    val = f"{int(val)//1000} mAh"
                elif ftype == "energy" and val.isdigit():
                    val = f"{int(val)//1000} mWh"
            except Exception: pass
            row(label, val)

        # Health calculation
        cf = safe_read(supply / "charge_full"); cn = safe_read(supply / "charge_now")
        if cf.isdigit() and cn.isdigit() and int(cf):
            hp = int(cn)/int(cf)*100
            col = C.GRN if hp>80 else C.YLW if hp>60 else C.RED
            row("Health Baterai", f"{col}{hp:.1f}%{C.RST}")

    # Fallback: dumpsys battery
    if not found:
        sec("Fallback — dumpsys battery:")
        out = run_cmd(["dumpsys","battery"], timeout=6)
        if out:
            for ln in out.split("\n"):
                if ":" in ln and ln.strip():
                    k, _, v = ln.partition(":")
                    row(k.strip()[:28], v.strip())
            found = True
        else:
            warn("Tidak ada data baterai yang tersedia.")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 5 — SUHU HARDWARE
# ══════════════════════════════════════════════════════════════════════════════
def fitur_suhu():
    hdr("FITUR 5 · SUHU HARDWARE", "🌡️")
    found = False

    # /sys/class/thermal
    for zone in safe_iterdir("/sys/class/thermal"):
        temp_path = zone / "temp"
        type_path = zone / "type"
        if not temp_path.exists(): continue
        val = safe_read(temp_path)
        if not val or not val.lstrip("-").isdigit(): continue
        try:
            temp_raw  = int(val)
            zone_type = safe_read(type_path) or zone.name
            temp_c    = temp_raw / 1000 if abs(temp_raw) > 200 else float(temp_raw)
            if abs(temp_c) < 1 or abs(temp_c) > 150: continue   # filter nilai aneh
            st = (f"{C.RED}⚠ KRITIS{C.RST}" if temp_c >= 80
                  else f"{C.YLW}⚡ Panas{C.RST}" if temp_c >= 55
                  else f"{C.GRN}✓ Normal{C.RST}")
            print(f"    {zone_type:<32} {C.BOLD}{temp_c:>6.1f}°C{C.RST}  [{st}]")
            found = True
        except Exception: continue

    # /sys/class/hwmon
    for hw in safe_iterdir("/sys/class/hwmon"):
        name = safe_read(hw/"name") or hw.name
        for tf in hw.glob("temp*_input") if hw.is_dir() else []:
            try:
                t = safe_int(safe_read(tf)) / 1000
                if abs(t) < 1 or abs(t) > 150: continue
                lf = hw / tf.name.replace("input","label")
                label = safe_read(lf) or tf.name
                print(f"    {name}/{label:<28} {t:>6.1f}°C")
                found = True
            except Exception: continue

    # Fallback: getprop suhu
    if not found:
        sec("Fallback via getprop:")
        for key in ["ro.thermal.degree","sys.thermal.data","thermal.degree"]:
            val = getprop(key)
            if val: row(key, val); found = True
        if not found:
            warn("Sensor suhu tidak bisa diakses. Normal di Android 10+ tanpa root.")
            info("Coba: Pengaturan → Baterai → Info tambahan (tergantung HP)")

    # Suhu baterai dari power_supply (biasanya tersedia)
    sec("Suhu Baterai (dari power_supply):")
    bat_found = False
    for supply in safe_iterdir("/sys/class/power_supply"):
        val = safe_read(supply/"temp")
        if val and val.lstrip("-").isdigit():
            temp_c = int(val) / 10
            row(f"  {supply.name}", f"{temp_c:.1f}°C")
            bat_found = True
    if not bat_found:
        info("Suhu baterai tidak tersedia via /sys/class/power_supply")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 6 — JARINGAN
# ══════════════════════════════════════════════════════════════════════════════
def fitur_network():
    hdr("FITUR 6 · INFO JARINGAN", "🌐")

    # Hostname & IP
    try:
        hostname = socket.gethostname()
        row("Hostname", hostname)
        try:
            local_ip = socket.gethostbyname(hostname)
            row("IP Lokal (hostname)", local_ip)
        except Exception: pass
    except Exception: pass

    # IP Publik
    try:
        import urllib.request
        pub = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode().strip()
        row("IP Publik", pub)
    except Exception:
        row("IP Publik", "Tidak tersambung / timeout")

    # Interface stats dari /sys/class/net/*/statistics/ (Android 10+ compatible)
    sec("Interface Jaringan:")
    net = _net_iface_stats()
    if net:
        for iface, d in sorted(net.items()):
            oper  = safe_read(f"/sys/class/net/{iface}/operstate") or "?"
            col   = C.GRN if oper == "up" else C.RED
            mtu   = safe_read(f"/sys/class/net/{iface}/mtu")
            spd   = safe_read(f"/sys/class/net/{iface}/speed")
            spd_s = f"  {spd} Mbps" if spd and spd not in ("-1","","4294967295") else ""

            # Skip interface yg benar-benar tidak aktif
            if d["rx_bytes"] == 0 and d["tx_bytes"] == 0 and oper != "up":
                continue

            print(f"\n    {C.BOLD}{iface}{C.RST}  [{col}{oper}{C.RST}]{spd_s}")

            # IP
            ip = _get_ip_for(iface)
            if ip and not ip.startswith("0."): row("  IP", ip)

            # MAC — di Android 10+ sering di-randomize
            mac = safe_read(f"/sys/class/net/{iface}/address")
            if mac and mac not in ("00:00:00:00:00:00","02:00:00:00:00:00",""):
                row("  MAC", mac)
            else:
                row("  MAC", "(tersembunyi — privasi Android 10+)")

            if mtu: row("  MTU", mtu)
            row("  ⬇ Diterima", f"{b2h(d['rx_bytes'])}  ({d['rx_packets']:,} paket)")
            row("  ⬆ Dikirim",  f"{b2h(d['tx_bytes'])}  ({d['tx_packets']:,} paket)")
    else:
        info("Statistik interface tidak tersedia via /sys/class/net/*/statistics/")

    # Latensi TCP
    sec("Latensi TCP:")
    targets = [("Google DNS","8.8.8.8",53),("Cloudflare","1.1.1.1",53),
               ("Google","google.com",443),("GitHub","github.com",443)]
    for name, host, port in targets:
        try:
            t0 = time.perf_counter()
            s  = socket.create_connection((host, port), timeout=5); s.close()
            ms = (time.perf_counter() - t0) * 1000
            q  = C.GRN if ms < 80 else C.YLW if ms < 200 else C.RED
            print(f"    {C.GRN}✓{C.RST}  {name:<22} {q}{ms:>7.1f} ms{C.RST}")
        except Exception:
            print(f"    {C.RED}✗{C.RST}  {name:<22} {C.RED}Tidak terjangkau{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 7 — INFO SISTEM & OS
# ══════════════════════════════════════════════════════════════════════════════
def fitur_os():
    hdr("FITUR 7 · INFO SISTEM & OS ANDROID", "📱")
    uname = platform.uname()
    row("Sistem",        uname.system)
    row("Kernel",        uname.release)
    row("Arsitektur",    uname.machine)
    row("Python",        platform.python_version())

    # Uptime
    up_raw = safe_read("/proc/uptime").split()
    if up_raw:
        up_s = safe_float(up_raw[0])
        h, r = divmod(int(up_s), 3600); m, s = divmod(r, 60)
        row("Uptime", f"{h} jam  {m} menit  {s} detik")

    # Android props via getprop — paling reliable di Termux
    sec("Info Perangkat Android:")
    props_device = [
        ("ro.product.brand",         "Brand"),
        ("ro.product.manufacturer",  "Produsen"),
        ("ro.product.model",         "Model"),
        ("ro.product.name",          "Nama Produk"),
        ("ro.product.device",        "Kode Device"),
        ("ro.product.board",         "Board"),
        ("ro.hardware",              "Hardware"),
        ("ro.board.platform",        "Platform"),
        ("ro.product.cpu.abi",       "CPU ABI"),
        ("ro.product.cpu.abilist",   "ABI List"),
    ]
    for key, label in props_device:
        val = getprop(key)
        if val: row(label, val[:64])

    sec("Info Android OS:")
    props_os = [
        ("ro.build.version.release", "Android Version"),
        ("ro.build.version.sdk",     "SDK Level"),
        ("ro.build.version.security_patch", "Security Patch"),
        ("ro.build.id",              "Build ID"),
        ("ro.build.type",            "Build Type"),
        ("ro.build.date",            "Tanggal Build"),
        ("ro.build.flavor",          "Build Flavor"),
        ("ro.build.fingerprint",     "Fingerprint"),
    ]
    for key, label in props_os:
        val = getprop(key)
        if val: row(label, val[:70])

    sec("Info Tambahan:")
    props_extra = [
        ("ro.serialno",              "Serial Number"),
        ("ro.boot.hardware",         "Boot Hardware"),
        ("ro.secure",                "Secure Boot"),
        ("ro.debuggable",            "Debuggable"),
        ("ro.adb.secure",            "ADB Secure"),
        ("persist.sys.timezone",     "Timezone"),
        ("persist.sys.language",     "Bahasa"),
        ("ro.sf.lcd_density",        "LCD Density (dpi)"),
        ("ro.opengles.version",      "OpenGL ES Version"),
    ]
    for key, label in props_extra:
        val = getprop(key)
        if val: row(label, val[:60])

    # /etc/os-release (Termux)
    osr = safe_read("/etc/os-release")
    if osr:
        sec("OS Release:")
        for ln in osr.split("\n"):
            if "=" in ln:
                k, v = ln.split("=", 1)
                if k in ("PRETTY_NAME","NAME","VERSION"):
                    row(k, v.strip('"'))


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 8 — PROSES AKTIF
# ══════════════════════════════════════════════════════════════════════════════
def fitur_proses():
    hdr("FITUR 8 · PROSES AKTIF", "⚙️")

    # Android 10+: /proc/<pid> hanya bisa dibaca untuk proses sendiri
    # Gunakan 'top' atau 'ps' sebagai sumber utama
    sec("Top Proses (via top / ps):")

    # Coba top dulu
    top_out = run_cmd(["top", "-n", "1", "-b"], timeout=8)
    if not top_out:
        top_out = run_cmd(["top", "-n", "1"], timeout=8)

    if top_out:
        lines = top_out.split("\n")
        printed = 0
        header_found = False
        for ln in lines:
            if any(kw in ln.upper() for kw in ["PID","CPU","MEM","COMMAND","%CPU"]):
                header_found = True
                print(f"    {C.BOLD}{ln}{C.RST}")
                continue
            if header_found and ln.strip() and printed < 15:
                print(f"    {C.WHT}{ln}{C.RST}")
                printed += 1
    else:
        # Fallback: ps
        ps_out = run_cmd(["ps", "-A"], timeout=6)
        if not ps_out:
            ps_out = run_cmd(["ps"], timeout=6)
        if ps_out:
            lines = ps_out.split("\n")
            print(f"    {C.BOLD}{lines[0] if lines else ''}{C.RST}")
            for ln in lines[1:16]:
                if ln.strip():
                    print(f"    {C.WHT}{ln}{C.RST}")
        else:
            warn("top/ps tidak tersedia di perangkat ini.")
            info("Di Android 10+, akses /proc/<pid> dibatasi untuk proses lain.")

    # Info proses dari /proc yang bisa diakses
    sec("Statistik Sistem:")
    all_pids = [d for d in safe_iterdir("/proc") if d.name.isdigit()]
    row("PID yang terlihat", len(all_pids))

    # Thread max
    tm = safe_read("/proc/sys/kernel/threads-max")
    if tm: row("Max Thread Sistem", tm)

    # Proses script sendiri
    mypid = os.getpid()
    sec(f"Proses Script Ini (PID {mypid}):")
    my_status = safe_read(f"/proc/{mypid}/status")
    if my_status:
        for ln in my_status.split("\n"):
            if any(ln.startswith(k) for k in ("Name:","VmRSS:","VmSize:","Threads:")):
                k, _, v = ln.partition(":")
                row(k.strip(), v.strip())


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 9 — KECEPATAN JARINGAN
# ══════════════════════════════════════════════════════════════════════════════
def fitur_netspeed():
    hdr("FITUR 9 · KECEPATAN JARINGAN", "📡")

    # Gunakan /sys/class/net/*/statistics/ (Android 10+ compatible)
    def total_bytes():
        rx = tx = 0
        for iface, d in _net_iface_stats().items():
            if iface == "lo": continue
            rx += d["rx_bytes"]; tx += d["tx_bytes"]
        return rx, tx

    print(f"    {C.GRY}Mengukur 3 detik...{C.RST}", end="", flush=True)
    r1, t1 = total_bytes()
    time.sleep(3)
    r2, t2 = total_bytes()
    print(f"\r{' '*32}\r", end="")

    dl = (r2 - r1) / 3
    ul = (t2 - t1) / 3

    if dl > 0 or ul > 0:
        row("⬇ Download (real-time)", f"{b2h(dl)}/s  ({dl*8/1e6:.3f} Mbps)")
        row("⬆ Upload   (real-time)", f"{b2h(ul)}/s  ({ul*8/1e6:.3f} Mbps)")
    else:
        info("Tidak ada traffic terdeteksi. Pastikan ada aktifitas jaringan.")

    sec("Uji Download (1 MB dari Cloudflare):")
    try:
        import urllib.request as ur
        t0   = time.perf_counter()
        req  = ur.Request("https://speed.cloudflare.com/__down?bytes=1048576",
                          headers={"User-Agent": "cek-hardware-android/3.0"})
        data = ur.urlopen(req, timeout=20).read()
        secs = time.perf_counter() - t0
        row("Ukuran",    b2h(len(data)))
        row("Waktu",     f"{secs:.2f} detik")
        row("Kecepatan", f"{b2h(len(data)/secs)}/s  ({len(data)*8/secs/1e6:.2f} Mbps)")
        ok("Speed test selesai!")
    except Exception as e:
        warn(f"Uji download gagal: {type(e).__name__}")
        info("Periksa koneksi internet atau coba lagi.")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 10 — BENCHMARK CPU
# ══════════════════════════════════════════════════════════════════════════════
def fitur_benchmark():
    hdr("FITUR 10 · BENCHMARK CPU (Pure Python)", "⚡")
    import math, threading

    sec("Tes 1: Kalkulasi π — Leibniz 5 juta iterasi:")
    print(f"    {C.GRY}Menghitung...{C.RST}", end="", flush=True)
    t0 = time.perf_counter()
    pi, sign = 0.0, 1
    for i in range(5_000_000):
        pi += sign / (2*i+1); sign = -sign
    pi *= 4
    s = time.perf_counter() - t0
    print(f"\r{' '*25}\r", end="")
    row("Nilai π",   f"{pi:.10f}")
    row("Waktu",     f"{s:.3f} detik")
    row("Kecepatan", f"{5_000_000/s/1e6:.2f} juta iter/detik")

    sec("Tes 2: Float Ops — sin/cos/sqrt 500 ribu iterasi:")
    print(f"    {C.GRY}Menghitung...{C.RST}", end="", flush=True)
    t0 = time.perf_counter()
    acc = 0.0
    for i in range(1, 500_001):
        acc += math.sin(i) * math.cos(i) + math.sqrt(i)
    s = time.perf_counter() - t0
    print(f"\r{' '*25}\r", end="")
    row("Waktu",     f"{s:.3f} detik")
    row("Kecepatan", f"{500_000/s/1e6:.2f} juta op/detik")

    n_t = min(max(_n_cores(), 1), 4)
    sec(f"Tes 3: Multi-Thread — {n_t} thread, 2 juta iter/thread:")
    results = []
    def worker(n):
        a = 0.0
        for i in range(1, n+1): a += math.sqrt(i) * math.log(i+1)
        results.append(a)
    threads = [threading.Thread(target=worker, args=(2_000_000,)) for _ in range(n_t)]
    t0 = time.perf_counter()
    for t in threads: t.start()
    for t in threads: t.join()
    s = time.perf_counter() - t0
    total_ops = 2_000_000 * n_t
    row("Thread",        n_t)
    row("Total Operasi", f"{total_ops:,}")
    row("Waktu",         f"{s:.3f} detik")
    row("Throughput",    f"{total_ops/s/1e6:.2f} juta op/detik")

    sec("Tes 4: Memori Bandwidth — alokasi + write 30 MB:")
    size = 30 * 1024 * 1024
    t0 = time.perf_counter()
    data = bytearray(size)
    for i in range(0, size, 4096): data[i] = i & 0xFF
    s = time.perf_counter() - t0
    row("Ukuran",    b2h(size))
    row("Waktu",     f"{s:.3f} detik")
    row("Bandwidth", f"{b2h(size/s)}/s")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 11 — MONITOR REAL-TIME
# ══════════════════════════════════════════════════════════════════════════════
def fitur_monitor():
    hdr("FITUR 11 · MONITOR REAL-TIME (10 detik)", "📊")
    print(f"    {C.GRY}Tekan Ctrl+C untuk berhenti.{C.RST}\n")

    def get_cpu_stat():
        try:
            vals = list(map(int, safe_read("/proc/stat").split("\n")[0].split()[1:]))
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            return idle, sum(vals)
        except: return 0, 1

    def get_net_total():
        rx = tx = 0
        for iface, d in _net_iface_stats().items():
            if iface != "lo":
                rx += d["rx_bytes"]; tx += d["tx_bytes"]
        return rx, tx

    ci, ct = get_cpu_stat()
    nr, nt = get_net_total()

    print(f"    {C.BOLD}{'Dtk':>4}  {'CPU%':>7}  {'RAM%':>7}  {'Suhu':>8}  {'Net⬇/s':>12}  {'Net⬆/s':>12}{C.RST}")
    print(f"    {'─'*66}")

    def get_max_temp():
        """Ambil suhu tertinggi yang tersedia."""
        max_t = None
        for zone in safe_iterdir("/sys/class/thermal"):
            val = safe_read(zone/"temp")
            if val and val.lstrip("-").isdigit():
                try:
                    t = int(val)
                    t_c = t/1000 if abs(t) > 200 else float(t)
                    if 1 < t_c < 150:
                        max_t = max(max_t or t_c, t_c)
                except Exception: pass
        return max_t

    try:
        for tick in range(1, 11):
            time.sleep(1)
            ci2, ct2 = get_cpu_stat()
            dt  = (ct2 - ct) or 1
            cpu = 100 * (1 - (ci2 - ci) / dt)
            ci, ct = ci2, ct2

            m     = _parse_meminfo()
            total = m.get("MemTotal", 1)
            free  = m.get("MemFree", 1)
            buf   = m.get("Buffers", 0)
            cach  = m.get("Cached", 0) + m.get("SReclaimable", 0)
            used  = total - free - buf - cach
            ram   = (max(used, 0) / total * 100) if total else 0

            nr2, nt2 = get_net_total()
            dl = nr2 - nr; ul = nt2 - nt
            nr, nt = nr2, nt2

            temp = get_max_temp()
            temp_s = f"{temp:.0f}°C" if temp else "N/A"
            tc = C.RED if (temp or 0) >= 80 else C.YLW if (temp or 0) >= 55 else C.GRN

            cc = C.RED if cpu > 80 else C.YLW if cpu > 50 else C.GRN
            rc = C.RED if ram > 80 else C.YLW if ram > 60 else C.GRN
            print(f"    {C.GRY}{tick:>4}{C.RST}"
                  f"  {cc}{cpu:>6.1f}%{C.RST}"
                  f"  {rc}{ram:>6.1f}%{C.RST}"
                  f"  {tc}{temp_s:>8}{C.RST}"
                  f"  {C.CYN}{b2h(dl):>12}{C.RST}"
                  f"  {C.CYN}{b2h(ul):>12}{C.RST}")
    except KeyboardInterrupt:
        print(f"\n    {C.GRY}Monitor dihentikan.{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 12 — LAPORAN JSON + TXT
# ══════════════════════════════════════════════════════════════════════════════
def fitur_laporan():
    hdr("FITUR 12 · LAPORAN LENGKAP (Export JSON + TXT)", "📋")

    m   = _parse_meminfo()
    net = _net_iface_stats()
    up  = safe_float(safe_read("/proc/uptime").split()[0] if safe_read("/proc/uptime").split() else "0")

    # Battery
    bat_data = {}
    for sup in safe_iterdir("/sys/class/power_supply"):
        cap = safe_read(sup/"capacity")
        status = safe_read(sup/"status")
        tech   = safe_read(sup/"technology")
        if cap: bat_data[sup.name] = {"capacity":cap,"status":status,"technology":tech}

    # Thermal
    thermals = []
    for zone in safe_iterdir("/sys/class/thermal"):
        val = safe_read(zone/"temp")
        if val and val.lstrip("-").isdigit():
            try:
                t_raw = int(val)
                t_c   = t_raw/1000 if abs(t_raw)>200 else float(t_raw)
                if 1 < t_c < 150:
                    thermals.append({"zone": safe_read(zone/"type") or zone.name, "temp_c": round(t_c,1)})
            except Exception: pass

    # Android info
    android = {}
    for key in ["ro.product.brand","ro.product.model","ro.product.manufacturer",
                "ro.build.version.release","ro.build.version.sdk",
                "ro.build.id","ro.product.cpu.abi","ro.hardware",
                "ro.board.platform","ro.sf.lcd_density"]:
        val = getprop(key)
        if val: android[key] = val

    # Storage
    storage = []
    seen = set()
    for ln in safe_read("/proc/mounts").split("\n"):
        parts = ln.split()
        if len(parts) < 3: continue
        dev, mpt, fs = parts[0], parts[1], parts[2]
        if fs in SKIP_FS or mpt in seen: continue
        seen.add(mpt)
        res = _statvfs(mpt)
        if res and res[0] > 1024*1024:
            storage.append({"device":dev,"mountpoint":mpt,"filesystem":fs,
                            "total":res[0],"used":res[1],"free":res[2],"pct":round(res[3],2)})

    cpuinfo = _parse_cpuinfo()
    laporan = {
        "meta":    {"waktu":datetime.datetime.now().isoformat(),
                    "versi":"android-v3.0","python":platform.python_version()},
        "android": android,
        "sistem":  {"os":platform.system(),"kernel":platform.release(),
                    "mesin":platform.machine(),"hostname":platform.node(),
                    "uptime_detik":int(up)},
        "cpu":     {"model":cpuinfo.get("model name",cpuinfo.get("Hardware","?")),
                    "cores":_n_cores(),"load_avg":safe_read("/proc/loadavg").split()[:3]},
        "ram":     {"total":m.get("MemTotal",0),"available":m.get("MemAvailable",0),
                    "swap_total":m.get("SwapTotal",0)},
        "storage": storage,
        "baterai": bat_data,
        "thermal": thermals,
        "jaringan":{iface:{"rx":d["rx_bytes"],"tx":d["tx_bytes"]} for iface,d in net.items()},
    }

    ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    jfile = f"laporan_{ts}.json"
    tfile = f"laporan_{ts}.txt"

    with open(jfile, "w", encoding="utf-8") as f:
        json.dump(laporan, f, ensure_ascii=False, indent=2)

    with open(tfile, "w", encoding="utf-8") as f:
        f.write(f"CEK HARDWARE ANDROID v3.0\nWaktu: {laporan['meta']['waktu']}\n{'='*54}\n")
        f.write(f"\nPERANGKAT:\n")
        for k,v in android.items(): f.write(f"  {k}: {v}\n")
        f.write(f"\nSISTEM:\n  Uptime: {int(up)//3600}j {(int(up)%3600)//60}m\n")
        f.write(f"  Kernel: {platform.release()}\n")
        f.write(f"\nRAM: {b2h(laporan['ram']['total'])}  tersedia: {b2h(laporan['ram']['available'])}\n")
        for s in storage:
            f.write(f"\nDisk {s['mountpoint']}: {b2h(s['total'])}  ({s['pct']}% terpakai)\n")
        for name, bat in bat_data.items():
            f.write(f"\nBaterai: {bat.get('capacity','?')}%  ({bat.get('status','?')})\n")
        for t in thermals:
            f.write(f"Suhu {t['zone']}: {t['temp_c']}°C\n")

    sec("File Tersimpan:")
    row("JSON", f"{jfile}  ({b2h(Path(jfile).stat().st_size)})")
    row("TXT",  f"{tfile}  ({b2h(Path(tfile).stat().st_size)})")
    ok("Laporan berhasil disimpan!")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 13 — INFO GPU
# ══════════════════════════════════════════════════════════════════════════════
def fitur_gpu():
    hdr("FITUR 13 · INFO GPU", "🎮")
    found = False

    # Identifikasi GPU dari getprop (paling reliable tanpa root)
    sec("Identifikasi GPU dari getprop:")
    gpu_props = {
        "ro.hardware.egl":          "EGL Driver",
        "ro.board.platform":        "Platform (SoC)",
        "ro.hardware":              "Hardware",
        "ro.gfx.driver.0":         "GPU Driver",
        "ro.gfx.driver.1":         "GPU Driver Alt",
        "debug.hwui.renderer":      "Renderer",
        "ro.opengles.version":      "OpenGL ES Version (raw)",
    }
    for key, label in gpu_props.items():
        val = getprop(key)
        if val:
            # Decode OpenGL ES version
            if key == "ro.opengles.version" and val.isdigit():
                v = int(val)
                major = (v >> 16) & 0xFFFF; minor = v & 0xFFFF
                val = f"{val}  → OpenGL ES {major}.{minor}"
            row(label, val)
            found = True

    # Tebak GPU dari platform
    platform_val = getprop("ro.board.platform") or getprop("ro.hardware","")
    if platform_val:
        pf = platform_val.lower()
        if any(k in pf for k in ["sm6","sm7","sm8","qcom","msm","sdm","snapdragon"]):
            sec("GPU Terdeteksi: Qualcomm Adreno")
            # Coba baca clock dari berbagai path alternatif
            for freq_path in [
                "/sys/class/kgsl/kgsl-3d0/gpu_clock",
                "/sys/class/kgsl/kgsl-3d0/devfreq/cur_freq",
                "/sys/kernel/gpu/gpu_clock",
                "/sys/kernel/debug/clk/gpuclk/measure",
            ]:
                val = safe_read(freq_path)
                if val and val.isdigit():
                    row("GPU Clock", f"{int(val)/1e6:.0f} MHz" if int(val) > 1e6 else f"{val} MHz")
                    found = True; break

            for busy_path in [
                "/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage",
                "/sys/kernel/gpu/gpu_busy",
            ]:
                val = safe_read(busy_path)
                if val: row("GPU Busy", f"{val}%"); found = True; break

        elif any(k in pf for k in ["mali","arm","mt","helio","dimensity"]):
            sec("GPU Terdeteksi: ARM Mali")
            for freq_path in [
                "/sys/class/misc/mali0/device/devfreq/mali0/cur_freq",
                "/sys/devices/platform/mali.0/devfreq/mali.0/cur_freq",
                "/sys/kernel/gpu/gpu_clock",
            ]:
                val = safe_read(freq_path)
                if val and val.isdigit():
                    row("GPU Clock", f"{int(val)/1e6:.0f} MHz")
                    found = True; break

        elif any(k in pf for k in ["exynos","samsung"]):
            sec("GPU Terdeteksi: ARM Mali (Samsung Exynos)")
            found = True

    # DevFreq — scan semua, filter yang GPU
    sec("DevFreq Frequencies:")
    for df in safe_iterdir("/sys/class/devfreq"):
        name = df.name.lower()
        if not any(k in name for k in ("gpu","kgsl","mali","gfx","adreno","dpu")):
            continue
        cur = safe_read(df/"cur_freq"); mx = safe_read(df/"max_freq")
        gov = safe_read(df/"governor")
        if cur or mx:
            print(f"\n    {C.MAG}{df.name}{C.RST}")
            if cur.isdigit(): row("  Freq Saat Ini", f"{int(cur)/1e6:.0f} MHz")
            if mx.isdigit():  row("  Freq Maks",     f"{int(mx)/1e6:.0f} MHz")
            if gov:           row("  Governor",      gov)
            found = True

    if not found:
        warn("Info GPU tidak bisa diakses langsung di Android 10+ tanpa root.")
        info("GPU teridentifikasi dari SoC (getprop ro.board.platform) di atas.")
        info("Untuk info GPU lengkap, gunakan aplikasi: CPU-Z, Aida64, DevCheck.")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 14 — WIFI DETAIL
# ══════════════════════════════════════════════════════════════════════════════
def fitur_wifi():
    hdr("FITUR 14 · WiFi DETAIL", "📶")
    found = False

    # Interface WiFi dari /sys/class/net
    sec("Interface WiFi:")
    for iface_dir in safe_iterdir("/sys/class/net"):
        iface = iface_dir.name
        # Hanya interface wireless
        if not (iface.startswith("wlan") or iface.startswith("wl")):
            continue
        oper  = safe_read(iface_dir/"operstate") or "?"
        col   = C.GRN if oper == "up" else C.RED
        mtu   = safe_read(iface_dir/"mtu")
        txq   = safe_read(iface_dir/"tx_queue_len")
        typ   = safe_read(iface_dir/"type")
        found = True
        print(f"\n    {C.BOLD}{iface}{C.RST}  [{col}{oper}{C.RST}]")
        ip = _get_ip_for(iface)
        if ip and not ip.startswith("0."): row("  IP Address", ip)
        mac = safe_read(iface_dir/"address")
        if mac and mac not in ("00:00:00:00:00:00","02:00:00:00:00:00",""):
            row("  MAC", mac)
        else:
            row("  MAC", "(diprivasi — Android 10+)")
        if mtu: row("  MTU", mtu)
        if txq: row("  TX Queue Len", txq)

        # Stats
        st = iface_dir / "statistics"
        if st.exists():
            rx = safe_int(safe_read(st/"rx_bytes"))
            tx = safe_int(safe_read(st/"tx_bytes"))
            row("  ⬇ Diterima", b2h(rx))
            row("  ⬆ Dikirim",  b2h(tx))

    # getprop WiFi
    sec("Android WiFi Properties (getprop):")
    wifi_props = [
        ("wifi.interface",            "Interface"),
        ("wifi.direct.interface",     "WiFi Direct"),
        ("wlan.driver.status",        "Driver Status"),
        ("init.svc.wpa_supplicant",   "WPA Supplicant"),
        ("ro.wifi.channels",          "Channels"),
        ("ro.bootimage.build.id",     "Boot Build ID"),
        ("net.wifi.state",            "WiFi State"),
        ("dhcp.wlan0.dns1",           "DNS 1 (DHCP)"),
        ("dhcp.wlan0.dns2",           "DNS 2 (DHCP)"),
        ("dhcp.wlan0.gateway",        "Gateway (DHCP)"),
        ("dhcp.wlan0.ipaddress",      "IP (DHCP)"),
        ("dhcp.wlan0.mask",           "Netmask (DHCP)"),
        ("dhcp.wlan0.leasetime",      "Lease Time (s)"),
    ]
    any_prop = False
    for key, label in wifi_props:
        val = getprop(key)
        if val: row(label, val); any_prop = True; found = True
    if not any_prop:
        info("WiFi properties tidak tersedia.")

    # dumpsys wifi — coba baca SSID & info koneksi
    sec("Koneksi WiFi Aktif (dumpsys wifi):")
    wifi_dump = run_cmd(["dumpsys","wifi"], timeout=8)
    if wifi_dump:
        for keyword in ["SSID","BSSID","supplicantState","linkSpeed","rssi",
                        "frequency","signalStrength","ipAddress","macAddress"]:
            for ln in wifi_dump.split("\n"):
                if keyword in ln and "=" in ln and ln.strip():
                    print(f"    {C.WHT}{ln.strip()[:80]}{C.RST}")
                    found = True
                    break
    else:
        info("dumpsys wifi tidak tersedia (perlu permission android.permission.DUMP).")
        info("Coba: Pengaturan → WiFi → ketuk jaringan aktif untuk lihat detail.")

    # Resolv.conf — DNS server
    sec("DNS Server:")
    resolv = safe_read("/etc/resolv.conf") or safe_read("/data/misc/net/resolv.conf")
    if resolv:
        for ln in resolv.split("\n"):
            if ln.startswith("nameserver"): row("  DNS", ln.split()[-1]); found = True
    else:
        # Coba dari getprop
        for prop in ["dhcp.wlan0.dns1","dhcp.wlan0.dns2","net.dns1","net.dns2"]:
            val = getprop(prop)
            if val: row(f"  DNS ({prop})", val); found = True

    if not found:
        warn("WiFi interface tidak terdeteksi atau WiFi sedang tidak aktif.")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 15 — KERNEL & SISTEM
# ══════════════════════════════════════════════════════════════════════════════
def fitur_kernel():
    hdr("FITUR 15 · KERNEL & PARAMETER SISTEM", "🔧")

    # Versi kernel — selalu tersedia
    sec("Versi Kernel:")
    ver = safe_read("/proc/version")
    if ver:
        row("Versi Lengkap", ver[:80])
    uname = platform.uname()
    row("Release",    uname.release)
    row("Mesin",      uname.machine)

    # /proc/sys/kernel params yang biasanya tersedia
    sec("Kernel Parameters:")
    params = [
        ("kernel/ostype",          "OS Type"),
        ("kernel/osrelease",       "OS Release"),
        ("kernel/pid_max",         "PID Max"),
        ("kernel/threads-max",     "Threads Max"),
        ("kernel/randomize_va_space", "ASLR (0=off 2=full)"),
        ("kernel/panic",           "Panic Timeout"),
        ("kernel/ngroups_max",     "ngroups Max"),
        ("kernel/sched_latency_ns","Sched Latency (ns)"),
        ("vm/swappiness",          "VM Swappiness"),
        ("vm/dirty_ratio",         "VM Dirty Ratio %"),
        ("vm/overcommit_memory",   "VM Overcommit"),
        ("vm/min_free_kbytes",     "Min Free KB"),
        ("net/core/rmem_max",      "Net rmem_max"),
        ("net/core/wmem_max",      "Net wmem_max"),
        ("net/core/somaxconn",     "Max Connections"),
    ]
    base = Path("/proc/sys")
    for rel, label in params:
        val = safe_read(base/rel)
        if val: row(label, val[:60])

    # /proc/cmdline — di Android 10+ biasanya blocked
    sec("Kernel Boot Cmdline:")
    cmdline = safe_read("/proc/cmdline")
    if cmdline:
        for part in cmdline.split():
            if any(k in part for k in ("androidboot","selinux","mem","cpu","init")):
                print(f"    {C.GRY}{part}{C.RST}")
    else:
        info("Boot cmdline tidak tersedia (dibatasi Android 10+).")
        # Fallback getprop
        for key in ["ro.boot.selinux","ro.bootmode","ro.boot.hardware"]:
            val = getprop(key)
            if val: row(key, val)

    # /proc/modules — hampir selalu blocked
    sec("Modul Kernel (/proc/modules):")
    mods_raw = safe_read("/proc/modules")
    if mods_raw:
        mods = []
        for ln in mods_raw.split("\n"):
            parts = ln.split()
            if len(parts) >= 2:
                mods.append((parts[0], safe_int(parts[1]) if len(parts)>1 else 0))
        row("Total Modul", len(mods))
        for name, size in sorted(mods, key=lambda x: x[1], reverse=True)[:20]:
            print(f"    {C.CYN}{name:<30}{C.RST}  {b2h(size)}")
    else:
        info("/proc/modules tidak bisa diakses (normal di Android 10+ tanpa root).")
        info("Coba: adb shell cat /proc/modules (via ADB)")

    # SELinux status
    sec("SELinux:")
    for path in ["/sys/fs/selinux/enforce", "/selinux/enforce"]:
        val = safe_read(path)
        if val:
            mode = "Enforcing" if val == "1" else "Permissive"
            col  = C.GRN if val == "1" else C.YLW
            row("Mode", f"{col}{mode}{C.RST}  (raw: {val})")
            break
    else:
        selinux_prop = getprop("ro.build.selinux") or getprop("ro.boot.selinux")
        row("SELinux (getprop)", selinux_prop or "Tidak tersedia")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 16 — VIRTUAL MEMORY STATS
# ══════════════════════════════════════════════════════════════════════════════
def fitur_vmstat():
    hdr("FITUR 16 · VIRTUAL MEMORY STATS", "🧮")

    # /proc/vmstat
    vmraw = safe_read("/proc/vmstat")
    if vmraw:
        vm = {}
        for ln in vmraw.split("\n"):
            parts = ln.split()
            if len(parts) == 2: vm[parts[0]] = safe_int(parts[1])

        sec("Page Activity:")
        row("Page Fault Minor (pgfault)",   f"{vm.get('pgfault',0):,}")
        row("Page Fault Major (pgmajfault)",f"{vm.get('pgmajfault',0):,}")
        row("Page In  (pgpgin)",            f"{vm.get('pgpgin',0):,} KB")
        row("Page Out (pgpgout)",           f"{vm.get('pgpgout',0):,} KB")
        row("Page Freed (pgfree)",          f"{vm.get('pgfree',0):,}")

        sec("Swap Activity:")
        row("Swap In  (pswpin)",  f"{vm.get('pswpin',0):,}  halaman masuk")
        row("Swap Out (pswpout)", f"{vm.get('pswpout',0):,}  halaman keluar")

        sec("Memory Reclaim:")
        row("kswapd steal",  f"{vm.get('kswapd_steal',0):,}")
        row("OOM Kill",      f"{vm.get('oom_kill',0):,}")
        if vm.get("oom_kill",0) > 0:
            warn(f"OOM Killer pernah berjalan {vm['oom_kill']}x — RAM pernah kritis!")

        sec("Huge Pages:")
        row("THP Fault Alloc",    f"{vm.get('thp_fault_alloc',0):,}")
        row("THP Collapse Alloc", f"{vm.get('thp_collapse_alloc',0):,}")

        # Rate (dari /proc/stat yang lebih reliable)
        sec("Context Switch & Interrupt (dari /proc/stat):")
        stat_raw = safe_read("/proc/stat")
        for ln in stat_raw.split("\n"):
            parts = ln.split()
            if not parts: continue
            if parts[0] == "ctxt"    and len(parts)>1: row("Context Switches total", f"{int(parts[1]):,}")
            if parts[0] == "intr"    and len(parts)>1: row("Interrupts total",        f"{int(parts[1]):,}")
            if parts[0] == "softirq" and len(parts)>1: row("Soft IRQ total",          f"{int(parts[1]):,}")
            if parts[0] == "procs_running": row("Proses Running",               parts[1])
            if parts[0] == "procs_blocked": row("Proses Blocked",               parts[1])

        # Activity rate (ukur 3 detik)
        sec("Activity Rate (diukur 3 detik):")
        snap = {k: vm.get(k,0) for k in ["pgpgin","pgpgout","pswpin","pswpout","pgfault"]}
        print(f"    {C.GRY}Mengukur...{C.RST}", end="", flush=True)
        time.sleep(3)
        print(f"\r{' '*20}\r", end="")
        vm2 = {}
        for ln in safe_read("/proc/vmstat").split("\n"):
            parts = ln.split()
            if len(parts) == 2: vm2[parts[0]] = safe_int(parts[1])
        row("Page In/s",    f"{(vm2.get('pgpgin',0)-snap['pgpgin'])//3:,} KB/s")
        row("Page Out/s",   f"{(vm2.get('pgpgout',0)-snap['pgpgout'])//3:,} KB/s")
        row("Page Fault/s", f"{(vm2.get('pgfault',0)-snap['pgfault'])//3:,}/s")
        row("Swap In/s",    f"{(vm2.get('pswpin',0)-snap['pswpin'])//3:,} hal/s")
    else:
        info("/proc/vmstat tidak tersedia. Coba alternatif:")
        # Fallback: info dari /proc/meminfo yang selalu tersedia
        m = _parse_meminfo()
        sec("Info Memori dari /proc/meminfo:")
        keys = ["MemTotal","MemFree","MemAvailable","Buffers","Cached","SwapTotal",
                "SwapFree","Active","Inactive","Unevictable","Mlocked"]
        for k in keys:
            if k in m: row(k, b2h(m[k]))


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 17 — SENSOR HARDWARE
# ══════════════════════════════════════════════════════════════════════════════
def fitur_sensor():
    hdr("FITUR 17 · SENSOR HARDWARE", "🧭")
    found = False

    # dumpsys sensorservice — paling reliable di Android Termux
    sec("Sensor List (dumpsys sensorservice):")
    sensor_dump = run_cmd(["dumpsys","sensorservice"], timeout=10)
    if sensor_dump:
        in_list = False
        count   = 0
        for ln in sensor_dump.split("\n"):
            if "Sensor List" in ln or "sensor 0x" in ln.lower():
                in_list = True
            if in_list and ln.strip():
                # Tampilkan baris yang berisi info sensor
                if any(k in ln for k in ["handle","type","name","vendor",
                                         "0x0000","Accel","Gyro","Magnet",
                                         "Pressure","Light","Proximity","Gravity"]):
                    print(f"    {C.WHT}{ln.strip()[:80]}{C.RST}")
                    count += 1
                    found = True
                if count >= 30: break
        if count == 0:
            # Tampilkan sebagian awal dump
            for ln in sensor_dump.split("\n")[:25]:
                if ln.strip(): print(f"    {C.GRY}{ln.strip()[:80]}{C.RST}")
            found = True
    else:
        info("dumpsys sensorservice tidak tersedia.")

    # IIO sensors — biasanya blocked di Android 10+
    sec("IIO Sensors (/sys/bus/iio/devices):")
    iio_base = Path("/sys/bus/iio/devices")
    if not iio_base.exists():
        info("/sys/bus/iio/devices tidak tersedia di perangkat ini.")
    else:
        for dev in safe_iterdir(iio_base):
            name = safe_read(dev/"name") or dev.name
            found = True
            print(f"\n    {C.BOLD}{C.MAG}{name}{C.RST}  [{dev.name}]")
            for pat, label in [
                ("in_accel_*_raw",       "Akselerometer"),
                ("in_anglvel_*_raw",     "Giroskop"),
                ("in_magn_*_raw",        "Magnetometer"),
                ("in_proximity_raw",     "Proximity"),
                ("in_illuminance_raw",   "Cahaya"),
                ("in_pressure_raw",      "Tekanan"),
                ("in_temp_raw",          "Suhu"),
            ]:
                try:
                    files = list(dev.glob(pat))
                    if not files: continue
                    vals = [f"{f.stem.split('_')[-2] if '_' in f.stem else f.stem}={safe_read(f)}"
                            for f in sorted(files)[:3] if safe_read(f)]
                    if vals:
                        scale = 1.0
                        try:
                            sf = list(dev.glob(pat.replace("_raw","_scale")))
                            if sf:
                                sv = safe_read(sf[0])
                                if sv: scale = safe_float(sv, 1.0)
                        except Exception: pass
                        row(f"  {label}", ", ".join(vals) + f"  (×{scale})")
                except Exception: continue
            sf = safe_read(dev/"sampling_frequency")
            if sf: row("  Sampling Hz", sf)

    # Input devices yang adalah sensor
    sec("Input Sensor Devices (/sys/class/input):")
    sensor_keywords = ("accel","gyro","magnet","sensor","compass","baro",
                       "prox","light","hall","gesture","orientation")
    found_input = False
    for inp in safe_iterdir("/sys/class/input"):
        name = safe_read(inp/"device/name") or safe_read(inp/"name") or ""
        if not name: continue
        if not any(k in name.lower() for k in sensor_keywords): continue
        phys = safe_read(inp/"device/phys") or "—"
        row(f"  {name}", phys)
        found_input = True; found = True

    if not found_input:
        info("Tidak ada sensor terdeteksi via /sys/class/input")

    if not found:
        warn("Sensor tidak bisa diakses langsung tanpa root di Android 10+.")
        info("Gunakan: CPU-Z, Sensor Kinetics, atau Physics Toolbox Sensor Suite")
        info("untuk membaca sensor via Android API.")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 18 — ANDROID LANJUT
# ══════════════════════════════════════════════════════════════════════════════
def fitur_android_lanjut():
    hdr("FITUR 18 · INFO ANDROID LANJUT", "🤖")

    # dumpsys battery
    sec("Baterai (dumpsys battery):")
    bat_out = run_cmd(["dumpsys","battery"], timeout=6)
    if bat_out:
        for ln in bat_out.split("\n"):
            if ":" in ln and ln.strip():
                k, _, v = ln.partition(":")
                row(k.strip()[:28], v.strip()[:50])
    else:
        info("dumpsys battery tidak tersedia.")

    # Package manager
    sec("Package Manager (pm):")
    all_pkg  = run_cmd(["pm","list","packages"],      timeout=12)
    user_pkg = run_cmd(["pm","list","packages","-3"], timeout=12)
    sys_pkg  = run_cmd(["pm","list","packages","-s"], timeout=12)
    dis_pkg  = run_cmd(["pm","list","packages","-d"], timeout=12)

    if all_pkg:
        all_c  = len([l for l in all_pkg.split("\n") if l.strip()])
        usr_c  = len([l for l in user_pkg.split("\n") if l.strip()]) if user_pkg else 0
        sys_c  = len([l for l in sys_pkg.split("\n")  if l.strip()]) if sys_pkg  else 0
        dis_c  = len([l for l in dis_pkg.split("\n")  if l.strip()]) if dis_pkg  else 0
        row("Total Paket",    all_c)
        row("Sistem",         sys_c)
        row("User/Install",   usr_c)
        row("Dinonaktifkan",  dis_c)
        if user_pkg:
            sec("Aplikasi User (maks 20):")
            for ln in sorted(user_pkg.split("\n"))[:20]:
                pkg = ln.replace("package:","").strip()
                if pkg: print(f"    {C.CYN}· {pkg}{C.RST}")
            if usr_c > 20:
                print(f"    {C.GRY}... dan {usr_c-20} lainnya{C.RST}")
    else:
        info("pm tidak tersedia atau butuh permission.")

    # Display
    sec("Display (wm):")
    wm_size  = run_cmd(["wm","size"],    timeout=4)
    wm_dens  = run_cmd(["wm","density"], timeout=4)
    if wm_size: row("Resolusi",  wm_size.replace("Physical size: ",""))
    if wm_dens: row("Density",   wm_dens.replace("Physical density: ","") + " dpi")
    # Fallback dari getprop
    dpi = getprop("ro.sf.lcd_density")
    if dpi and not wm_dens: row("Density (getprop)", f"{dpi} dpi")

    # Getprop lanjut
    sec("Android Properties Lanjut (getprop):")
    adv_props = [
        ("ro.product.first_api_level",   "First API Level"),
        ("ro.crypto.type",               "Enkripsi"),
        ("ro.crypto.state",              "Status Enkripsi"),
        ("ro.secure",                    "Secure Boot"),
        ("ro.debuggable",                "Debuggable"),
        ("ro.adb.secure",                "ADB Secure"),
        ("sys.usb.state",                "USB State"),
        ("persist.sys.timezone",         "Timezone"),
        ("persist.sys.language",         "Bahasa"),
        ("ro.opengles.version",          "OpenGL ES (raw)"),
        ("dalvik.vm.heapsize",           "Dalvik VM Heap Max"),
        ("dalvik.vm.heapgrowthlimit",    "Heap Growth Limit"),
        ("ro.dalvik.vm.native.bridge",   "Native Bridge"),
        ("ro.build.selinux",             "SELinux"),
        ("ro.product.first_api_level",   "First API Level"),
        ("persist.vendor.radio.rat_on",  "Radio RAT"),
        ("gsm.operator.alpha",           "Operator (SIM1)"),
        ("gsm.operator.alpha.2",         "Operator (SIM2)"),
        ("gsm.network.type",             "Tipe Jaringan"),
    ]
    for key, label in adv_props:
        val = getprop(key)
        if val: row(label, val[:60])

    # Settings system
    sec("Settings System:")
    settings_items = [
        ("screen_brightness",      "Kecerahan Layar"),
        ("screen_off_timeout",     "Timeout Layar"),
        ("accelerometer_rotation", "Rotasi Otomatis"),
        ("sound_effects_enabled",  "Efek Suara"),
        ("ringtone",               "Nada Dering"),
        ("volume_ring",            "Volume Ring"),
        ("volume_music",           "Volume Media"),
    ]
    for key, label in settings_items:
        val = run_cmd(["settings","get","system",key], timeout=3)
        if val and val != "null": row(label, val)


# ══════════════════════════════════════════════════════════════════════════════
# MENU UTAMA
# ══════════════════════════════════════════════════════════════════════════════
MENU = [
    ("1",  "🖥️   Info CPU (core, freq, governor, load avg)",          fitur_cpu),
    ("2",  "💾   Info RAM (meminfo, swap, zRAM)",                     fitur_ram),
    ("3",  "💿   Info Storage (mount, df, space)",                    fitur_storage),
    ("4",  "🔋   Info Baterai (tegangan, arus, health, siklus)",      fitur_baterai),
    ("5",  "🌡️   Suhu Hardware (thermal zones, baterai)",             fitur_suhu),
    ("6",  "🌐   Info Jaringan (IP, statistik, latensi TCP)",         fitur_network),
    ("7",  "📱   Info Sistem & OS (getprop Android lengkap)",         fitur_os),
    ("8",  "⚙️   Proses Aktif (top / ps — Android 10+ compatible)",  fitur_proses),
    ("9",  "📡   Kecepatan Jaringan + uji download real",             fitur_netspeed),
    ("10", "⚡   Benchmark CPU (4 tes pure Python)",                  fitur_benchmark),
    ("11", "📊   Monitor Real-time (CPU+RAM+Suhu+Net live)",          fitur_monitor),
    ("12", "📋   Laporan Lengkap (Export JSON + TXT)",                fitur_laporan),
    ("13", "🎮   Info GPU (getprop + devfreq — tanpa root)",          fitur_gpu),
    ("14", "📶   WiFi Detail (interface + getprop + dumpsys)",        fitur_wifi),
    ("15", "🔧   Kernel & Parameter Sistem",                          fitur_kernel),
    ("16", "🧮   Virtual Memory Stats (/proc/vmstat)",                fitur_vmstat),
    ("17", "🧭   Sensor Hardware (dumpsys + IIO + input)",            fitur_sensor),
    ("18", "🤖   Android Lanjut (pm, wm, settings, getprop++)",      fitur_android_lanjut),
]

def show_menu():
    print(f"\n{C.BOLD}{C.MAG}{'═'*68}{C.RST}")
    print(f"  {C.BOLD}{C.WHT}   CEK HARDWARE ANDROID v3.0  ·  ZERO DEPENDENCY{C.RST}")
    print(f"  {C.DIM}{C.GRY}   Support Android 10+ · Tanpa root · Tanpa psutil{C.RST}")
    print(f"{C.BOLD}{C.MAG}{'═'*68}{C.RST}")
    for k, label, _ in MENU:
        print(f"  {C.CYN}{k:>3}{C.RST}  {label}")
    print(f"\n  {C.BOLD}{C.GRN}    0{C.RST}  🚀 Jalankan Semua 18 Fitur")
    print(f"  {C.RED}    q{C.RST}  ❌ Keluar")
    print(f"{C.BOLD}{C.MAG}{'─'*68}{C.RST}")

def main():
    fmap = {k: fn for k, _, fn in MENU}
    while True:
        show_menu()
        try:
            ch = input(f"\n  {C.BOLD}Pilih [1-18 / 0=semua / q=keluar]{C.RST}: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {C.GRN}Sampai jumpa! 👋{C.RST}\n"); break

        if ch in ("q","quit","exit","keluar"):
            print(f"\n  {C.GRN}Sampai jumpa! 👋{C.RST}\n"); break
        elif ch == "0":
            for k, label, fn in MENU:
                print(f"\n  {C.GRY}▶ {label}{C.RST}")
                try:    fn()
                except Exception as e:
                    print(f"  {C.RED}Error di {label}: {type(e).__name__}: {e}{C.RST}")
        elif ch in fmap:
            try:    fmap[ch]()
            except Exception as e:
                print(f"\n  {C.RED}Error: {type(e).__name__}: {e}{C.RST}")
        else:
            print(f"\n  {C.RED}⚠  Masukkan 1-18, 0, atau q{C.RST}")

        try:    input(f"\n  {C.GRY}[Tekan Enter untuk kembali ke menu...]{C.RST}")
        except (KeyboardInterrupt, EOFError): break

if __name__ == "__main__":
    main()
