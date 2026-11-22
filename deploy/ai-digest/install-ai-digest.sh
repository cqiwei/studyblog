#!/usr/bin/env bash
# AI 前哨日报安装脚本（在服务器上跑）
#   bash install-ai-digest.sh <源码目录>
# 源码目录 = 含 ai-digest.py / *.service / *.timer 的目录（先 scp 上来）
set -euo pipefail

SRC_DIR="${1:-/tmp/ai-digest-src}"
REPO_URL="${REPO_URL:-git@github.com:cqiwei/studyblog.git}"
REPO_DIR="${REPO_DIR:-/opt/blogrepo}"
KEY_FILE="${KEY_FILE:-/root/.ssh/blog_deploy_key}"
HUGO_VERSION="${HUGO_VERSION:-0.170.1}"

say() { echo "== $*"; }

say "文件"
install -m 755 "$SRC_DIR/ai-digest.py" /usr/local/bin/ai-digest.py
install -m 755 "$SRC_DIR/lab-trending.py" /usr/local/bin/lab-trending.py
install -m 644 "$SRC_DIR/ai-digest.service" /etc/systemd/system/
install -m 644 "$SRC_DIR/ai-digest.timer" /etc/systemd/system/
install -m 644 "$SRC_DIR/lab-trending.service" /etc/systemd/system/
install -m 644 "$SRC_DIR/lab-trending.timer" /etc/systemd/system/

say "hugo"
if [ ! -x /usr/local/bin/hugo ] || ! /usr/local/bin/hugo version | grep -q "$HUGO_VERSION"; then
  dnf install -y git rsync >/dev/null
  curl -fsSL "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_${HUGO_VERSION}_linux-amd64.tar.gz" -o /tmp/hugo.tgz
  tar -xzf /tmp/hugo.tgz -C /tmp hugo
  install -m 755 /tmp/hugo /usr/local/bin/hugo
fi
/usr/local/bin/hugo version

say "部署密钥（git push 用）"
if [ ! -f "$KEY_FILE" ]; then
  mkdir -p /root/.ssh && chmod 700 /root/.ssh
  ssh-keygen -t ed25519 -N '' -C 'aiqivy.com ai-digest' -f "$KEY_FILE" -q
fi
ssh-keyscan -t ed25519 github.com > /root/.ssh/known_hosts.github 2>/dev/null
if ! grep -q github.com /root/.ssh/known_hosts 2>/dev/null; then
  cat /root/.ssh/known_hosts.github >> /root/.ssh/known_hosts
fi
chmod 600 "$KEY_FILE"*

# ssh 只在访问 github.com 时用部署密钥
cat > /root/.ssh/config <<EOF
Host github.com
  User git
  IdentityFile $KEY_FILE
  IdentitiesOnly yes
  UserKnownHostsFile /root/.ssh/known_hosts
EOF
chmod 600 /root/.ssh/config

echo "-----BEGIN 把下面这行公钥加到 GitHub 仓库 -----"
cat "$KEY_FILE.pub"
echo "-----END（Settings → Deploy keys → Add deploy key，勾选 Allow write access）-----"

say "克隆仓库"
if [ ! -d "$REPO_DIR/.git" ]; then
  git clone "$REPO_URL" "$REPO_DIR" || \
    echo "!! 克隆失败：先把上面的公钥加到 GitHub（Deploy key，允许写入）后手动执行 git clone $REPO_URL $REPO_DIR"
fi
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" config user.name ai-digest
  git -C "$REPO_DIR" config user.email digest@aiqivy.com
  echo "仓库就绪: $(git -C "$REPO_DIR" log --oneline -1)"
fi

say "去重数据库目录"
install -d -m 755 /var/lib/ai-digest

say "systemd"
systemctl daemon-reload
systemctl enable --now ai-digest.timer lab-trending.timer
systemctl list-timers ai-digest.timer lab-trending.timer --no-pager | head -8

say "完成。凭据写在这里：/etc/ai-digest.conf（600）"
# 幂等：已填过凭据就不覆盖
if [ ! -s /etc/ai-digest.conf ] || ! grep -qE '^LLM_API_KEY=.+' /etc/ai-digest.conf; then
cat > /etc/ai-digest.conf <<'EOF'
# AI 前哨日报配置（KEY=VALUE，不要加引号，注释要整行写）
# LLM 用 OpenAI 兼容接口；默认魔搭 API-Inference（每天免费额度）
LLM_API_KEY=
# LLM_API_KEY=ms-xxxxxx            ← 魔搭令牌（modelscope.cn/my/myaccesstoken）
# LLM_BASE_URL=https://api-inference.modelscope.cn/v1
# LLM_MODEL=ZhipuAI/GLM-5.2
# 换 DeepSeek 官方时：
# LLM_BASE_URL=https://api.deepseek.com/v1
# LLM_MODEL=deepseek-chat
# GITHUB_TOKEN=（可选，GitHub API 限额更高时用）
# CF_API_TOKEN=（可选，有权限时发布后自动清理 Cloudflare 缓存）
# AI_RSSHUB_URLS=（可选，一行多个用逗号分隔）
EOF
chmod 600 /etc/ai-digest.conf
fi
echo "跑一次试试：systemctl start ai-digest && journalctl -u ai-digest -n 30"
