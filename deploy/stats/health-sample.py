#!/usr/bin/env python3
"""服务器健康采样：每 5 分钟往 /var/lib/blogstats/health.jsonl 追加一行。

只读 /proc 和 statvfs，不装任何依赖；单条记录包含
时间、负载、CPU 使用率、内存、磁盘、网卡收发增量。
stats-daily.py 会把这些采样按北京时间的「天」聚合进日报。
"""

import json
import os
import time

STATE_DIR = "/var/lib/blogstats"
OUT = os.path.join(STATE_DIR, "health.jsonl")
CPU_PREV = os.path.join(STATE_DIR, "cpu.prev")
KEEP_SECONDS = 8 * 24 * 3600  # 留 8 天，日报只看 30 天内的趋势


def read_first(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.readline().strip()
    except OSError:
        return ""


def cpu_times():
    """返回 (total, idle) 的累计 jiffies。"""
    parts = read_first("/proc/stat").split()
    if not parts or parts[0] != "cpu":
        return None, None
    nums = [int(x) for x in parts[1:11]]
    idle = nums[3] + (nums[4] if len(nums) > 4 else 0)  # idle + iowait
    return sum(nums), idle


def cpu_percent():
    """用两次采样之间的差值算真实占用率；间隔太短或没有基准就返回 None。

    坑：定时器刚装好时两次采样会挨在一起跑，delta 只有个位数 jiffies，
    除出来的占用率是假的 100%。所以要求窗口内至少累计 50 jiffies（约 0.5 秒/核），
    不满足就沿用旧基准，等下一次真正的 5 分钟采样。
    """
    total, idle = cpu_times()
    if total is None:
        return None
    prev = None
    try:
        with open(CPU_PREV, "r", encoding="utf-8") as fh:
            p_total, p_idle = fh.read().split()
        prev = (int(p_total), int(p_idle))
    except (OSError, ValueError):
        prev = None
    os.makedirs(STATE_DIR, exist_ok=True)

    pct = None
    if prev:
        d_total = total - prev[0]
        d_idle = idle - prev[1]
        if d_total >= 50 and d_idle >= 0:
            pct = round(100.0 * (1 - d_idle / d_total), 1)
    if pct is not None or not prev:
        with open(CPU_PREV, "w", encoding="utf-8") as fh:
            fh.write(f"{total} {idle}")
    return pct


def memory():
    info = {}
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            for line in fh:
                key, _, rest = line.partition(":")
                if key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
                    info[key] = int(rest.split()[0]) * 1024
    except (OSError, ValueError, IndexError):
        return None
    total = info.get("MemTotal", 0)
    avail = info.get("MemAvailable", 0)
    if not total:
        return None
    return {
        "total": total,
        "used": total - avail,
        "pct": round(100.0 * (total - avail) / total, 1),
        "swap_used": info.get("SwapTotal", 0) - info.get("SwapFree", 0),
    }


def disk():
    try:
        st = os.statvfs("/")
    except OSError:
        return None
    total = st.f_blocks * st.f_frsize
    free = st.f_bavail * st.f_frsize
    used = total - st.f_bfree * st.f_frsize
    return {
        "total": total,
        "used": used,
        "free": free,
        "pct": round(100.0 * used / total, 1) if total else 0.0,
    }


def net():
    """累计字节数（排除回环），增量由 stats-daily 里按相邻采样算，避免重启丢状态。"""
    rx = tx = 0
    try:
        with open("/proc/net/dev", "r", encoding="utf-8") as fh:
            for line in fh.readlines()[2:]:
                name, _, data = line.partition(":")
                if name.strip() == "lo":
                    continue
                cols = data.split()
                if len(cols) < 9:
                    continue
                rx += int(cols[0])
                tx += int(cols[8])
    except (OSError, ValueError, IndexError):
        return None
    return {"rx": rx, "tx": tx}


def trim():
    """按时间裁掉过老的行，避免文件无限增长。"""
    now = time.time()
    try:
        with open(OUT, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return
    kept = []
    for line in lines:
        try:
            if now - json.loads(line)["ts"] < KEEP_SECONDS:
                kept.append(line if line.endswith("\n") else line + "\n")
        except (ValueError, KeyError):
            continue
    if len(kept) != len(lines):
        tmp = OUT + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.writelines(kept)
        os.replace(tmp, OUT)


def main():
    os.makedirs(STATE_DIR, exist_ok=True)
    try:
        load = [float(x) for x in read_first("/proc/loadavg").split()[:3]]
    except (ValueError, IndexError):
        load = [0.0, 0.0, 0.0]
    try:
        up = float(read_first("/proc/uptime").split()[0])
    except (ValueError, IndexError):
        up = 0.0

    rec = {
        "ts": int(time.time()),
        "load": load,
        "ncpu": os.cpu_count() or 1,
        "cpu": cpu_percent(),
        "mem": memory(),
        "disk": disk(),
        "net": net(),
        "uptime": int(up),
    }
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    m, d, n = rec["mem"] or {}, rec["disk"] or {}, rec["net"] or {}
    print(
        f"load={load[0]:.2f} cpu={rec['cpu']} "
        f"mem={m.get('pct')}% disk={d.get('pct')}% "
        f"net_rx_total={n.get('rx')} net_tx_total={n.get('tx')}"
    )
    trim()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())