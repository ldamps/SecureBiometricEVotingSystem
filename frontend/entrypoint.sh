#!/bin/sh
set -e

CERT_DIR="/etc/nginx/ssl"
LE_DIR="/etc/letsencrypt/live/${DOMAIN:-localhost}"

# If Let's Encrypt certs exist, symlink them; otherwise generate self-signed fallback
if [ -f "$LE_DIR/fullchain.pem" ] && [ -f "$LE_DIR/privkey.pem" ]; then
  echo "==> Using Let's Encrypt certificate from $LE_DIR"
  ln -sf "$LE_DIR/fullchain.pem" "$CERT_DIR/fullchain.pem"
  ln -sf "$LE_DIR/privkey.pem"   "$CERT_DIR/privkey.pem"
else
  echo "==> No Let's Encrypt certificate found — generating self-signed fallback"
  openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$CERT_DIR/privkey.pem" \
    -out    "$CERT_DIR/fullchain.pem" \
    -subj   "/C=GB/ST=Aberdeen/L=Aberdeen/O=SecureBiometricEVoting/CN=${DOMAIN:-localhost}"
fi

exec "$@"
