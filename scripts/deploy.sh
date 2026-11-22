#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
branch="$(git branch --show-current)"
status="$(git status --porcelain --untracked-files=normal)"
if [[ "$branch" != master || -n "$status" ]]; then
  echo "Use um checkout limpo do branch master." >&2
  exit 1
fi

git pull --ff-only origin master
commit="$(git rev-parse HEAD)"
if [[ "$commit" != "$(git rev-parse FETCH_HEAD)" ]]; then
  echo "O HEAD local difere do master remoto." >&2
  exit 1
fi

compose=(docker compose -f compose.yml -f compose.deploy.yml)
"${compose[@]}" build backend
"${compose[@]}" up -d --wait db
"${compose[@]}" run --rm --no-deps backend bash scripts/prestart.sh
"${compose[@]}" up -d --wait --remove-orphans
"${compose[@]}" ps
printf 'Commit publicado: %s\n' "$commit"
