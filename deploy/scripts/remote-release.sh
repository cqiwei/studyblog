#!/usr/bin/env bash
# remote-release.sh — runs ON THE SERVER, piped over ssh by deploy.ps1.
# Usage: bash -s -- <release-id> <archive-path>
#
# Layout:
#   /var/www/blog/releases/<id>/   unpacked site
#   /var/www/blog/current          symlink to the active release
# Switching = repoint the symlink, so rollback is instant and atomic.

set -euo pipefail

TS="${1:?release id required}"
ARCHIVE="${2:?archive path required}"
ROOT="/var/www/blog"
KEEP=5

if [[ ! -f "$ARCHIVE" ]]; then
  echo "archive not found: $ARCHIVE" >&2
  exit 1
fi

mkdir -p "$ROOT/releases"
DEST="$ROOT/releases/$TS"
rm -rf "$DEST"
mkdir -p "$DEST"

tar -xzf "$ARCHIVE" -C "$DEST"

# Debian 用 www-data，RHEL 系用 nginx；都没有就保持 root（nginx 主进程是 root 也能读）
if id www-data >/dev/null 2>&1; then
  WEB_USER=www-data
elif id nginx >/dev/null 2>&1; then
  WEB_USER=nginx
else
  WEB_USER=root
fi
chown -R "$WEB_USER:$WEB_USER" "$DEST"

# sanity check: a release without index.html would blank the site
if [[ ! -f "$DEST/index.html" ]]; then
  echo "release is missing index.html, aborting" >&2
  rm -rf "$DEST"
  exit 1
fi

ln -sfn "$DEST" "$ROOT/current"

nginx -t 2>&1
systemctl reload nginx

rm -f "$ARCHIVE"

# keep the newest $KEEP releases, drop the rest
if [[ $(ls -1d "$ROOT"/releases/*/ 2>/dev/null | wc -l) -gt $KEEP ]]; then
  ls -1dt "$ROOT"/releases/*/ | tail -n +$((KEEP + 1)) | xargs -r rm -rf
fi

echo "deployed $TS"