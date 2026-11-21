#!/usr/bin/env bash
# 把 nginx 访问日志汇总成一张静态 HTML 报表。
# --persist/--restore 让 goaccess 自己存一份累积数据库，
# 这样日志轮转、被删掉之后历史数据还在。
set -euo pipefail

OUT_DIR=/var/www/blog-stats
DB_DIR=/var/lib/goaccess

mkdir -p "$OUT_DIR" "$DB_DIR"

mapfile -t LOGS < <(ls -1 /var/log/nginx/access.log* 2>/dev/null | grep -v '\.gz$' | sort)
if [ "${#LOGS[@]}" -eq 0 ]; then
  echo "no access logs yet" >&2
  exit 0
fi

goaccess "${LOGS[@]}" \
  --log-format=COMBINED \
  --output="$OUT_DIR/index.html" \
  --ignore-crawlers \
  --persist --restore \
  --db-path="$DB_DIR" \
  --no-progress \
  --no-global-config

chmod 644 "$OUT_DIR/index.html"
echo "report written: $OUT_DIR/index.html ($(stat -c %s "$OUT_DIR/index.html") bytes)"
