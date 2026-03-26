#!/bin/sh
# ──────────────────────────────────────────────────────────────────────────
# Database backup script for the e-voting system.
# Runs inside the db-backup container (postgres:16-alpine).
# Creates a compressed pg_dump and prunes backups older than BACKUP_RETENTION_DAYS.
# ──────────────────────────────────────────────────────────────────────────

set -euo pipefail

BACKUP_DIR="/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/evoting_${TIMESTAMP}.sql.gz"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

echo "[$(date -Iseconds)] Starting database backup..."

# Create compressed backup
pg_dump --no-owner --no-privileges | gzip > "${BACKUP_FILE}"

FILESIZE=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || stat -f%z "${BACKUP_FILE}" 2>/dev/null)
echo "[$(date -Iseconds)] Backup created: ${BACKUP_FILE} (${FILESIZE} bytes)"

# Prune old backups
find "${BACKUP_DIR}" -name "evoting_*.sql.gz" -mtime "+${RETENTION_DAYS}" -print -delete | while read -r f; do
    echo "[$(date -Iseconds)] Pruned old backup: ${f}"
done

echo "[$(date -Iseconds)] Backup complete. Retention: ${RETENTION_DAYS} days."
