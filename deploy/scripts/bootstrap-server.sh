#!/usr/bin/env bash
# bootstrap-server.sh — one-time server setup for the Hugo blog.
# Usage (on the server, as root):
#   bash deploy/scripts/bootstrap-server.sh example.com you@example.com
#
# What it does:
#   1. installs nginx + certbot
#   2. creates /var/www/blog/{releases,current}
#   3. installs the nginx site config (domain substituted)
#   4. opens 22/80/443 in ufw
#   5. requests a Let's Encrypt certificate and turns on the HTTPS redirect

set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-}"

if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "usage: bash $0 <domain> <email-for-letsencrypt>" >&2
  exit 1
fi

if [[ $EUID -ne 0 ]]; then
  echo "please run as root (sudo bash $0 ...)" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_SRC="$SCRIPT_DIR/../nginx/blog.conf"

if [[ ! -f "$CONF_SRC" ]]; then
  echo "missing nginx template: $CONF_SRC" >&2
  echo "upload the whole deploy/ directory, not just this script." >&2
  exit 1
fi

echo "==> [1/5] installing packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nginx certbot python3-certbot-nginx rsync ufw

echo "==> [2/5] creating web root"
mkdir -p /var/www/blog/releases
chown -R www-data:www-data /var/www/blog

echo "==> [3/5] installing nginx site"
sed "s/__DOMAIN__/${DOMAIN}/g" "$CONF_SRC" > /etc/nginx/sites-available/blog
ln -sfn /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/blog
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> [4/5] firewall"
ufw allow OpenSSH >/dev/null
ufw allow 80/tcp >/dev/null
ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null
ufw status | head -n 10

echo "==> [5/5] requesting certificate"
DOMAIN_ARGS=(-d "$DOMAIN")
if getent hosts "www.$DOMAIN" >/dev/null 2>&1; then
  DOMAIN_ARGS+=(-d "www.$DOMAIN")
else
  echo "    (www.$DOMAIN has no DNS record, issuing for $DOMAIN only)"
fi

certbot --nginx \
  "${DOMAIN_ARGS[@]}" \
  --agree-tos -m "$EMAIL" \
  --redirect --non-interactive

echo
echo "done. verify:"
echo "  curl -I https://$DOMAIN/"
echo "  systemctl list-timers | grep certbot"
echo
echo "next: deploy the site from your laptop (deploy/scripts/deploy.ps1)."