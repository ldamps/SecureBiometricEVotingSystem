#!/bin/bash
# ── First-time Let's Encrypt certificate provisioning ─────────────────────
# Run this on the EC2 host after `docker compose up -d` to obtain the
# initial certificate. Subsequent renewals are handled automatically by
# the certbot container.
#
# Usage: DOMAIN=3.216.237.228.nip.io EMAIL=you@example.com ./scripts/init-letsencrypt.sh

set -euo pipefail

DOMAIN="${DOMAIN:?Set DOMAIN, e.g. 3.216.237.228.nip.io}"
EMAIL="${EMAIL:?Set EMAIL for Let's Encrypt notifications}"

echo "==> Requesting certificate for ${DOMAIN}..."
docker compose exec -T certbot certbot certonly \
  --webroot -w /var/www/certbot \
  --email "$EMAIL" \
  --domain "$DOMAIN" \
  --agree-tos \
  --no-eff-email \
  --non-interactive

echo "==> Reloading nginx to pick up the new certificate..."
docker compose exec -T frontend nginx -s reload

echo "==> Done! Visit https://${DOMAIN} to verify."
