#!/usr/bin/env python3
"""每日访问摘要：把昨天的 nginx 日志 + 阅读数库压成一页，供 /stats/daily/ 查看。

设计要点（都是踩过坑换来的）：
- 日志里绝大多数请求是扫描器，所以「总量」和「真实读者」必须分开报数；
- 阅读数库（views.db）才是可信的阅读口径，日志只能看趋势；
- 只在有真实数据的时候才写文件，避免把空一天写进历史。

用法：
    python3 stats-daily.py              # 生成昨天的
    python3 stats-daily.py 2026-11-21   # 指定日期
"""

import gzip
import html
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone

LOG_DIR = "/var/log/nginx"
OUT_DIR = os.environ.get("STATS_OUT_DIR", "/var/www/blog-stats/daily")
STATE = "/var/lib/blogstats/daily.json"
HEALTH = "/var/lib/blogstats/health.jsonl"
DB = "/var/lib/blogviews/views.db"
KEEP_DAYS = 30
BJT = timezone(timedelta(hours=8))

BOT_RE = re.compile(
    r"(bot|crawler|spider|scrapy|curl|wget|python-|go-http|java/|okhttp|"
    r"headless|phantom|monitor|uptime|http-client|zgrab|masscan|nmap)",
    re.I,
)
# 扫描器爱试的路径：既不算页面浏览，也不进热门榜
PROBE_RE = re.compile(
    r"(\.php|\.asp|\.jsp|\.cgi|/\.(git|svn|hg|bzr|env|DS_Store)|wp-|xmlrpc|"
    r"phpmyadmin|/config\.json|/\.ssh|/\.aws|actuator|administrator|/test\.)",
    re.I,
)
LINE_RE = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d{3}) (\S+) "([^"]*)" "([^"]*)"')

REQ_RE = re.compile(r"^([A-Z]+) (\S+)")


def target_day(argv):
    if len(argv) > 1:
        return datetime.strptime(argv[1], "%Y-%m-%d").date()
    return (datetime.now(BJT) - timedelta(days=1)).date()


def log_files():
    """按新到旧列出可读的日志文件（含 gz）。"""
    names = []
    for i in range(0, 8):
        for cand in (f"access.log.{i}.gz", f"access.log.{i}" if i else "access.log"):
            path = os.path.join(LOG_DIR, cand)
            if os.path.exists(path):
                names.append(path)
    return names


def open_log(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def collect(day):
    total = 0
    ips = set()
    human = 0
    human_ips = set()
    pages = Counter()
    status = Counter()
    refs = Counter()
    bots = Counter()
    probes = Counter()
    probe_total = 0
    hours = Counter()

    for path in log_files():
        with open_log(path) as fh:
            for line in fh:
                m = LINE_RE.match(line)
                if not m:
                    continue
                ip, ts, req, code, size, ref, ua = m.groups()
                try:
                    when = datetime.strptime(ts, "%d/%b/%Y:%H:%M:%S %z").astimezone(BJT)
                except ValueError:
                    continue
                if when.date() != day:
                    continue

                rm = REQ_RE.match(req)
                url = rm.group(2) if rm else "-"
                path_only = url.split("?", 1)[0]

                total += 1
                ips.add(ip)
                status[code] += 1
                hours[when.hour] += 1

                if PROBE_RE.search(path_only):
                    probes[path_only[:60]] += 1
                    probe_total += 1
                    continue
                if BOT_RE.search(ua):
                    bots[os.path.basename(path_only) or path_only] += 1
                    continue

                human += 1
                human_ips.add(ip)
                if ref and "aiqivy.com" not in ref:
                    refs[ref[:80]] += 1
                if code in ("200", "304") and (path_only.endswith("/") or path_only.endswith(".html")):
                    pages[path_only] += 1

    return {
        "date": day.isoformat(),
        "total": total,
        "ips": len(ips),
        "human": human,
        "human_ips": len(human_ips),
        "pages": pages.most_common(12),
        "status": dict(sorted(status.items())),
        "refs": refs.most_common(8),
        "bots": bots.most_common(6),
        "probes": probes.most_common(6),
        "probe_total": probe_total,
        "hourly": [hours.get(h, 0) for h in range(24)],
    }


def reads(day):
    """阅读数库：真实阅读的 PV/UV，按文章。"""
    if not os.path.exists(DB):
        return 0, 0, []
    key = day.isoformat()
    try:
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=5)
    except sqlite3.Error:
        return 0, 0, []
    try:
        pv = con.execute("SELECT COALESCE(SUM(n),0) FROM pv WHERE day=?", (key,)).fetchone()[0]
        uv = con.execute("SELECT COUNT(*) FROM uv WHERE day=?", (key,)).fetchone()[0]
        top = con.execute(
            "SELECT path, n FROM pv WHERE day=? ORDER BY n DESC LIMIT 8", (key,)
        ).fetchall()
    except sqlite3.Error:
        pv, uv, top = 0, 0, []
    finally:
        con.close()
    return pv, uv, top


def health(day):
    """把 health.jsonl 里当天的采样聚合成一份摘要；没有采样就返回 None。"""
    rows = []
    try:
        with open(HEALTH, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    when = datetime.fromtimestamp(rec["ts"], BJT)
                except (ValueError, KeyError, OSError):
                    continue
                if when.date() == day:
                    rows.append(rec)
    except OSError:
        return None
    if not rows:
        return None
    rows.sort(key=lambda r: r["ts"])

    loads = [r["load"][0] for r in rows if r.get("load")]
    cpus = [r["cpu"] for r in rows if r.get("cpu") is not None]
    mems = [r["mem"]["pct"] for r in rows if r.get("mem")]
    disks = [r for r in rows if r.get("disk")]

    rx = tx = peak_rx = peak_tx = 0
    prev = None
    for r in rows:
        net = r.get("net")
        if not net:
            continue
        if prev:
            d_rx = max(0, net["rx"] - prev["rx"])
            d_tx = max(0, net["tx"] - prev["tx"])
            rx += d_rx
            tx += d_tx
            peak_rx = max(peak_rx, d_rx)
            peak_tx = max(peak_tx, d_tx)
        prev = net

    disk_first = disks[0]["disk"] if disks else None
    disk_last = disks[-1]["disk"] if disks else None
    return {
        "samples": len(rows),
        "ncpu": rows[-1].get("ncpu", 1),
        "uptime": rows[-1].get("uptime", 0),
        "load_avg": round(sum(loads) / len(loads), 2) if loads else 0.0,
        "load_max": round(max(loads), 2) if loads else 0.0,
        "cpu_avg": round(sum(cpus) / len(cpus), 1) if cpus else None,
        "cpu_max": round(max(cpus), 1) if cpus else None,
        "mem_avg": round(sum(mems) / len(mems), 1) if mems else None,
        "mem_max": round(max(mems), 1) if mems else None,
        "mem_total": rows[-1]["mem"]["total"] if rows[-1].get("mem") else None,
        "disk_pct_first": disk_first["pct"] if disk_first else None,
        "disk_pct_last": disk_last["pct"] if disk_last else None,
        "disk_used_last": disk_last["used"] if disk_last else None,
        "disk_total": disk_last["total"] if disk_last else None,
        "disk_delta": (disk_last["used"] - disk_first["used"]) if (disk_first and disk_last) else 0,
        "rx": rx,
        "tx": tx,
        "peak_rx": peak_rx,
        "peak_tx": peak_tx,
    }


def human_bytes(n):
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(n or 0)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.0f} {unit}" if unit in ("B", "KB") else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def load_state():
    try:
        with open(STATE, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (OSError, ValueError):
        pass
    return []


def save_state(rows):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    rows = sorted({r["date"]: r for r in rows}.values(), key=lambda r: r["date"])[-KEEP_DAYS:]
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)
    return rows


def esc(text):
    return html.escape(str(text))


def bar(value, peak, width=22):
    n = 0 if not peak else round(value / peak * width)
    return "█" * max(n, 1 if value else 0)


def render(rows, cur):
    peak = max([p[1] for p in cur["pages"]] or [1])
    status_peak = max(list(cur["status"].values()) or [1])
    hours_peak = max(cur["hourly"] or [1])

    def page_rows():
        out = []
        for path, n in cur["pages"]:
            out.append(
                f'<tr><td class="p"><a href="https://aiqivy.com{esc(path)}">{esc(path)}</a></td>'
                f'<td class="n">{n}</td><td class="b">{bar(n, peak)}</td></tr>'
            )
        return "".join(out) or '<tr><td colspan="3" class="muted">当天没有页面浏览</td></tr>'

    def read_rows():
        out = []
        for path, n in cur["read_top"]:
            out.append(
                f'<tr><td class="p"><a href="https://aiqivy.com{esc(path)}">{esc(path)}</a></td>'
                f'<td class="n">{n}</td></tr>'
            )
        return "".join(out) or '<tr><td colspan="2" class="muted">没有计数</td></tr>'

    def status_rows():
        label = {"200": "200 正常", "301": "301 跳转", "304": "304 缓存", "404": "404 不存在", "444": "444 已掐断"}
        out = []
        for code, n in cur["status"].items():
            out.append(
                f'<tr><td class="p">{esc(label.get(code, code))}</td><td class="n">{n}</td>'
                f'<td class="b">{bar(n, status_peak)}</td></tr>'
            )
        return "".join(out)

    def ref_rows():
        if not cur["refs"]:
            return '<tr><td colspan="2" class="muted">没有外部来源 —— 目前还是自己在看</td></tr>'
        return "".join(
            f'<tr><td class="p">{esc(r)}</td><td class="n">{n}</td></tr>' for r, n in cur["refs"]
        )

    def probe_rows():
        if not cur["probes"]:
            return '<tr><td colspan="2" class="muted">没有探测</td></tr>'
        return "".join(
            f'<tr><td class="p"><code>{esc(p)}</code></td><td class="n">{n}</td></tr>'
            for p, n in cur["probes"]
        )

    def health_cards():
        h = cur.get("health")
        if not h:
            return ""
        total_net = h["rx"] + h["tx"]
        return (
            f'<div class="card"><div class="k">服务器负载</div>'
            f'<div class="v">{h["load_max"]:.2f}</div>'
            f'<div class="u">峰值 · {h["ncpu"]} 核 · 均 {h["load_avg"]:.2f}</div></div>'
            f'<div class="card"><div class="k">CPU 峰值</div>'
            f'<div class="v">{h["cpu_max"] if h["cpu_max"] is not None else "–"}%</div>'
            f'<div class="u">均值 {h["cpu_avg"] if h["cpu_avg"] is not None else "–"}%</div></div>'
            f'<div class="card"><div class="k">内存峰值</div>'
            f'<div class="v">{h["mem_max"] if h["mem_max"] is not None else "–"}%</div>'
            f'<div class="u">均值 {h["mem_avg"] if h["mem_avg"] is not None else "–"}%</div></div>'
            f'<div class="card"><div class="k">磁盘占用</div>'
            f'<div class="v">{h["disk_pct_last"] if h["disk_pct_last"] is not None else "–"}%</div>'
            f'<div class="u">当日 {"+" if h["disk_delta"] >= 0 else ""}{human_bytes(h["disk_delta"])}</div></div>'
            f'<div class="card"><div class="k">今日流量</div>'
            f'<div class="v">{human_bytes(total_net)}</div>'
            f'<div class="u">↓ {human_bytes(h["rx"])} · ↑ {human_bytes(h["tx"])}</div></div>'
        )

    def health_rows():
        h = cur.get("health")
        if not h:
            return (
                '<section><h2>服务器健康</h2>'
                '<table><tr><td class="muted">这一天没有采样数据'
                "（健康采样从 2026-11-22 起开始记录，明天起每天都有）</td></tr></table></section>"
            )
        rows_html = [
            ("负载（1 分钟）", f'{h["load_avg"]:.2f} 均值 · {h["load_max"]:.2f} 峰值 · {h["ncpu"]} 核'),
            (
                "CPU 使用率",
                f'{h["cpu_avg"] if h["cpu_avg"] is not None else "–"}% 均值 · '
                f'{h["cpu_max"] if h["cpu_max"] is not None else "–"}% 峰值',
            ),
            (
                "内存",
                f'{h["mem_avg"] if h["mem_avg"] is not None else "–"}% 均值 · '
                f'{h["mem_max"] if h["mem_max"] is not None else "–"}% 峰值'
                + (f' · 共 {human_bytes(h["mem_total"])}' if h["mem_total"] else ""),
            ),
            (
                "磁盘 /",
                f'{human_bytes(h["disk_used_last"])} / {human_bytes(h["disk_total"])}'
                f'（{h["disk_pct_last"]}%，当日 {"+" if h["disk_delta"] >= 0 else ""}'
                f'{human_bytes(h["disk_delta"])}）'
                if h["disk_total"]
                else "无数据",
            ),
            (
                "网络",
                f'下行 {human_bytes(h["rx"])}（峰值 {human_bytes(h["peak_rx"])}/5 分钟）'
                f' · 上行 {human_bytes(h["tx"])}（峰值 {human_bytes(h["peak_tx"])}/5 分钟）',
            ),
            ("采样", f'{h["samples"]} 次（每 5 分钟一次）· 开机 {h["uptime"] // 86400} 天'),
        ]
        return "<section><h2>服务器健康</h2><table>" + "".join(
            f'<tr><td class="p">{k}</td><td class="n">{v}</td></tr>' for k, v in rows_html
        ) + "</table></section>"

    def history_rows():
        out = []
        for r in reversed(rows[-14:]):
            hh = r.get("health") or {}
            load_cell = f'{hh["load_max"]:.2f}' if hh.get("load_max") is not None else "–"
            disk_cell = hh.get("disk_pct_last")
            disk_cell = f"{disk_cell}" if disk_cell is not None else "–"
            out.append(
                f'<tr{" class=cur" if r["date"] == cur["date"] else ""}>'
                f'<td class="p">{r["date"]}</td><td class="n">{r["total"]}</td>'
                f'<td class="n">{r["human"]}</td><td class="n">{r["human_ips"]}</td>'
                f'<td class="n">{r.get("read_pv", 0)}</td><td class="n">{r.get("read_uv", 0)}</td>'
                f'<td class="n">{load_cell}</td><td class="n">{disk_cell}</td></tr>'
            )
        return "".join(out)

    def hour_chart():
        cells = []
        for h, n in enumerate(cur["hourly"]):
            hgt = 2 + round(n / hours_peak * 46) if n else 2
            cells.append(
                f'<div class="hcol" title="{h:02d}:00 · {n} 次"><i style="height:{hgt}px"></i>'
                f'<b>{h if h % 3 == 0 else ""}</b></div>'
            )
        return "".join(cells)

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>访问日报 · {esc(cur["date"])} · 蔚来实验室</title>
<style>
:root{{--ink:#1b1c2b;--muted:#8b8aa0;--line:#e7e4dc;--bg:#faf8f4;--accent:#6d4bd8;--warm:#d8804b}}
*{{box-sizing:border-box}}
body{{margin:0;padding:32px 20px 64px;background:var(--bg);color:var(--ink);
 font:15px/1.7 -apple-system,"Segoe UI","Noto Sans SC",system-ui,sans-serif}}
.wrap{{max-width:900px;margin:0 auto}}
h1{{font:600 26px/1.3 Georgia,"Noto Serif SC",serif;margin:0 0 4px}}
.sub{{color:var(--muted);font-size:13px;margin-bottom:26px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:26px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px}}
.card .k{{color:var(--muted);font-size:12px;letter-spacing:.04em}}
.card .v{{font:600 26px/1.2 Georgia,serif;margin-top:2px}}
.card .u{{color:var(--muted);font-size:12px}}
section{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px 20px;margin-bottom:16px}}
h2{{font-size:14px;letter-spacing:.06em;color:var(--muted);font-weight:600;margin:0 0 12px;text-transform:uppercase}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}
td{{padding:6px 4px;border-bottom:1px solid #f1efe9;vertical-align:top}}
tr:last-child td{{border-bottom:none}}
td.p{{word-break:break-all}} td.n{{text-align:right;white-space:nowrap;color:var(--ink);font-variant-numeric:tabular-nums}}
td.b{{color:var(--accent);font-size:11px;letter-spacing:-1px;width:150px}}
code{{background:#f4f2ec;padding:1px 5px;border-radius:5px;font-size:12.5px}}
a{{color:inherit;text-decoration:none;border-bottom:1px solid #ddd8cd}} a:hover{{border-color:var(--accent)}}
.muted{{color:var(--muted)}}
.cur td{{background:#f7f4ff}}
.chart{{display:flex;align-items:flex-end;gap:3px;height:64px;margin-top:6px}}
.hcol{{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%}}
.hcol i{{display:block;width:100%;background:linear-gradient(180deg,#8a6ce8,#c9b8f7);border-radius:3px 3px 1px 1px;min-height:2px}}
.hcol b{{font-size:9px;color:var(--muted);font-weight:400;height:12px}}
footer{{color:var(--muted);font-size:12px;margin-top:22px;text-align:center}}
</style></head><body><div class="wrap">
<h1>访问日报 · {esc(cur["date"])}</h1>
<div class="sub">北京时间 00:00–24:00 ｜ 数据：nginx 访问日志 + 阅读数库</div>

<div class="cards">
  <div class="card"><div class="k">总请求</div><div class="v">{cur["total"]}</div><div class="u">含扫描器</div></div>
  <div class="card"><div class="k">独立 IP</div><div class="v">{cur["ips"]}</div><div class="u">全部来源</div></div>
  <div class="card"><div class="k">真实请求</div><div class="v">{cur["human"]}</div><div class="u">{cur["human_ips"]} 个 IP</div></div>
  <div class="card"><div class="k">文章阅读</div><div class="v">{cur["read_pv"]}</div><div class="u">{cur["read_uv"]} 人读过</div></div>
</div>
{health_cards()}

<section><h2>热门页面（已剔除扫描器与爬虫）</h2><table>{page_rows()}</table></section>

<section><h2>阅读数库 · 按文章</h2><table>{read_rows()}</table></section>

<section><h2>24 小时请求分布</h2><div class="chart">{hour_chart()}</div></section>

<section><h2>状态码</h2><table>{status_rows()}</table></section>

<section><h2>外部来源</h2><table>{ref_rows()}</table></section>

<section><h2>探测与扫描 · 共 {cur.get("probe_total", 0)} 次（前 6 名）</h2><table>{probe_rows()}</table></section>

{health_rows()}

<section><h2>最近 14 天</h2>
<table><tr><td class="p muted">日期</td><td class="n muted">请求</td><td class="n muted">真实</td><td class="n muted">IP</td><td class="n muted">阅读</td><td class="n muted">读者</td><td class="n muted">负载</td><td class="n muted">磁盘%</td></tr>
{history_rows()}</table></section>

<footer>由 stats-daily.py 每日 00:10 生成 · 共记录 {len(rows)} 天</footer>
</div></body></html>
"""


def main(argv):
    day = target_day(argv)
    cur = collect(day)
    pv, uv, top = reads(day)
    cur["read_pv"] = pv
    cur["read_uv"] = uv
    cur["read_top"] = top
    cur["health"] = health(day)

    rows = save_state(load_state() + [cur]) if cur["total"] else load_state()
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(render(rows, cur))

    top_pages = "、".join(p for p, _ in cur["pages"][:3]) or "无"
    h = cur.get("health") or {}
    health_bit = ""
    if h:
        health_bit = (
            f"｜负载 {h['load_max']:.2f}（峰值）"
            f"｜磁盘 {h['disk_pct_last']}%"
            f"｜流量 ↓{human_bytes(h['rx'])} ↑{human_bytes(h['tx'])}"
        )
    summary = (
        f"[{cur['date']}] 请求 {cur['total']}（真实 {cur['human']} / {cur['human_ips']} IP）"
        f"｜阅读 {pv} pv / {uv} uv｜热门：{top_pages}"
        f"｜探测类请求 {cur.get('probe_total', 0)} 次{health_bit}"
    )
    print(summary)

    hook = os.environ.get("STATS_WEBHOOK_URL", "").strip()
    if hook:
        body = json.dumps({"text": summary}, ensure_ascii=False).encode()
        req = urllib.request.Request(
            hook, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            urllib.request.urlopen(req, timeout=10).read()
        except Exception as exc:  # 推送失败不影响报表
            print(f"WARN webhook 失败：{exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))