"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        CEK HARDWARE — VERSI ANDROID v2.0  (Zero Dependency)                 ║
║   Baca langsung dari /proc & /sys — tanpa psutil, tanpa library eksternal   ║
║   Jalankan : python3 cek_hardware_android.py                                 ║
║   GitHub   : https://github.com/                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

FITUR (18 total):
  1  · Info CPU           9  · Kecepatan Jaringan Real-time
  2  · Info RAM           10 · Benchmark CPU (4 tes)
  3  · Info Storage       11 · Monitor Real-time (live chart)
  4  · Info Baterai       12 · Laporan Lengkap (Export JSON+TXT)
  5  · Suhu Hardware      13 · Info GPU (Adreno/Mali/DevFreq)
  6  · Info Jaringan      14 · WiFi Detail (signal, channel, AP)
  7  · Info Sistem & OS   15 · Kernel & Modul
  8  · Proses Aktif       16 · Virtual Memory Stats (/proc/vmstat)
                          17 · Sensor IIO / Hardware Sensor
                          18 · Android Lanjut (dumpsys, paket, dll)
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
    print(f"    {C.GRY}{label:<{w}}{C.RST}{C.WHT}{value}{C.RST}")

def sec(label):
    print(f"\n    {C.BOLD}{C.YLW}▸ {label}{C.RST}")

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

def read(path, default=""):
    try:    return Path(path).read_text().strip()
    except: return default

def run(cmd, timeout=5):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL,
               timeout=timeout).decode(errors="replace").strip()
    except: return ""

def na(val):
    """Kembalikan '—' jika kosong."""
    return val if val else "—"


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 1 — CPU (/proc/cpuinfo + /proc/stat)
# ══════════════════════════════════════════════════════════════════════════════
def _parse_cpuinfo():
    info = {}
    try:
        text = Path("/proc/cpuinfo").read_text()
        for ln in text.split("\n"):
            if ":" in ln:
                k, v = ln.split(":", 1)
                k = k.strip(); v = v.strip()
                if k not in info:
                    info[k] = v
    except: pass
    return info

def _cpu_usage(interval=1.0):
    def read_stat():
        try:
            line = Path("/proc/stat").read_text().split("\n")[0]
            vals = list(map(int, line.split()[1:]))
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            total = sum(vals)
            return idle, total
        except: return 0, 1
    i1, t1 = read_stat(); time.sleep(interval); i2, t2 = read_stat()
    return 100.0 * (1 - (i2 - i1) / ((t2 - t1) or 1))

def _cpu_freq_mhz():
    f = read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    if f.isdigit(): return int(f) / 1000
    info = _parse_cpuinfo()
    mhz  = info.get("cpu MHz","")
    try:   return float(mhz)
    except: return None

def _n_cores():
    try:
        return len([l for l in Path("/proc/cpuinfo").read_text().split("\n")
                    if l.startswith("processor")])
    except: return 0

