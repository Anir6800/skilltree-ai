#!/usr/bin/env bash
# SkillTree AI — PostgreSQL backup (run BEFORE migration / cutover)
# Usage:  ./scripts/backup_postgres.sh
# Requires: pg_dump on PATH. Reads DATABASE_URL from environment.
set -euo pipefail

STAMP="$(date +%Y%m%d_%H%M%S)"
DIR="$(dirname "$0")/../_backups"
mkdir -p "$DIR"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL not set."
  SQLITE="$(dirname "$0")/../db.sqlite3"
  if [[ -f "$SQLITE" ]]; then
    cp "$SQLITE" "$DIR/db_${STAMP}.sqlite3"
    echo "SQLite snapshot saved to _backups/db_${STAMP}.sqlite3"
  fi
  exit 0
fi

OUT="$DIR/skilltree_pg_${STAMP}.dump"
echo "Dumping PostgreSQL to $OUT ..."
pg_dump --dbname="$DATABASE_URL" -Fc -f "$OUT"
echo "Backup complete: $OUT"
echo "Restore with:  pg_restore --clean --dbname=\$DATABASE_URL $OUT"
