#!/usr/bin/env python3
"""极简文章浏览量计数服务（只用标准库）。

    POST /api/views   {"path": "/posts/xxx/"}   记一次浏览，返回最新数字
    GET  /api/views?path=/posts/xxx/            只读

统计口径：
  pv  每次访问 +1（同一个人刷新也算）
  uv  同一天、同一 IP、同一篇文章只算一次

数据库默认在 /var/lib/blogviews/views.db，可以用 VIEWS_DB 覆盖。
服务只监听 127.0.0.1，由 nginx 反代，外部无法直连。
"""

import json
import os
import re
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DB_PATH = os.environ.get("VIEWS_DB", "/var/lib/blogviews/views.db")
PORT = int(os.environ.get("VIEWS_PORT", "8099"))
HOST = "127.0.0.1"

# 只接受文章详情页，避免有人往库里塞乱七八糟的路径
PATH_RE = re.compile(r"^/posts/[A-Za-z0-9][A-Za-z0-9._-]*/$")
BOT_RE = re.compile(
    r"bot|spider|crawl|slurp|headless|preview|monitor|uptime|curl|wget|"
    r"python-requests|httpclient|go-http-client|facebookexternalhit",
    re.I,
)

_lock = threading.Lock()
_last_hit = {}  # (ip, path) -> 上次计数时间，防连点


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS pv (
                path TEXT NOT NULL,
                day  TEXT NOT NULL,
                n    INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (path, day)
            );
            CREATE TABLE IF NOT EXISTS uv (
                path TEXT NOT NULL,
                day  TEXT NOT NULL,
                ip   TEXT NOT NULL,
                PRIMARY KEY (path, day, ip)
            );
            """
        )


def today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def read_stats(path):
    with connect() as conn:
        pv = conn.execute("SELECT COALESCE(SUM(n), 0) FROM pv WHERE path = ?", (path,)).fetchone()[0]
        uv = conn.execute("SELECT COUNT(*) FROM uv WHERE path = ?", (path,)).fetchone()[0]
    return int(pv), int(uv)


def record_hit(path, ip):
    day = today()
    with _lock, connect() as conn:
        conn.execute(
            "INSERT INTO pv (path, day, n) VALUES (?, ?, 1) "
            "ON CONFLICT(path, day) DO UPDATE SET n = n + 1",
            (path, day),
        )
        conn.execute(
            "INSERT OR IGNORE INTO uv (path, day, ip) VALUES (?, ?, ?)", (path, day, ip)
        )


class Handler(BaseHTTPRequestHandler):
    server_version = "blog-views/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # 交给 journald 就够了，别刷 stderr
        pass

    def _ip(self):
        for header in ("X-Real-IP", "CF-Connecting-IP", "X-Forwarded-For"):
            value = self.headers.get(header)
            if value:
                return value.split(",")[0].strip()
        return self.client_address[0]

    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _target(self):
        url = urlparse(self.path)
        if url.path != "/api/views":
            return None
        values = parse_qs(url.query).get("path") or [""]
        return values[0]

    def do_GET(self):
        path = self._target()
        if path is None:
            return self._json({"error": "not found"}, 404)
        if not PATH_RE.match(path):
            return self._json({"error": "bad path"}, 400)
        pv, uv = read_stats(path)
        self._json({"pv": pv, "uv": uv})

    def do_POST(self):
        path = self._target()
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length > 1024:
            return self._json({"error": "payload too large"}, 413)
        if length:
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8", "ignore") or "{}")
                path = body.get("path") or path
            except (ValueError, AttributeError):
                return self._json({"error": "bad json"}, 400)
        if path is None:
            return self._json({"error": "not found"}, 404)
        if not PATH_RE.match(str(path)):
            return self._json({"error": "bad path"}, 400)

        ua = self.headers.get("User-Agent") or ""
        if BOT_RE.search(ua):
            pv, uv = read_stats(path)
            return self._json({"pv": pv, "uv": uv, "counted": False})

        ip = self._ip()
        key = (ip, path)
        now = time.monotonic()
        if now - _last_hit.get(key, 0) > 1.5:  # 1.5 秒内的重复请求不计
            _last_hit[key] = now
            if len(_last_hit) > 5000:
                _last_hit.clear()
            record_hit(path, ip)

        pv, uv = read_stats(path)
        self._json({"pv": pv, "uv": uv, "counted": True})


def main():
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    print(f"blog-views listening on {HOST}:{PORT}, db={DB_PATH}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
