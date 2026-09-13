#!/usr/bin/env bash
# ----------------------------
# Deus seja Louvado!
# ----------------------------
# Sobe lab RedMapa: MariaDB (Docker) + API Flask + Vite.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> MariaDB (Docker redmapa-mariadb-p0)"
if ! docker info >/dev/null 2>&1; then
  echo "AVISO: Docker não está rodando — API sobe sem banco (login falhará)."
  echo "  Rode em outro terminal: sudo systemctl start docker && docker start redmapa-mariadb-p0"
else
  docker start redmapa-mariadb-p0 >/dev/null || true
  for i in $(seq 1 30); do
    if docker exec redmapa-mariadb-p0 mariadb-admin ping -uroot --silent 2>/dev/null \
      || docker exec redmapa-mariadb-p0 mysqladmin ping -uroot --silent 2>/dev/null; then
      echo "    MariaDB OK em 127.0.0.1:3306"
      break
    fi
    sleep 1
  done
fi

echo "==> Backend Flask :5000"
pkill -f 'python -m BackEnd.app' 2>/dev/null || true
set -a
# shellcheck disable=SC1091
source BackEnd/.env
set +a
export REDMAPA_SGBD=mariadb ERP_PROVIDER=mock FLASK_DEBUG=0
nohup .venv/bin/python -m BackEnd.app >/tmp/redmapa-backend.log 2>&1 &
echo $! >/tmp/redmapa-backend.pid
sleep 2
curl -sf http://127.0.0.1:5000/api/v1/health | head -c 200 || true
echo

echo "==> Frontend Vite :5173"
pkill -f 'vite --host' 2>/dev/null || true
cd FrontEnd
nohup npm run dev -- --host 127.0.0.1 --port 5173 >/tmp/redmapa-frontend.log 2>&1 &
echo $! >/tmp/redmapa-frontend.pid
sleep 2
echo
echo "Abra: http://127.0.0.1:5173/"
echo "API:  http://127.0.0.1:5000/api/v1/health"
echo "Logs: /tmp/redmapa-backend.log  /tmp/redmapa-frontend.log"
