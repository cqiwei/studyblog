#!/usr/bin/env bash
# 安装每日访问摘要：脚本 + systemd timer（幂等）
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> 安装脚本"
install -m 755 "$SRC_DIR/stats-daily.py" /usr/local/bin/stats-daily.py
install -d -m 755 /var/lib/blogstats /var/www/blog-stats/daily

echo "==> 安装 systemd 单元"
install -m 644 "$SRC_DIR/stats-daily.service" /etc/systemd/system/stats-daily.service
install -m 644 "$SRC_DIR/stats-daily.timer" /etc/systemd/system/stats-daily.timer
systemctl daemon-reload
systemctl enable --now stats-daily.timer >/dev/null

echo "==> 先跑一次（生成昨天的）"
/usr/bin/python3 /usr/local/bin/stats-daily.py || true

echo "==> 下次触发"
systemctl list-timers stats-daily.timer --no-pager | head -3
echo "OK 每日摘要已安装：https://aiqivy.com/stats/daily/"