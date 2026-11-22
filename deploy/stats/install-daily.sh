#!/usr/bin/env bash
# 安装每日访问摘要 + 服务器健康采样：脚本 + systemd timer（幂等）
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> 安装脚本"
install -m 755 "$SRC_DIR/stats-daily.py" /usr/local/bin/stats-daily.py
install -m 755 "$SRC_DIR/health-sample.py" /usr/local/bin/health-sample.py
install -d -m 755 /var/lib/blogstats /var/www/blog-stats/daily

echo "==> 安装 systemd 单元"
install -m 644 "$SRC_DIR/stats-daily.service" /etc/systemd/system/stats-daily.service
install -m 644 "$SRC_DIR/stats-daily.timer" /etc/systemd/system/stats-daily.timer
install -m 644 "$SRC_DIR/health-sample.service" /etc/systemd/system/health-sample.service
install -m 644 "$SRC_DIR/health-sample.timer" /etc/systemd/system/health-sample.timer
systemctl daemon-reload
systemctl enable --now stats-daily.timer >/dev/null
systemctl enable --now health-sample.timer >/dev/null

echo "==> 立刻采一次健康数据（CPU% 要等第二次采样才有值）"
systemctl start health-sample.service || true
systemctl start health-sample.service || true

echo "==> 先跑一次日报（生成昨天的）"
/usr/bin/python3 /usr/local/bin/stats-daily.py || true

echo "==> 下次触发"
systemctl list-timers stats-daily.timer health-sample.timer --no-pager | head -4
echo "OK 已安装：https://aiqivy.com/stats/daily/（含服务器健康区块）"