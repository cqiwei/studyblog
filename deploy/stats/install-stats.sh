#!/usr/bin/env bash
# 在服务器上安装「阅读数计数服务 + goaccess 统计面板」。
#
#   sudo bash install-stats.sh [源码目录] [域名]
#
# 幂等：可以反复跑。会做这几件事：
#   - 装 goaccess、httpd-tools（htpasswd）
#   - 建 blogviews 系统用户，装计数服务（127.0.0.1:8099）
#   - 装 goaccess 报表脚本 + 5 分钟定时器，输出 /var/www/blog-stats/index.html
#   - 写 nginx snippet，并在 site 的 server{} 里 include 它
#   - 生成 /stats/ 的 Basic Auth 账号（没给密码就随机一个并打印）
set -euo pipefail

SRC=${1:-/tmp/blog-stats-src}
DOMAIN=${2:-aiqivy.com}
STATS_USER=${STATS_USER:-admin}
STATS_PASS=${STATS_PASS:-}
NGINX_SITE=${NGINX_SITE:-/etc/nginx/conf.d/blog.conf}

say() { printf '\n== %s\n' "$*"; }

say "packages"
command -v goaccess >/dev/null 2>&1 || dnf install -y goaccess
command -v htpasswd >/dev/null 2>&1 || dnf install -y httpd-tools

say "service user"
id blogviews >/dev/null 2>&1 || useradd --system --home-dir /var/lib/blogviews --shell /sbin/nologin blogviews

say "files"
install -m 755 "$SRC/blog-views.py" /usr/local/bin/blog-views.py
install -m 644 "$SRC/blog-views.service" /etc/systemd/system/blog-views.service
install -m 755 "$SRC/stats-report.sh" /usr/local/bin/stats-report.sh
install -m 644 "$SRC/stats-report.service" /etc/systemd/system/stats-report.service
install -m 644 "$SRC/stats-report.timer" /etc/systemd/system/stats-report.timer

mkdir -p /var/lib/blogviews /var/www/blog-stats /etc/nginx/snippets /var/lib/goaccess
chown blogviews:blogviews /var/lib/blogviews
chmod 750 /var/lib/blogviews
install -m 644 "$SRC/nginx-blog-stats.conf" /etc/nginx/snippets/blog-stats.conf

say "htpasswd"
if [ -z "$STATS_PASS" ]; then
  STATS_PASS=$(head -c 32 /dev/urandom | base64 | tr -d '/+=' | cut -c1-16)
fi
if [ -f /etc/nginx/.htpasswd ]; then
  htpasswd -mb /etc/nginx/.htpasswd "$STATS_USER" "$STATS_PASS" >/dev/null
else
  htpasswd -cmb /etc/nginx/.htpasswd "$STATS_USER" "$STATS_PASS" >/dev/null
fi
chmod 640 /etc/nginx/.htpasswd
chown root:nginx /etc/nginx/.htpasswd 2>/dev/null || chown root:www-data /etc/nginx/.htpasswd

say "nginx include"
python3 - "$NGINX_SITE" <<'PY'
import re
import sys

path = sys.argv[1]
with open(path) as fh:
    text = fh.read()

line = "    include /etc/nginx/snippets/blog-stats.conf;\n"
text = "\n".join(l for l in text.split("\n") if "blog-stats.conf" not in l)
if not text.endswith("\n"):
    text += "\n"

# 找出所有顶层 server 块，优先插到带 listen 443 的那个里
blocks, depth, start = [], 0, None
for i, ch in enumerate(text):
    if ch == "{" and depth == 0:
        start = i
        depth = 1
    elif ch == "{" and depth > 0:
        depth += 1
    elif ch == "}" :
        depth -= 1
        if depth == 0 and start is not None:
            blocks.append((start, i))
            start = None

target = next(
    ((s, e) for s, e in blocks if re.search(r"listen\s+(\[::\]:)?443", text[s:e])),
    blocks[0] if blocks else None,
)
if target is None:
    raise SystemExit("no server block found in " + path)

s, e = target
text = text[:e] + line + text[e:]
with open(path, "w") as fh:
    fh.write(text)
print("include ensured in server block %d..%d" % (s, e))
PY

say "services"
systemctl daemon-reload
systemctl enable --now blog-views.service
systemctl restart blog-views.service
/usr/local/bin/stats-report.sh || echo "WARN: 首次报表生成失败（多半是还没有访问日志）"
systemctl enable --now stats-report.timer

say "nginx reload"
nginx -t
systemctl reload nginx

cat <<EOF

完成。

  计数接口   https://$DOMAIN/api/views?path=/posts/hello-world/
  统计面板   https://$DOMAIN/stats/
  账号       $STATS_USER
  密码       $STATS_PASS

  数据库     /var/lib/blogviews/views.db
  报表       /var/www/blog-stats/index.html（每 5 分钟刷新）
EOF
