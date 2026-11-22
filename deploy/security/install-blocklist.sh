#!/usr/bin/env bash
# 安装扫描器拦截：写 snippet + 在站点 server{} 里 include（幂等）
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SNIPPET=/etc/nginx/snippets/blog-blocklist.conf
SITE=/etc/nginx/conf.d/blog.conf
INCLUDE_LINE='include /etc/nginx/snippets/blog-blocklist.conf;'

echo "==> 安装 snippet"
install -d -m 755 /etc/nginx/snippets
install -m 644 "$SRC_DIR/nginx-blocklist.conf" "$SNIPPET"

echo "==> 在 server{} 中挂载 include（幂等）"
python3 - "$SITE" "$INCLUDE_LINE" <<'PY'
import re, sys
path, line = sys.argv[1], sys.argv[2]
src = open(path, encoding='utf-8').read()
if line in src:
    print("   已经挂载，跳过")
    sys.exit(0)

# 找到第一个 listen 443 的 server 块，把 include 插到 server_name/charset 之后
idx = src.find('listen 443')
if idx < 0:
    sys.exit("   找不到 listen 443 的 server 块，请手工挂载")

start = src.rfind('server {', 0, idx)
# 在该 server 块内的 charset 行后插入；没有就插在 server { 后
charset = src.find('charset utf-8;', start, idx)
if charset > 0:
    pos = src.find('\n', charset) + 1
else:
    pos = src.find('\n', start) + 1

new = src[:pos] + '\n    # 扫描器/漏洞探测拦截（deploy/security/install-blocklist.sh）\n    ' + line + '\n' + src[pos:]
open(path, 'w', encoding='utf-8').write(new)
print(f"   已插入到第 {src[:pos].count(chr(10)) + 1} 行")
PY

echo "==> 校验并重载"
nginx -t 2>&1
systemctl reload nginx
echo "OK 扫描器拦截已生效"