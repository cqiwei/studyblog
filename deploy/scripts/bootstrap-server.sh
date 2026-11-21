#!/usr/bin/env bash
# bootstrap-server.sh — one-time server setup for the Hugo blog.
#
# Usage (on the server, as root):
#   bash deploy/scripts/bootstrap-server.sh <domain> [email-for-letsencrypt]
#   bash deploy/scripts/bootstrap-server.sh <domain> --skip-cert
#
# Works on both Debian/Ubuntu (apt + ufw, www-data) and
# RHEL/CentOS/Alma/Rocky (dnf + firewalld, nginx user).
#
# What it does:
#   1. installs nginx + certbot
#   2. creates /var/www/blog/{releases,current}
#   3. installs the nginx site config (domain substituted)
#   4. opens 22/80/443 in ufw or firewalld
#   5. requests a Let's Encrypt certificate and turns on the HTTPS redirect
#      (skipped with --skip-cert, e.g. while DNS is not pointing here yet)

set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-}"
SKIP_CERT=0
if [[ "$EMAIL" == "--skip-cert" || "${3:-}" == "--skip-cert" ]]; then
  SKIP_CERT=1
  [[ "$EMAIL" == "--skip-cert" ]] && EMAIL=""
fi

if [[ -z "$DOMAIN" ]]; then
  echo "usage: bash $0 <domain> [email-for-letsencrypt|--skip-cert]" >&2
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

# --- distro detection -----------------------------------------------------
if command -v apt-get >/dev/null 2>&1; then
  FAMILY=debian
  WEB_USER=www-data
elif command -v dnf >/dev/null 2>&1; then
  FAMILY=rhel
  WEB_USER=nginx
elif command -v yum >/dev/null 2>&1; then
  FAMILY=rhel
  WEB_USER=nginx
else
  echo "unsupported distro: neither apt-get nor dnf/yum found" >&2
  exit 1
fi

echo "==> [1/5] installing packages ($FAMILY)"
if [[ "$FAMILY" == debian ]]; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq nginx certbot python3-certbot-nginx rsync
else
  # python3-certbot-nginx lives in EPEL on RHEL-family distros
  if ! rpm -q epel-release >/dev/null 2>&1 && dnf -y install epel-release >/dev/null 2>&1; then
    echo "    installed epel-release (for certbot-nginx plugin)"
  fi
  dnf -y install nginx certbot python3-certbot-nginx rsync
fi

echo "==> [2/5] creating web root"
mkdir -p /var/www/blog/releases
chown -R "$WEB_USER":"$WEB_USER" /var/www/blog

echo "==> [3/5] installing nginx site"
if [[ "$FAMILY" == debian ]]; then
  sed "s/__DOMAIN__/${DOMAIN}/g" "$CONF_SRC" > /etc/nginx/sites-available/blog
  ln -sfn /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/blog
  rm -f /etc/nginx/sites-enabled/default
else
  sed "s/__DOMAIN__/${DOMAIN}/g" "$CONF_SRC" > /etc/nginx/conf.d/blog.conf
fi
nginx -t
systemctl enable nginx >/dev/null 2>&1 || true
systemctl restart nginx

echo "==> [4/5] firewall"
if command -v ufw >/dev/null 2>&1 && ufw status >/dev/null 2>&1; then
  ufw allow OpenSSH >/dev/null || true
  ufw allow 80/tcp >/dev/null || true
  ufw allow 443/tcp >/dev/null || true
  ufw --force enable >/dev/null || true
  ufw status | head -n 10
elif command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state >/dev/null 2>&1; then
  firewall-cmd --permanent --add-service=http --add-service=https >/dev/null
  firewall-cmd --reload >/dev/null
  firewall-cmd --list-services
  # If the site will sit behind Cloudflare (orange cloud), tighten later:
  # install cf-realip-update.sh + its timer, then this opens only CF's ranges.
  echo "    note: behind Cloudflare? see README section 7 (cfweb zone)."
else
  echo "    no active ufw/firewalld found, make sure 80/443 are reachable"
fi

echo "==> [5/5] certificate"
if [[ "$SKIP_CERT" == 1 ]]; then
  echo "    skipped (--skip-cert). run later:"
  echo "    certbot --nginx -d $DOMAIN -d www.$DOMAIN --agree-tos -m you@example.com --redirect"
  exit 0
fi

DOMAIN_ARGS=(-d "$DOMAIN")
if getent hosts "www.$DOMAIN" >/dev/null 2>&1; then
  DOMAIN_ARGS+=(-d "www.$DOMAIN")
else
  echo "    (www.$DOMAIN has no DNS record, issuing for $DOMAIN only)"
fi

EMAIL_ARGS=(--agree-tos --redirect --non-interactive)
if [[ -n "$EMAIL" ]]; then
  EMAIL_ARGS+=(-m "$EMAIL")
else
  EMAIL_ARGS+=(--register-unsafely-without-email)
fi

if ! certbot --nginx "${DOMAIN_ARGS[@]}" "${EMAIL_ARGS[@]}"; then
  echo
  echo "!! certbot failed — most likely $DOMAIN does not resolve to this server yet." >&2
  echo "   point the A record here, wait for DNS, then run:" >&2
  echo "   certbot --nginx ${DOMAIN_ARGS[*]} --agree-tos -m you@example.com --redirect" >&2
  exit 0
fi

echo
echo "done. verify:"
echo "  curl -I https://$DOMAIN/"
echo "  systemctl list-timers | grep certbot"
echo
echo "next: deploy the site from your laptop (deploy/scripts/deploy.ps1)."