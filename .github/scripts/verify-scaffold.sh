#!/usr/bin/env bash
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"

command -v docker >/dev/null || { echo "Smoke test requires Docker" >&2; exit 1; }
docker compose version >/dev/null

project="skkup-smoke-$(date +%s)-$$"
if [ "$project" = "skkup-v2" ]; then
  echo "Refusing to use the standard Compose project name" >&2
  exit 1
fi

read -r db_port api_port web_port < <(python3 - <<'PY'
import secrets

ports = set()
while len(ports) < 3:
    ports.add(30000 + secrets.randbelow(30000))
print(*ports)
PY
)
export DB_HOST_PORT="$db_port" API_HOST_PORT="$api_port" WEB_PORT="$web_port"

compose=(docker compose --env-file /dev/null --project-name "$project" --file compose.yaml)
cleanup() {
  status=$?
  if [ "$status" -ne 0 ]; then
    "${compose[@]}" ps --all || true
    "${compose[@]}" logs || true
  fi
  "${compose[@]}" down --volumes --remove-orphans || true
  return "$status"
}
trap cleanup EXIT

"${compose[@]}" up --detach --build
"${compose[@]}" wait migrate
ready=false
# A fresh Next.js production server can need over a minute on a cold GitHub
# runner after the image is built. Poll until a wall-clock deadline, and bound
# each probe so an unresponsive service cannot leave this script hanging.
run_probe() {
  python3 - "$@" <<'PY'
import subprocess
import sys

try:
    subprocess.run(sys.argv[1:], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=4)
except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
    sys.exit(1)
PY
}

deadline=$((SECONDS + 180))
while (( SECONDS < deadline )); do
  if run_probe "${compose[@]}" exec -T db pg_isready -t 2 -U skkup_v2 -d skkup_v2 \
    && run_probe "${compose[@]}" exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=2)" \
    && run_probe "${compose[@]}" exec -T web node -e "fetch('http://127.0.0.1:3000/', {signal: AbortSignal.timeout(2500)}).then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"; then
    ready=true
    break
  fi
  remaining=$((deadline - SECONDS))
  if (( remaining > 0 )); then sleep "$((remaining < 2 ? remaining : 2))"; fi
done
if [ "$ready" != true ]; then
  echo "Scaffold services did not become ready within 180 seconds" >&2
  exit 1
fi

revision="$("${compose[@]}" exec -T db psql -U skkup_v2 -d skkup_v2 -Atc 'SELECT version_num FROM alembic_version;')"
test "$revision" = "0001_empty_baseline"

"${compose[@]}" run --rm migrate alembic -c alembic.ini downgrade base
version_rows="$("${compose[@]}" exec -T db psql -U skkup_v2 -d skkup_v2 -Atc 'SELECT COUNT(*) FROM alembic_version;')"
product_tables="$("${compose[@]}" exec -T db psql -U skkup_v2 -d skkup_v2 -Atc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name <> 'alembic_version';")"
test "$version_rows" = "0"
test "$product_tables" = "0"
"${compose[@]}" run --rm migrate alembic -c alembic.ini upgrade head
revision="$("${compose[@]}" exec -T db psql -U skkup_v2 -d skkup_v2 -Atc 'SELECT version_num FROM alembic_version;')"
test "$revision" = "0001_empty_baseline"

echo "Scaffold smoke test passed (isolated project: $project; cleanup removes only its volume)"