def fitur_cpu():
    hdr("FITUR 1 · INFO CPU", "🖥️")
    info    = _parse_cpuinfo()
    n_cores = _n_cores()

    row("Model CPU",       na(info.get("model name", info.get("Hardware",""))))
    row("Implementasi",    na(info.get("CPU implementer","")))
    row("Arsitektur",      na(info.get("CPU architecture", platform.machine())))
    row("Varian",          na(info.get("CPU variant","")))
    row("Part",            na(info.get("CPU part","")))
    row("Revision",        na(info.get("CPU revision","")))
    row("Jumlah Core",     n_cores or "?")
    row("BogoMIPS",        na(info.get("BogoMIPS","")))
    row("Fitur CPU",       (info.get("Features","—"))[:60])

    freq = _cpu_freq_mhz()
    if freq: row("Frekuensi Saat Ini", f"{freq:.0f} MHz  ({freq/1000:.2f} GHz)")

    fmax = read("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
    fmin = read("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq")
    if fmax.isdigit(): row("Frekuensi Maks", f"{int(fmax)//1000} MHz")
    if fmin.isdigit(): row("Frekuensi Min",  f"{int(fmin)//1000} MHz")

    gov = read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    if gov: row("Governor", gov)

    sec("Load Average:")
    la = read("/proc/loadavg").split()
    if la: row("1 / 5 / 15 menit", f"{la[0]}  {la[1]}  {la[2]}")

    sec("Penggunaan CPU (diukur 1 detik):")
    print(f"    {C.GRY}Mengukur...{C.RST}", end="", flush=True)
    usage = _cpu_usage(1.0)
    print(f"\r{' '*22}\r", end="")
    print(f"    {bar(usage)}")

    sec("Frekuensi Per Core:")
    for i in range(min(n_cores or 0, 8)):
        f = read(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_cur_freq")
        if f.isdigit():
            mhz = int(f) / 1000
            max_f = read(f"/sys/devices/system/cpu/cpu{i}/cpufreq/cpuinfo_max_freq")
            max_mhz = f"/ maks {int(max_f)//1000} MHz" if max_f.isdigit() else ""
            print(f"    Core {i}  {mhz:.0f} MHz  {max_mhz}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 2 — RAM (/proc/meminfo)
# ══════════════════════════════════════════════════════════════════════════════
def _parse_meminfo():
    d = {}
    try:
        for ln in Path("/proc/meminfo").read_text().split("\n"):
            if ":" in ln:
                k, v = ln.split(":", 1)
                nums = re.findall(r"\d+", v)
                d[k.strip()] = int(nums[0]) * 1024 if nums else 0
    except: pass
    return d

def fitur_ram():
    hdr("FITUR 2 · INFO RAM / MEMORI", "💾")
    m = _parse_meminfo()
    if not m:
        print(f"    {C.YLW}⚠  /proc/meminfo tidak bisa dibaca.{C.RST}"); return

    total     = m.get("MemTotal", 0)
    free      = m.get("MemFree",  0)
    avail     = m.get("MemAvailable", free)
    buffers   = m.get("Buffers", 0)
    cached    = m.get("Cached",  0) + m.get("SReclaimable", 0)
    used      = total - free - buffers - cached
    swap_tot  = m.get("SwapTotal", 0)
    swap_free = m.get("SwapFree",  0)
    swap_used = swap_tot - swap_free
    pct       = (used / total * 100) if total else 0

    row("Total RAM",      b2h(total))
    row("Terpakai",       b2h(max(used, 0)))
    row("Tersedia",       b2h(avail))
    row("Bebas (murni)",  b2h(free))
    row("Buffer",         b2h(buffers))
    row("Cache",          b2h(cached))
    row("Active",         b2h(m.get("Active", 0)))
    row("Inactive",       b2h(m.get("Inactive", 0)))
    print(f"\n    {bar(pct)}")

    sec("SWAP:")
    row("Total SWAP",     b2h(swap_tot))
    row("Terpakai",       b2h(swap_used))
    row("Bebas",          b2h(swap_free))
    if swap_tot:
        print(f"    {bar(swap_used / swap_tot * 100)}")
    else:
        print(f"    {C.GRY}Tidak ada SWAP.{C.RST}")

    for key in ("HugePages_Total","Hugepagesize","DirectMap4k","DirectMap2M"):
        if key in m:
            row(key, b2h(m[key]) if "size" in key.lower() or "map" in key.lower() else str(m[key]//1024))


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 3 — STORAGE (/proc/mounts + /proc/diskstats)
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

def fitur_storage():
    hdr("FITUR 3 · INFO STORAGE / PENYIMPANAN", "💿")
    mounts = read("/proc/mounts")
    seen   = set()
    for ln in mounts.split("\n"):
        parts = ln.split()
        if len(parts) < 3: continue
        dev, mpt, fs = parts[0], parts[1], parts[2]
        if fs in ("tmpfs","proc","sysfs","devtmpfs","cgroup","cgroup2",
                  "pstore","devpts","debugfs","securityfs","configfs",
                  "hugetlbfs","mqueue","fusectl","bpf","tracefs","none"): continue
        if mpt in seen: continue
        seen.add(mpt)
        res = _statvfs(mpt)
        if not res: continue
        total, used, avail, pct = res
        if total < 1024 * 1024: continue
        sec(f"{dev}  →  {mpt}  [{fs}]")
        row("Total",    b2h(total))
        row("Terpakai", b2h(used))
        row("Tersedia", b2h(avail))
        print(f"    {bar(pct)}")

    sec("Aktivitas Disk I/O (/proc/diskstats):")
    ds = read("/proc/diskstats")
    printed = False
    for ln in ds.split("\n"):
        parts = ln.split()
        if len(parts) < 14: continue
        name = parts[2]
        if re.match(r"^(sd[a-z]|mmcblk\d|nvme\d|vd[a-z])$", name):
            r_sec  = int(parts[5])  * 512
            w_sec  = int(parts[9])  * 512
            r_ms   = int(parts[6])
            w_ms   = int(parts[10])
            print(f"    {C.BOLD}{name}{C.RST}  "
                  f"Baca:{b2h(r_sec)}  Tulis:{b2h(w_sec)}  "
                  f"T-Baca:{r_ms}ms  T-Tulis:{w_ms}ms")
            printed = True
    if not printed:
        print(f"    {C.GRY}Tidak ada data /proc/diskstats.{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 4 — BATERAI (/sys/class/power_supply)
# ══════════════════════════════════════════════════════════════════════════════
def fitur_baterai():
    hdr("FITUR 4 · INFO BATERAI", "🔋")
    base = Path("/sys/class/power_supply")
    if not base.exists():
        print(f"    {C.YLW}⚠  /sys/class/power_supply tidak tersedia.{C.RST}"); return

    found = False
    for supply in sorted(base.iterdir()):
        stype = read(supply / "type")
        if stype not in ("Battery","USB","Mains") and "bat" not in supply.name.lower():
            continue

        sec(f"Supply: {supply.name}  [{stype}]")
        found = True

        cap = read(supply / "capacity")
        if cap.isdigit():
            pct = float(cap)
            row("Persentase",  f"{pct:.0f}%")
            print(f"\n    {bar(pct)}\n")

        status = read(supply / "status")
        if status:
            col = C.GRN if status == "Charging" else C.YLW if status == "Discharging" else C.GRY
            row("Status",      f"{col}{status}{C.RST}")

        for fname, label in [
            ("voltage_now",        "Tegangan (µV)"),
            ("voltage_max_design", "Tegangan Desain (µV)"),
            ("current_now",        "Arus Sekarang (µA)"),
            ("charge_now",         "Charge Sekarang (µAh)"),
            ("charge_full",        "Charge Penuh (µAh)"),
            ("charge_full_design", "Charge Desain (µAh)"),
            ("energy_now",         "Energi Sekarang (µWh)"),
            ("energy_full",        "Energi Penuh (µWh)"),
            ("energy_full_design", "Energi Desain (µWh)"),
            ("cycle_count",        "Siklus Charge"),
            ("health",             "Kondisi"),
            ("technology",         "Teknologi"),
            ("manufacturer",       "Produsen"),
            ("model_name",         "Model"),
            ("serial_number",      "Serial"),
            ("temp",               "Suhu Baterai"),
        ]:
            val = read(supply / fname)
            if val:
                if fname == "temp" and val.lstrip("-").isdigit():
                    val = f"{int(val)/10:.1f}°C"
                elif fname in ("charge_full","charge_now") and val.isdigit():
                    val = f"{int(val)//1000} mAh ({val} µAh)"
                elif fname in ("energy_now","energy_full") and val.isdigit():
                    val = f"{int(val)//1000} mWh"
                elif fname in ("voltage_now","voltage_max_design") and val.lstrip("-").isdigit():
                    val = f"{int(val)/1000000:.3f} V  ({val} µV)"
                row(label, val)

        cf = read(supply / "charge_full")
        cn = read(supply / "charge_now")
        if cf.isdigit() and cn.isdigit() and int(cf):
            health_pct = int(cn) / int(cf) * 100
            row("Health Baterai", f"{health_pct:.1f}%")

    if not found:
        print(f"    {C.GRY}Tidak ada supply baterai terdeteksi.{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 5 — SUHU (/sys/class/thermal)
# ══════════════════════════════════════════════════════════════════════════════
def fitur_suhu():
    hdr("FITUR 5 · SUHU HARDWARE", "🌡️")
    thermal = Path("/sys/class/thermal")
    if not thermal.exists():
        print(f"    {C.YLW}⚠  /sys/class/thermal tidak tersedia.{C.RST}"); return

    found = False
    for zone in sorted(thermal.iterdir()):
        temp_f = zone / "temp"
        type_f = zone / "type"
        if not temp_f.exists(): continue
        try:
            temp_raw  = int(read(temp_f))
            zone_type = read(type_f) or zone.name
            temp_c    = temp_raw / 1000 if temp_raw > 200 else float(temp_raw)
            st = (f"{C.RED}⚠ KRITIS{C.RST}" if temp_c >= 80
                  else f"{C.YLW}⚡ Panas{C.RST}" if temp_c >= 55
                  else f"{C.GRN}✓ Normal{C.RST}")
            print(f"    {zone_type:<30} {C.BOLD}{temp_c:>6.1f}°C{C.RST}  [{st}]")
            found = True
        except: pass

    if not found:
        print(f"    {C.GRY}Tidak ada sensor thermal terdeteksi.{C.RST}")

    hwmon = Path("/sys/class/hwmon")
    if hwmon.exists():
        sec("hwmon sensors:")
        for hw in sorted(hwmon.iterdir()):
            name = read(hw / "name") or hw.name
            for tf in sorted(hw.glob("temp*_input")):
                try:
                    t = int(read(tf)) / 1000
                    label_f = hw / tf.name.replace("input","label")
                    label   = read(label_f) or tf.name
                    print(f"    {name}/{label:<26} {t:>6.1f}°C")
                except: pass


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 6 — JARINGAN (/proc/net/dev)
# ══════════════════════════════════════════════════════════════════════════════
def _parse_net_dev():
    result = {}
    try:
        lines = Path("/proc/net/dev").read_text().split("\n")[2:]
        for ln in lines:
            if ":" not in ln: continue
            iface, data = ln.split(":", 1)
            vals = data.split()
            if len(vals) >= 16:
                result[iface.strip()] = {
                    "rx_bytes":   int(vals[0]),  "rx_packets": int(vals[1]),
                    "rx_errs":    int(vals[2]),  "rx_drop":    int(vals[3]),
                    "tx_bytes":   int(vals[8]),  "tx_packets": int(vals[9]),
                    "tx_errs":    int(vals[10]), "tx_drop":    int(vals[11]),
                }
    except: pass
    return result

def _get_ip(iface):
    try:
        import fcntl, struct
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(), 0x8915,
            struct.pack("256s", iface[:15].encode()))[20:24])
    except: return ""

def fitur_network():
    hdr("FITUR 6 · INFO JARINGAN", "🌐")

    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        row("Hostname",  hostname)
        row("IP Lokal",  local_ip)
    except: pass

    try:
        import urllib.request
        pub = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
        row("IP Publik", pub)
    except:
        row("IP Publik", "Timeout / tidak tersambung")

    net = _parse_net_dev()
    sec("Interface Jaringan:")
    for iface, d in sorted(net.items()):
        if d["rx_bytes"] == 0 and d["tx_bytes"] == 0: continue
        ip   = _get_ip(iface)
        oper = read(f"/sys/class/net/{iface}/operstate")
        col  = C.GRN if oper == "up" else C.RED
        spd  = read(f"/sys/class/net/{iface}/speed")
        spd_str = f"  {spd} Mbps" if spd and spd not in ("-1","") else ""
        print(f"\n    {C.BOLD}{iface}{C.RST}  [{col}{oper or '?'}{C.RST}]{spd_str}")
        if ip: row("  IP",        ip)
        mac = read(f"/sys/class/net/{iface}/address")
        if mac: row("  MAC",      mac)
        row("  ⬇ Diterima", f"{b2h(d['rx_bytes'])}  ({d['rx_packets']:,} paket, {d['rx_errs']} err)")
        row("  ⬆ Dikirim",  f"{b2h(d['tx_bytes'])}  ({d['tx_packets']:,} paket, {d['tx_errs']} err)")

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
        except:
            print(f"    {C.RED}✗{C.RST}  {name:<22} {C.RED}Gagal{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 7 — INFO SISTEM & OS
# ══════════════════════════════════════════════════════════════════════════════
def fitur_os():
    hdr("FITUR 7 · INFO SISTEM OPERASI", "📱")
    uname = platform.uname()
    row("Sistem",        uname.system)
    row("Node",          uname.node)
    row("Kernel",        uname.release)
    row("Versi Kernel",  uname.version[:72])
    row("Mesin",         uname.machine)
    row("Python",        platform.python_version())

    sec("Android Properties (getprop):")
    props = {
        "ro.product.brand":         "Brand",
        "ro.product.model":         "Model HP",
        "ro.product.name":          "Nama Produk",
        "ro.product.device":        "Device",
        "ro.build.version.release": "Android Version",
        "ro.build.version.sdk":     "SDK Level",
        "ro.build.id":              "Build ID",
        "ro.build.type":            "Build Type",
        "ro.build.date":            "Tanggal Build",
        "ro.build.fingerprint":     "Fingerprint",
        "ro.product.cpu.abi":       "CPU ABI",
        "ro.product.cpu.abilist":   "ABI List",
        "ro.hardware":              "Hardware",
        "ro.board.platform":        "Platform Board",
        "ro.product.manufacturer":  "Produsen",
        "ro.serialno":              "Serial Number",
    }
    any_prop = False
    for key, label in props.items():
        val = run(["getprop", key])
        if val:
            row(label, val[:70])
            any_prop = True
    if not any_prop:
        print(f"    {C.GRY}getprop tidak tersedia (bukan Android / tidak ada akses){C.RST}")

    if Path("/etc/os-release").exists():
        sec("OS Release:")
        for ln in Path("/etc/os-release").read_text().split("\n"):
            if "=" in ln:
                k, v = ln.split("=", 1)
                if k in ("PRETTY_NAME","NAME","VERSION","ID"):
                    row(k, v.strip('"'))

    sec("Uptime:")
    up_raw = read("/proc/uptime").split()
    if up_raw:
        up_s = float(up_raw[0])
        h, r = divmod(int(up_s), 3600); m, s = divmod(r, 60)
        row("Uptime", f"{h} jam  {m} menit  {s} detik")
    if len(up_raw) > 1:
        idle_s = float(up_raw[1])
        row("CPU Idle Total", f"{idle_s/3600:.1f} jam (akumulasi semua core)")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 8 — PROSES AKTIF (/proc)
# ══════════════════════════════════════════════════════════════════════════════
def _cpu_times_proc(pid):
    try:
        parts = Path(f"/proc/{pid}/stat").read_text().split()
        return int(parts[13]) + int(parts[14])
    except: return 0

def fitur_proses():
    hdr("FITUR 8 · PROSES AKTIF (TOP 15 CPU)", "⚙️")
    m = _parse_meminfo()
    total_mem = m.get("MemTotal", 1)
    clk = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100

    snap1 = {}
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit(): continue
        snap1[pid_dir.name] = _cpu_times_proc(pid_dir.name)

    print(f"    {C.GRY}Mengukur 1 detik...{C.RST}", end="", flush=True)
    time.sleep(1)
    print(f"\r{' '*25}\r", end="")

    hasil = []
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit(): continue
        pid = pid_dir.name
        t2  = _cpu_times_proc(pid)
        t1  = snap1.get(pid, t2)
        cpu_pct = (t2 - t1) / clk * 100

        try:   name = (pid_dir/"comm").read_text().strip()
        except: name = "?"

        mem_kb = 0
        try:
            for ln in (pid_dir/"status").read_text().split("\n"):
                if ln.startswith("VmRSS:"):
                    nums = re.findall(r"\d+", ln)
                    mem_kb = int(nums[0]) if nums else 0; break
        except: pass

        status = ""
        try:
            for ln in (pid_dir/"status").read_text().split("\n"):
                if ln.startswith("State:"):
                    status = ln.split(":",1)[1].strip()[:8]; break
        except: pass

        hasil.append({"pid":pid,"name":name,"cpu":cpu_pct,
                      "mem_kb":mem_kb,"mem_pct":mem_kb*1024/total_mem*100,"status":status})

    top = sorted(hasil, key=lambda x: x["cpu"], reverse=True)[:15]
    print(f"\n    {'PID':<8}{'Nama':<22}{'CPU%':>7}{'RAM':>10}{'RAM%':>7}  Status")
    print(f"    {'─'*66}")
    for p in top:
        cc = C.RED if p["cpu"] > 50 else C.YLW if p["cpu"] > 20 else C.GRN
        print(f"    {C.GRY}{p['pid']:<8}{C.RST}"
              f"{p['name']:<22}"
              f"{cc}{p['cpu']:>6.1f}%{C.RST}"
              f"{C.CYN}{b2h(p['mem_kb']*1024):>10}{C.RST}"
              f"{p['mem_pct']:>6.1f}%"
              f"  {C.GRY}{p['status']}{C.RST}")

    sec("Jumlah Proses:")
    all_pids = [d for d in Path("/proc").iterdir() if d.name.isdigit()]
    row("Total Proses",  len(all_pids))
    row("Max Thread",    na(read("/proc/sys/kernel/threads-max")))


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 9 — KECEPATAN JARINGAN REAL-TIME
# ══════════════════════════════════════════════════════════════════════════════
def fitur_netspeed():
    hdr("FITUR 9 · KECEPATAN JARINGAN REAL-TIME", "📡")

    def total_bytes():
        rx = tx = 0
        for iface, d in _parse_net_dev().items():
            if iface == "lo": continue
            rx += d["rx_bytes"]; tx += d["tx_bytes"]
        return rx, tx

    print(f"    {C.GRY}Mengukur 3 detik...{C.RST}", end="", flush=True)
    r1, t1 = total_bytes(); time.sleep(3); r2, t2 = total_bytes()
    print(f"\r{' '*30}\r", end="")

    dl = (r2-r1)/3; ul = (t2-t1)/3
    row("⬇ Download (real-time)", f"{b2h(dl)}/s  ({dl*8/1e6:.3f} Mbps)")
    row("⬆ Upload   (real-time)", f"{b2h(ul)}/s  ({ul*8/1e6:.3f} Mbps)")

    sec("Uji Download Nyata (1 MB dari Cloudflare):")
    try:
        import urllib.request as ur
        t0   = time.perf_counter()
        data = ur.urlopen("https://speed.cloudflare.com/__down?bytes=1048576", timeout=20).read()
        secs = time.perf_counter() - t0
        row("Ukuran",     b2h(len(data)))
        row("Waktu",      f"{secs:.2f} detik")
        row("Throughput", f"{b2h(len(data)/secs)}/s  ({len(data)*8/secs/1e6:.2f} Mbps)")
    except Exception as e:
        row("Uji Download", f"Gagal — {e}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 10 — BENCHMARK CPU (PURE PYTHON)
# ══════════════════════════════════════════════════════════════════════════════
def fitur_benchmark():
    hdr("FITUR 10 · BENCHMARK CPU (Pure Python)", "⚡")
    import math, threading

    sec("Tes 1: Kalkulasi π (5 juta iterasi Leibniz):")
    print(f"    {C.GRY}Menghitung...{C.RST}", end="", flush=True)
    t0 = time.perf_counter()
    pi, sign = 0.0, 1
    for i in range(5_000_000):
        pi += sign / (2*i+1); sign = -sign
    pi *= 4
    s = time.perf_counter() - t0
    print(f"\r{' '*25}\r", end="")
    row("Nilai π",    f"{pi:.10f}")
    row("Waktu",      f"{s:.3f} detik")
    row("Kecepatan",  f"{5_000_000/s/1e6:.2f} juta iter/detik")

    sec("Tes 2: Float ops (sin/cos/sqrt, 500 ribu iterasi):")
    print(f"    {C.GRY}Menghitung...{C.RST}", end="", flush=True)
    t0 = time.perf_counter()
    acc = 0.0
    for i in range(1, 500_001):
        acc += math.sin(i) * math.cos(i) + math.sqrt(i)
    s = time.perf_counter() - t0
    print(f"\r{' '*25}\r", end="")
    row("Waktu",     f"{s:.3f} detik")
    row("Kecepatan", f"{500_000/s/1e6:.2f} juta op/detik")

    n_t = min(max(_n_cores() or 1, 1), 4)
    sec(f"Tes 3: Multi-thread ({n_t} thread, 2 juta iter/thread):")
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
    row("Thread",         n_t)
    row("Total Operasi",  f"{total_ops:,}")
    row("Waktu",          f"{s:.3f} detik")
    row("Throughput",     f"{total_ops/s/1e6:.2f} juta op/detik")

    sec("Tes 4: Memori bandwidth (alokasi + write 30 MB):")
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
    print(f"    {C.GRY}Tekan Ctrl+C untuk berhenti lebih awal.{C.RST}\n")

    def get_cpu_stat():
        try:
            vals = list(map(int, Path("/proc/stat").read_text().split("\n")[0].split()[1:]))
            idle = vals[3] + (vals[4] if len(vals)>4 else 0)
            return idle, sum(vals)
        except: return 0, 1

    def get_net():
        rx = tx = 0
        for iface, d in _parse_net_dev().items():
            if iface!="lo": rx+=d["rx_bytes"]; tx+=d["tx_bytes"]
        return rx, tx

    ci, ct = get_cpu_stat()
    nr, nt = get_net()

    print(f"    {C.BOLD}{'Dtk':>4}  {'CPU%':>7}  {'RAM%':>7}  {'Net⬇/s':>12}  {'Net⬆/s':>12}{C.RST}")
    print(f"    {'─'*58}")
    try:
        for tick in range(1, 11):
            time.sleep(1)
            ci2, ct2 = get_cpu_stat()
            dt = (ct2-ct) or 1
            cpu = 100*(1-(ci2-ci)/dt)
            ci, ct = ci2, ct2

            m = _parse_meminfo()
            total = m.get("MemTotal",1); free=m.get("MemFree",1)
            buf   = m.get("Buffers",0); cach=m.get("Cached",0)+m.get("SReclaimable",0)
            avail = m.get("MemAvailable", free)
            used  = total-free-buf-cach
            ram   = used/total*100 if total else 0

            nr2, nt2 = get_net()
            dl = nr2-nr; ul = nt2-nt
            nr, nt = nr2, nt2

            cc = C.RED if cpu>80 else C.YLW if cpu>50 else C.GRN
            rc = C.RED if ram>80 else C.YLW if ram>60 else C.GRN
            print(f"    {C.GRY}{tick:>4}{C.RST}"
                  f"  {cc}{cpu:>6.1f}%{C.RST}"
                  f"  {rc}{ram:>6.1f}%{C.RST}"
                  f"  {C.CYN}{b2h(dl):>12}{C.RST}"
                  f"  {C.CYN}{b2h(ul):>12}{C.RST}")
    except KeyboardInterrupt:
        print(f"\n    {C.GRY}Monitor dihentikan.{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 12 — EXPORT LAPORAN JSON + TXT
# ══════════════════════════════════════════════════════════════════════════════
def fitur_laporan():
    hdr("FITUR 12 · LAPORAN LENGKAP (Export JSON + TXT)", "📋")

    m   = _parse_meminfo()
    net = _parse_net_dev()
    up  = float(read("/proc/uptime").split()[0]) if read("/proc/uptime").split() else 0

    bat_data = {}
    for sup in (Path("/sys/class/power_supply").iterdir()
                if Path("/sys/class/power_supply").exists() else []):
        cap = read(sup/"capacity"); status = read(sup/"status")
        if cap: bat_data[sup.name] = {"capacity": cap, "status": status}

    cpuinfo = _parse_cpuinfo()
    n_cores = _n_cores()

    android = {}
    for key in ["ro.product.model","ro.product.brand","ro.build.version.release",
                "ro.build.version.sdk","ro.product.manufacturer"]:
        val = run(["getprop", key])
        if val: android[key] = val

    storage = []
    seen = set()
    for ln in read("/proc/mounts").split("\n"):
        parts = ln.split()
        if len(parts)<3: continue
        dev,mpt,fs = parts[0],parts[1],parts[2]
        if fs in ("tmpfs","proc","sysfs","devtmpfs","cgroup","devpts"): continue
        if mpt in seen: continue
        seen.add(mpt)
        res = _statvfs(mpt)
        if res and res[0] > 1024*1024:
            storage.append({"device":dev,"mountpoint":mpt,"filesystem":fs,
                            "total":res[0],"used":res[1],"free":res[2],"pct":round(res[3],2)})

    # Thermal
    thermals = []
    for zone in sorted(Path("/sys/class/thermal").iterdir()) if Path("/sys/class/thermal").exists() else []:
        temp_raw_s = read(zone/"temp")
        if temp_raw_s.lstrip("-").isdigit():
            temp_raw = int(temp_raw_s)
            temp_c   = temp_raw/1000 if temp_raw > 200 else float(temp_raw)
            thermals.append({"zone": read(zone/"type") or zone.name, "temp_c": round(temp_c,1)})

    laporan = {
        "meta":     {"waktu": datetime.datetime.now().isoformat(),
                     "versi": "android-v2.0", "python": platform.python_version()},
        "android":  android,
        "sistem":   {"os":platform.system(),"kernel":platform.release(),
                     "mesin":platform.machine(),"hostname":platform.node(),
                     "uptime_detik":int(up)},
        "cpu":      {"model":cpuinfo.get("model name",cpuinfo.get("Hardware","?")),
                     "core":n_cores,"load_avg":read("/proc/loadavg").split()[:3]},
        "ram":      {"total":m.get("MemTotal",0),"used":m.get("MemTotal",0)-m.get("MemFree",0),
                     "available":m.get("MemAvailable",0),"swap_total":m.get("SwapTotal",0)},
        "storage":  storage,
        "baterai":  bat_data,
        "jaringan": {iface:{"rx":d["rx_bytes"],"tx":d["tx_bytes"]} for iface,d in net.items()},
        "thermal":  thermals,
    }

    ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    jfile = f"laporan_{ts}.json"
    tfile = f"laporan_{ts}.txt"

    with open(jfile,"w",encoding="utf-8") as f:
        json.dump(laporan, f, ensure_ascii=False, indent=2)

    with open(tfile,"w",encoding="utf-8") as f:
        f.write(f"CEK HARDWARE ANDROID v2.0\nWaktu: {laporan['meta']['waktu']}\n{'='*52}\n")
        for k,v in android.items(): f.write(f"{k}: {v}\n")
        f.write(f"\nRAM Total  : {b2h(laporan['ram']['total'])}\n")
        f.write(f"RAM Terpakai: {b2h(laporan['ram']['used'])}\n")
        for s in storage:
            f.write(f"\nDisk {s['device']}: {b2h(s['total'])}  terpakai:{s['pct']}%\n")
        for name,bat in bat_data.items():
            f.write(f"\nBaterai {name}: {bat.get('capacity','?')}%  ({bat.get('status','?')})\n")
        for t in thermals:
            f.write(f"\nSuhu {t['zone']}: {t['temp_c']}°C\n")

    sec("File Tersimpan:")
    row("JSON", f"{jfile}  ({b2h(Path(jfile).stat().st_size)})")
    row("TXT",  f"{tfile}  ({b2h(Path(tfile).stat().st_size)})")
    print(f"\n    {C.GRN}✓  Laporan berhasil disimpan!{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 13 — INFO GPU (ADRENO / MALI / DEVFREQ)
# ══════════════════════════════════════════════════════════════════════════════
def fitur_gpu():
    hdr("FITUR 13 · INFO GPU (Adreno / Mali / DevFreq)", "🎮")
    found_any = False

    # ── Adreno: /sys/class/kgsl ──────────────────────────────────────────────
    kgsl = Path("/sys/class/kgsl")
    if kgsl.exists():
        sec("Adreno GPU (kgsl):")
        try: _kgsl_items = sorted(kgsl.iterdir())
        except PermissionError: _kgsl_items=[]; print(f"    {C.GRY}Permission denied: /sys/class/kgsl{C.RST}")
        for dev in _kgsl_items:
            found_any = True
            row("Device", dev.name)
            for fname, label, unit in [
                ("gpu_clock",           "Clock Saat Ini",   " Hz"),
                ("gpuclk",              "Clock (gpuclk)",   " Hz"),
                ("gpu_busy_percentage", "GPU Busy",         "%"),
                ("gpu_model",           "Model GPU",        ""),
                ("max_gpuclk",          "Clock Maksimum",   " Hz"),
                ("min_clock_mhz",       "Clock Min",        " MHz"),
                ("max_clock_mhz",       "Clock Maks",       " MHz"),
                ("temp",                "Suhu GPU",         " milli°C"),
                ("power_level",         "Power Level",      ""),
                ("num_pwrlevels",       "Jumlah PwrLevel",  ""),
                ("throttling",          "Throttling",       ""),
                ("perfcounter_total_busy_time", "Busy Time Total", " ms"),
            ]:
                val = read(dev / fname)
                if not val: val = read(dev / "device" / fname)
                if val:
                    if fname == "temp" and val.isdigit():
                        val = f"{int(val)/1000:.1f}°C"
                    elif fname in ("gpu_clock","gpuclk","max_gpuclk") and val.isdigit():
                        val = f"{int(val)/1e6:.0f} MHz  ({val} Hz)"
                    else:
                        val = val + unit
                    row(label, val)

    # ── Mali: /sys/class/misc/mali0 ──────────────────────────────────────────
    mali_paths = list(Path("/sys/class/misc").glob("mali*")) if Path("/sys/class/misc").exists() else []
    mali_paths += list(Path("/sys/devices").rglob("mali_gpu*"))[:2]
    if mali_paths:
        sec("Mali GPU:")
        for mp in mali_paths[:2]:
            found_any = True
            row("Path", str(mp))
            for fname, label in [("cur_freq","Frekuensi"),("utilization","Utilisasi %"),
                                  ("core_mask","Core Mask"),("mem_pool_size","Pool Memori")]:
                val = read(mp/fname)
                if val: row(label, val)

    # ── DevFreq: bisa berisi GPU, DSP, dll ───────────────────────────────────
    devfreq = Path("/sys/class/devfreq")
    if devfreq.exists():
        sec("DevFreq (GPU/DSP/Bus):")
        try: _devfreq_items = sorted(devfreq.iterdir())
        except PermissionError: _devfreq_items=[]; print(f"    {C.GRY}Permission denied: /sys/class/devfreq{C.RST}")
        for df in _devfreq_items:
            name = df.name
            # Filter hanya yg kemungkinan GPU/graphics
            if not any(k in name.lower() for k in
                       ("gpu","kgsl","mali","adreno","gfx","graphics","dpu","disp","bus")):
                continue
            found_any = True
            cur  = read(df/"cur_freq")
            mxf  = read(df/"max_freq")
            mnf  = read(df/"min_freq")
            gov  = read(df/"governor")
            avail= read(df/"available_frequencies")
            print(f"\n    {C.BOLD}{C.MAG}{name}{C.RST}")
            if cur.isdigit():  row("  Freq Saat Ini", f"{int(cur)//1000} kHz  ({int(cur)/1e6:.0f} MHz)")
            if mxf.isdigit():  row("  Freq Maks",     f"{int(mxf)//1000} kHz")
            if mnf.isdigit():  row("  Freq Min",      f"{int(mnf)//1000} kHz")
            if gov:            row("  Governor",      gov)
            if avail:          row("  Freq Tersedia", avail[:60])

    # ── DRM (Direct Rendering Manager) ───────────────────────────────────────
    drm = Path("/sys/class/drm")
    if drm.exists():
        sec("DRM / Display:")
        for card in sorted(drm.iterdir()):
            if not card.name.startswith("card"): continue
            found_any = True
            row(card.name, read(card/"device/uevent") or "—")

    if not found_any:
        print(f"    {C.GRY}Tidak ada GPU terdeteksi di /sys/class/kgsl, /sys/class/devfreq, dll.")
        print(f"    {C.GRY}Coba jalankan sebagai root untuk akses lebih lanjut.{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 14 — WIFI DETAIL (/proc/net/wireless + /sys/class/net/wlan*)
# ══════════════════════════════════════════════════════════════════════════════
def fitur_wifi():
    hdr("FITUR 14 · WiFi DETAIL", "📶")
    found = False

    # ── /proc/net/wireless ────────────────────────────────────────────────────
    wireless_raw = read("/proc/net/wireless")
    if wireless_raw:
        sec("/proc/net/wireless:")
        lines = wireless_raw.strip().split("\n")
        for ln in lines[2:]:
            if ":" not in ln: continue
            parts = ln.replace(".","").split()
            if len(parts) < 4: continue
            iface = parts[0].rstrip(":")
            found = True
            row(f"Interface",  iface)
            try:
                status = int(parts[1])
                link   = int(parts[2])
                level  = int(parts[3])
                noise  = int(parts[4]) if len(parts)>4 else 0
                row("  Status",       hex(status))
                row("  Link Quality", f"{link}/70  ({link/70*100:.0f}%)")
                row("  Signal Level", f"{level-256 if level>100 else level} dBm")
                row("  Noise Level",  f"{noise-256 if noise>100 else noise} dBm")
            except: pass

    # ── /sys/class/net/wlan* ─────────────────────────────────────────────────
    wlan_ifaces = list(Path("/sys/class/net").glob("wlan*"))
    if not wlan_ifaces:
        wlan_ifaces = list(Path("/sys/class/net").glob("wl*"))

    for wi in wlan_ifaces:
        found = True
        sec(f"Interface: {wi.name}")
        mac    = read(wi/"address")
        oper   = read(wi/"operstate")
        speed  = read(wi/"speed")
        mtu    = read(wi/"mtu")
        txq    = read(wi/"tx_queue_len")
        col    = C.GRN if oper == "up" else C.RED
        row("MAC Address",    na(mac))
        row("Status",         f"{col}{oper or '?'}{C.RST}")
        if speed and speed != "-1": row("Speed",  f"{speed} Mbps")
        if mtu:  row("MTU",          mtu)
        if txq:  row("TX Queue Len", txq)

        # Baca uevent untuk lebih banyak info
        ue = read(wi/"uevent")
        for ln in ue.split("\n"):
            if "=" in ln:
                k, v = ln.split("=",1)
                if k in ("INTERFACE","DEVTYPE","DRIVER"): row(f"  {k}", v)

        # IP Address via proc/net/fib_trie atau fcntl
        ip = _get_ip(wi.name)
        if ip: row("IP Address", ip)

    # ── iwconfig / iw ─────────────────────────────────────────────────────────
    sec("iwconfig / iw output:")
    for cmd in [["iwconfig"], ["iw","dev"]]:
        out = run(cmd, timeout=4)
        if out:
            for ln in out.split("\n")[:20]:
                if ln.strip():
                    print(f"    {C.GRY}{ln}{C.RST}")
            found = True
            break

    # ── getprop WiFi ─────────────────────────────────────────────────────────
    sec("Android WiFi Properties:")
    wifi_props = {
        "wifi.interface":          "WiFi Interface",
        "wifi.direct.interface":   "WiFi Direct",
        "ro.wifi.channels":        "Channels",
        "wlan.driver.status":      "Driver Status",
        "init.svc.wpa_supplicant": "WPA Supplicant",
    }
    got_prop = False
    for key, label in wifi_props.items():
        val = run(["getprop", key])
        if val:
            row(label, val)
            got_prop = True
    if not got_prop:
        print(f"    {C.GRY}getprop tidak tersedia.{C.RST}")

    if not found:
        print(f"\n    {C.YLW}⚠  Tidak ada interface WiFi yang terdeteksi.{C.RST}")
        print(f"    {C.GRY}Pastikan WiFi aktif dan script dijalankan di Termux.{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 15 — KERNEL & MODUL (/proc/modules + /proc/sys/kernel)
# ══════════════════════════════════════════════════════════════════════════════
def fitur_kernel():
    hdr("FITUR 15 · KERNEL & MODUL SISTEM", "🔧")

    sec("Informasi Kernel:")
    row("Versi Lengkap",  na(read("/proc/version")))
    uname = platform.uname()
    row("Kernel Release", uname.release)
    row("Hostname",       uname.node)
    row("Architecture",   uname.machine)

    # /proc/sys/kernel params
    sec("Kernel Parameters (/proc/sys/kernel):")
    kernel_params = {
        "kernel/ostype":            "OS Type",
        "kernel/osrelease":         "OS Release",
        "kernel/version":           "Build Kernel",
        "kernel/hostname":          "Hostname",
        "kernel/domainname":        "Domain",
        "kernel/pid_max":           "PID Max",
        "kernel/threads-max":       "Threads Max",
        "kernel/perf_event_max_sample_rate": "Perf Max Rate",
        "kernel/randomize_va_space": "ASLR (0=off 2=full)",
        "kernel/dmesg_restrict":    "dmesg Restrict",
        "kernel/kptr_restrict":     "kptr Restrict",
        "kernel/panic":             "Panic Timeout",
        "kernel/ngroups_max":       "ngroups Max",
        "kernel/sched_latency_ns":  "Sched Latency (ns)",
        "kernel/printk":            "printk Level",
        "vm/swappiness":            "VM Swappiness",
        "vm/dirty_ratio":           "VM Dirty Ratio %",
        "vm/overcommit_memory":     "VM Overcommit",
        "net/core/rmem_max":        "Net rmem_max",
        "net/core/wmem_max":        "Net wmem_max",
    }
    base = Path("/proc/sys")
    for rel, label in kernel_params.items():
        val = read(base / rel)
        if val: row(label, val[:70])

    # Modul yang dimuat
    sec("Modul Kernel Dimuat (/proc/modules):")
    mods_raw = read("/proc/modules")
    if mods_raw:
        mods = []
        for ln in mods_raw.split("\n"):
            parts = ln.split()
            if len(parts) >= 3:
                name    = parts[0]
                size    = int(parts[1]) if parts[1].isdigit() else 0
                used_by = parts[3].strip(",") if len(parts)>3 else "-"
                state   = parts[4] if len(parts)>4 else "?"
                mods.append((name, size, used_by, state))

        row("Total Modul", len(mods))
        print(f"\n    {C.BOLD}{'Nama':<28}{'Ukuran':>10}  Digunakan oleh{C.RST}")
        print(f"    {'─'*60}")
        for name, size, used_by, state in sorted(mods, key=lambda x: x[1], reverse=True)[:25]:
            sc = C.GRN if state == "Live" else C.YLW
            print(f"    {C.CYN}{name:<28}{C.RST}"
                  f"{b2h(size):>10}  "
                  f"{C.GRY}{used_by[:22]:<22}{C.RST}  {sc}{state}{C.RST}")
        if len(mods) > 25:
            print(f"    {C.GRY}... dan {len(mods)-25} modul lainnya.{C.RST}")
    else:
        print(f"    {C.GRY}/proc/modules tidak tersedia (mungkin perlu akses root).{C.RST}")

    # /proc/cmdline (kernel boot args)
    sec("Kernel Boot Command Line:")
    cmdline = read("/proc/cmdline")
    if cmdline:
        for part in cmdline.split():
            print(f"    {C.GRY}{part}{C.RST}")
    else:
        print(f"    {C.GRY}Tidak tersedia.{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 16 — VIRTUAL MEMORY STATS (/proc/vmstat)
# ══════════════════════════════════════════════════════════════════════════════
def fitur_vmstat():
    hdr("FITUR 16 · VIRTUAL MEMORY STATS (/proc/vmstat)", "🧮")

    vmstat_raw = read("/proc/vmstat")
    if not vmstat_raw:
        print(f"    {C.YLW}⚠  /proc/vmstat tidak tersedia.{C.RST}"); return

    vm = {}
    for ln in vmstat_raw.split("\n"):
        parts = ln.split()
        if len(parts) == 2:
            vm[parts[0]] = int(parts[1])

    sec("Page Faults:")
    row("Minor Faults (pgfault)",  f"{vm.get('pgfault',0):,}")
    row("Major Faults (pgmajfault)",f"{vm.get('pgmajfault',0):,}")

    sec("Swap Activity:")
    row("Swap In  (pswpin)",  f"{vm.get('pswpin',0):,}  halaman masuk")
    row("Swap Out (pswpout)", f"{vm.get('pswpout',0):,}  halaman keluar")
    swap_total = vm.get('pswpin',0) + vm.get('pswpout',0)
    row("Total Swap I/O",     f"{swap_total:,}")

    sec("Paging Activity:")
    row("Page In  (pgpgin)",  f"{vm.get('pgpgin',0):,}  KB")
    row("Page Out (pgpgout)", f"{vm.get('pgpgout',0):,}  KB")
    row("Page Freed (pgfree)",f"{vm.get('pgfree',0):,}")
    row("Page Aktif→Inaktif", f"{vm.get('pgdeactivate',0):,}")
    row("Page Inaktif→Aktif", f"{vm.get('pgactivate',0):,}")

    sec("Memory Reclaim:")
    row("kswapd steal",       f"{vm.get('kswapd_steal',0):,}")
    row("Direct reclaim",     f"{vm.get('allocstall',0):,}")
    row("OOM Kill",           f"{vm.get('oom_kill',0):,}")
    oom = vm.get('oom_kill',0)
    if oom > 0:
        print(f"    {C.RED}⚠  OOM Killer aktif — {oom} proses pernah dibunuh!{C.RST}")

    sec("CPU Context Switches & Interrupts (dari /proc/stat):")
    # ctxt, intr, softirq ada di /proc/stat, bukan /proc/vmstat
    stat_raw = read("/proc/stat")
    stat_ctxt = stat_intr = stat_sirq = 0
    for ln in stat_raw.split("\n"):
        parts = ln.split()
        if not parts: continue
        if parts[0] == "ctxt"    and len(parts)>1: stat_ctxt = int(parts[1])
        if parts[0] == "intr"    and len(parts)>1: stat_intr = int(parts[1])
        if parts[0] == "softirq" and len(parts)>1: stat_sirq = int(parts[1])
    row("Context Switches (ctxt)", f"{stat_ctxt:,}")
    row("Interrupts (intr)",        f"{stat_intr:,}")
    row("Soft IRQ (softirq)",       f"{stat_sirq:,}")

    sec("Huge Pages:")
    row("THP Fault Alloc",   f"{vm.get('thp_fault_alloc',0):,}")
    row("THP Collapse Alloc",f"{vm.get('thp_collapse_alloc',0):,}")

    # Snapshot sebelum & sesudah untuk activity rate
    sec("Activity Rate (diukur 3 detik):")
    vm_keys = ["pgpgin","pgpgout","pswpin","pswpout","pgfault","ctxt"]
    before = {}
    for k in vm_keys: before[k] = vm.get(k, 0)

    print(f"    {C.GRY}Mengukur...{C.RST}", end="", flush=True)
    time.sleep(3)
    print(f"\r{' '*20}\r", end="")

    vm2 = {}
    for ln in read("/proc/vmstat").split("\n"):
        parts = ln.split()
        if len(parts) == 2: vm2[parts[0]] = int(parts[1])

    row("Page In/s",        f"{(vm2.get('pgpgin',0)-before['pgpgin'])//3:,} KB/s")
    row("Page Out/s",       f"{(vm2.get('pgpgout',0)-before['pgpgout'])//3:,} KB/s")
    row("Page Fault/s",     f"{(vm2.get('pgfault',0)-before['pgfault'])//3:,}/s")
    row("Context Switch/s", f"{(vm2.get('ctxt',0)-before['ctxt'])//3:,}/s")
    row("Swap In/s",        f"{(vm2.get('pswpin',0)-before['pswpin'])//3:,} halaman/s")
    row("Swap Out/s",       f"{(vm2.get('pswpout',0)-before['pswpout'])//3:,} halaman/s")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 17 — SENSOR IIO / HARDWARE SENSOR
# ══════════════════════════════════════════════════════════════════════════════
def fitur_sensor():
    hdr("FITUR 17 · SENSOR IIO & HARDWARE SENSOR", "🧭")
    found = False

    # ── IIO Sensors (/sys/bus/iio/devices) ───────────────────────────────────
    iio_base = Path("/sys/bus/iio/devices")
    if iio_base.exists():
        sec("IIO Sensors (/sys/bus/iio/devices):")
        try: _iio_items = sorted(iio_base.iterdir())
        except PermissionError: _iio_items=[]; print(f"    {C.GRY}Permission denied: /sys/bus/iio/devices{C.RST}")
        for dev in _iio_items:
            name = read(dev/"name") or dev.name
            found = True
            print(f"\n    {C.BOLD}{C.MAG}{name}{C.RST}  [{dev.name}]")

            # Baca semua channel IIO yg tersedia
            for pat, label in [
                ("in_accel_*_raw",       "Akselerometer"),
                ("in_anglvel_*_raw",     "Giroskop"),
                ("in_magn_*_raw",        "Magnetometer"),
                ("in_proximity_raw",     "Proximity"),
                ("in_illuminance_raw",   "Cahaya Lux"),
                ("in_pressure_raw",      "Tekanan"),
                ("in_humidityrelative_raw","Kelembaban"),
                ("in_temp_raw",          "Suhu"),
                ("in_rot_*_raw",         "Rotasi"),
                ("in_gravity_*_raw",     "Gravitasi"),
                ("in_steps_raw",         "Langkah"),
                ("in_distance_raw",      "Jarak"),
            ]:
                files = list(dev.glob(pat))
                if files:
                    vals = []
                    for f in sorted(files)[:3]:
                        v = read(f)
                        if v: vals.append(f"{f.name.split('_')[2] if '_' in f.name else f.stem}={v}")
                    if vals:
                        # Cek scale factor — bungkus try/except agar tidak crash jika format aneh
                        scale = 1.0
                        try:
                            scale_f = list(dev.glob(pat.replace("_raw","_scale")))[:1]
                            if scale_f:
                                sv = read(scale_f[0])
                                if sv: scale = float(sv)
                        except (ValueError, OSError): scale = 1.0
                        row(f"  {label}", ", ".join(vals) + f"  (scale={scale})")

            # Sampling freq
            sf = read(dev/"sampling_frequency")
            if sf: row("  Sampling Freq", f"{sf} Hz")

            # Buffer
            buf_en = read(dev/"buffer/enable")
            if buf_en: row("  Buffer Enable", buf_en)

    # ── /sys/class/sensors (non-IIO) ─────────────────────────────────────────
    sens_class = Path("/sys/class/sensors")
    if sens_class.exists():
        sec("/sys/class/sensors:")
        try: _sens_items = sorted(sens_class.iterdir())
        except PermissionError: _sens_items=[]; print(f"    {C.GRY}Permission denied: /sys/class/sensors{C.RST}")
        for s in _sens_items:
            found = True
            name = read(s/"name") or s.name
            vendor = read(s/"vendor")
            row(name, na(vendor))

    # ── Input event devices (touchscreen, accelerometer sbg input) ───────────
    input_base = Path("/sys/class/input")
    if input_base.exists():
        sec("Input Devices (/sys/class/input):")
        try: _input_items = sorted(input_base.iterdir())
        except PermissionError: _input_items=[]; print(f"    {C.GRY}Permission denied: /sys/class/input{C.RST}")
        for inp in _input_items:
            name = read(inp/"device/name") or read(inp/"name") or ""
            if not name: continue
            # Filter hanya sensor / hardware input yg relevan
            if not any(k in name.lower() for k in
                       ("accel","gyro","magnet","sensor","compass","baro",
                        "prox","light","touch","key","hall","gesture")):
                continue
            found = True
            phys = read(inp/"device/phys") or read(inp/"phys") or "—"
            row(f"  {name}", phys)

    # ── getprop sensor ────────────────────────────────────────────────────────
    sec("Android Sensor Properties:")
    sensor_props = {
        "ro.hardware.sensors":      "Sensor HAL",
        "sensors.iio.auto_trigger": "IIO Auto Trigger",
    }
    any_s = False
    for key, label in sensor_props.items():
        val = run(["getprop", key])
        if val: row(label, val); any_s = True
    if not any_s:
        print(f"    {C.GRY}Tidak ada sensor property dari getprop.{C.RST}")

    if not found:
        print(f"\n    {C.YLW}⚠  Tidak ada sensor IIO terdeteksi.")
        print(f"    {C.GRY}Di Termux, sensor mungkin perlu akses root atau permission.{C.RST}")


# ══════════════════════════════════════════════════════════════════════════════
# FITUR 18 — ANDROID LANJUT (dumpsys, pm list, dll)
# ══════════════════════════════════════════════════════════════════════════════
def fitur_android_lanjut():
    hdr("FITUR 18 · INFO ANDROID LANJUT", "🤖")

    # ── dumpsys battery ───────────────────────────────────────────────────────
    sec("dumpsys battery:")
    out = run(["dumpsys","battery"], timeout=6)
    if out:
        for ln in out.split("\n")[:20]:
            if ":" in ln and ln.strip():
                k, _, v = ln.partition(":")
                row(k.strip()[:28], v.strip()[:50])
    else:
        print(f"    {C.GRY}dumpsys tidak tersedia (butuh akses ADB / Termux).{C.RST}")

    # ── dumpsys cpuinfo (top-level) ───────────────────────────────────────────
    sec("dumpsys cpuinfo (CPU Load):")
    cpuout = run(["dumpsys","cpuinfo"], timeout=8)
    if cpuout:
        for ln in cpuout.split("\n")[:15]:
            if ln.strip(): print(f"    {C.GRY}{ln}{C.RST}")
    else:
        print(f"    {C.GRY}Tidak tersedia.{C.RST}")

    # ── pm list packages (hitung total) ───────────────────────────────────────
    sec("Package Manager (pm):")
    all_pkg  = run(["pm","list","packages"], timeout=10)
    sys_pkg  = run(["pm","list","packages","-s"], timeout=10)
    user_pkg = run(["pm","list","packages","-3"], timeout=10)
    dis_pkg  = run(["pm","list","packages","-d"], timeout=10)
    if all_pkg:
        total = len([l for l in all_pkg.split("\n") if l.strip()])
        sys_c = len([l for l in sys_pkg.split("\n") if l.strip()]) if sys_pkg else "?"
        usr_c = len([l for l in user_pkg.split("\n") if l.strip()]) if user_pkg else "?"
        dis_c = len([l for l in dis_pkg.split("\n") if l.strip()]) if dis_pkg else "?"
        row("Total Paket",        total)
        row("Sistem",             sys_c)
        row("User (Install)",     usr_c)
        row("Dinonaktifkan",      dis_c)

        if user_pkg:
            sec("Aplikasi User Terinstall:")
            for ln in sorted(user_pkg.split("\n"))[:20]:
                pkg = ln.replace("package:","").strip()
                if pkg: print(f"    {C.CYN}· {pkg}{C.RST}")
            if usr_c != "?" and int(str(usr_c)) > 20:
                print(f"    {C.GRY}... dan {int(str(usr_c))-20} lainnya.{C.RST}")
    else:
        print(f"    {C.GRY}pm tidak tersedia (butuh Termux + permission).{C.RST}")

    # ── getprop lanjut ────────────────────────────────────────────────────────
    sec("Android Properties Lanjut:")
    adv_props = {
        "ro.product.first_api_level":   "First API Level",
        "ro.crypto.type":               "Enkripsi",
        "ro.secure":                    "Secure Boot",
        "ro.debuggable":                "Debuggable",
        "ro.adb.secure":                "ADB Secure",
        "sys.usb.state":                "USB State",
        "persist.sys.language":         "Bahasa Sistem",
        "persist.sys.country":          "Negara",
        "persist.sys.timezone":         "Timezone",
        "ro.sf.lcd_density":            "LCD Density (dpi)",
        "ro.opengles.version":          "OpenGL ES Version",
        "ro.dalvik.vm.heapsize":        "Dalvik Heap Size",
        "dalvik.vm.heapgrowthlimit":    "Heap Growth Limit",
        "dalvik.vm.heapstartsize":      "Heap Start Size",
        "dalvik.vm.heapsize":           "Dalvik VM Heap Max",
        "ro.build.selinux":             "SELinux",
        "ro.boot.selinux":              "SELinux Boot",
    }
    any_p = False
    for key, label in adv_props.items():
        val = run(["getprop", key])
        if val: row(label, val[:60]); any_p = True
    if not any_p:
        print(f"    {C.GRY}getprop tidak tersedia.{C.RST}")

    # ── wm size & density ─────────────────────────────────────────────────────
    sec("Display (wm):")
    size = run(["wm","size"], timeout=4)
    dens = run(["wm","density"], timeout=4)
    if size: row("Resolusi",  size.replace("Physical size: ",""))
    if dens: row("Density",   dens.replace("Physical density: ","") + " dpi")
    if not size and not dens:
        print(f"    {C.GRY}wm tidak tersedia.{C.RST}")

    # ── settings get ─────────────────────────────────────────────────────────
    sec("Settings System:")
    settings_keys = [
        ("screen_brightness",      "Kecerahan Layar"),
        ("screen_off_timeout",     "Timeout Layar (ms)"),
        ("accelerometer_rotation", "Rotasi Otomatis"),
        ("sound_effects_enabled",  "Efek Suara"),
        ("wifi_sleep_policy",      "WiFi Sleep Policy"),
    ]
    for key, label in settings_keys:
        val = run(["settings","get","system", key], timeout=3)
        if val and val != "null": row(label, val)


# ══════════════════════════════════════════════════════════════════════════════
# MENU UTAMA
# ══════════════════════════════════════════════════════════════════════════════
MENU = [
    ("1",  "🖥️   Info CPU (core, freq, governor, load avg)",     fitur_cpu),
    ("2",  "💾   Info RAM (meminfo detail + swap)",               fitur_ram),
    ("3",  "💿   Info Storage (mount + diskstats I/O)",           fitur_storage),
    ("4",  "🔋   Info Baterai (tegangan, siklus, health)",        fitur_baterai),
    ("5",  "🌡️   Suhu Hardware (thermal zones + hwmon)",          fitur_suhu),
    ("6",  "🌐   Info Jaringan (IP, MAC, latensi TCP)",           fitur_network),
    ("7",  "📱   Info Sistem & OS (getprop Android)",             fitur_os),
    ("8",  "⚙️   Proses Aktif — Top 15 CPU (/proc)",             fitur_proses),
    ("9",  "📡   Kecepatan Jaringan Real-time + speed test",      fitur_netspeed),
    ("10", "⚡   Benchmark CPU (4 tes pure Python)",              fitur_benchmark),
    ("11", "📊   Monitor Real-time (live 10 detik)",              fitur_monitor),
    ("12", "📋   Laporan Lengkap (Export JSON + TXT)",            fitur_laporan),
    ("13", "🎮   Info GPU (Adreno/Mali/DevFreq)         [NEWv2]", fitur_gpu),
    ("14", "📶   WiFi Detail (signal, channel, AP)      [NEWv2]", fitur_wifi),
    ("15", "🔧   Kernel & Modul Sistem                  [NEWv2]", fitur_kernel),
    ("16", "🧮   Virtual Memory Stats (/proc/vmstat)    [NEWv2]", fitur_vmstat),
    ("17", "🧭   Sensor IIO & Hardware Sensor           [NEWv2]", fitur_sensor),
    ("18", "🤖   Android Lanjut (dumpsys, pm, wm)       [NEWv2]", fitur_android_lanjut),
]

def show_menu():
    print(f"\n{C.BOLD}{C.MAG}{'═'*66}{C.RST}")
    print(f"  {C.BOLD}{C.WHT}   CEK HARDWARE — ANDROID v2.0  ·  ZERO DEPENDENCY{C.RST}")
    print(f"  {C.DIM}{C.GRY}   Baca /proc & /sys langsung — tanpa psutil{C.RST}")
    print(f"{C.BOLD}{C.MAG}{'═'*66}{C.RST}")
    for k, label, _ in MENU:
        color = C.YLW if "NEWv2" in label else C.CYN
        print(f"  {color}{k:>3}{C.RST}  {label}")
    print(f"\n  {C.BOLD}{C.GRN}    0{C.RST}  🚀 Jalankan Semua 18 Fitur")
    print(f"  {C.RED}    q{C.RST}  ❌ Keluar")
    print(f"{C.BOLD}{C.MAG}{'─'*66}{C.RST}")

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
                try: fn()
                except Exception as e: print(f"  {C.RED}Error: {e}{C.RST}")
        elif ch in fmap:
            try: fmap[ch]()
            except Exception as e: print(f"\n  {C.RED}Error: {e}{C.RST}")
        else:
            print(f"\n  {C.RED}⚠  Pilihan tidak valid. Masukkan 1-18, 0, atau q.{C.RST}")

        try: input(f"\n  {C.GRY}[Tekan Enter untuk kembali ke menu...]{C.RST}")
        except (KeyboardInterrupt, EOFError): break

if __name__ == "__main__":
    main()
