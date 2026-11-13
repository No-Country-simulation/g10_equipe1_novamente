#! /usr/bin/env bash
# Prepara o banco de um worktree: cria o banco app_<ticket>, aponta o .env
# para ele e roda as migrations. O servidor PostgreSQL e compartilhado e sobe
# uma vez, no checkout principal, com `docker compose up -d --wait db`.

set -euo pipefail

ticket="${1:?uso: bash scripts/worktree-setup.sh TNN}"
suffix="$(printf '%s' "$ticket" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '_')"
database="app_${suffix}"

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if [ ! -f .env ]; then
  cp .env.example .env
fi

password="$(grep -E '^POSTGRES_PASSWORD=' .env | head -n 1 | cut -d= -f2-)"
host="${POSTGRES_HOST:-localhost}"
port="${POSTGRES_PORT:-5432}"

cd backend
uv sync

WORKTREE_DB="$database" PGHOST_="$host" PGPORT_="$port" PGPASSWORD_="$password" \
  uv run python - <<'PY'
import os

import psycopg
from psycopg import sql

database = os.environ["WORKTREE_DB"]
with psycopg.connect(
    host=os.environ["PGHOST_"],
    port=os.environ["PGPORT_"],
    user="postgres",
    password=os.environ["PGPASSWORD_"],
    dbname="postgres",
    autocommit=True,
) as connection:
    exists = connection.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s", (database,)
    ).fetchone()
    if exists is None:
        connection.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database))
        )
PY
cd "$root"

url="postgresql://postgres:\${POSTGRES_PASSWORD}@${host}:${port}/${database}"
grep -v -E '^DATABASE_URL=' .env > .env.tmp
printf 'DATABASE_URL=%s\n' "$url" >> .env.tmp
mv .env.tmp .env

cd backend
uv run bash scripts/prestart.sh

echo "Banco ${database} pronto. O .env deste worktree aponta para ele."
