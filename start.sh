#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
# One local configuration file: backend/.env
if [[ ! -f backend/.env ]]; then echo '[SALST] Missing backend/.env'; exit 1; fi
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
if ! .venv/bin/python -c 'import flask,psycopg,requests,dotenv' >/dev/null 2>&1; then
 echo '[SALST] Installing Python requirements...'
 .venv/bin/python -m pip install -r backend/requirements.txt
fi
eval "$(.venv/bin/python - <<'PYENV'
from dotenv import dotenv_values
import os,shlex
for k,v in dotenv_values('backend/.env').items():
 if k.startswith('SALST_') and v is not None and k not in os.environ:
  print('export '+k+'='+shlex.quote(v))
PYENV
)"
pids=()
cleanup(){
 trap - INT TERM EXIT
 echo '[SALST] Stopping managed processes...'
 for pid in "${pids[@]}"; do kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true; done
 sleep .4
 for pid in "${pids[@]}"; do kill -KILL -- "-$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; done
 echo '[SALST] Stopped. PostgreSQL remains running.'
}
trap cleanup INT TERM EXIT
if [[ "${1:-}" == '--reset-reports' ]]; then
 .venv/bin/python - <<'PYRESET'
import sys
sys.path.insert(0,'backend')
from server import conn,init
init()
with conn() as c:
 c.execute('TRUNCATE reports,events,notifications RESTART IDENTITY')
 c.execute("UPDATE tags SET seq=0,last_seen=NULL,mode='peace'")
PYRESET
 rm -f tags/.SALST-*.position
fi
echo '[SALST] Importing CSV test data (existing telemetry preserved)...'
.venv/bin/python backend/populate.py
echo '[SALST] Starting Flask...'
setsid .venv/bin/python -u backend/server.py & pids+=("$!")
for i in $(seq 1 60); do
 if curl -fsS http://127.0.0.1:5000/api/health >/dev/null 2>&1; then break; fi
 sleep .25
done
if ! curl -fsS http://127.0.0.1:5000/api/health >/dev/null; then echo '[SALST] Backend failed to start'; exit 1; fi
if [[ "${SALST_NGROK:-0}" == '1' ]] && command -v ngrok >/dev/null; then
 echo '[SALST] Starting ngrok HTTPS tunnel...'
 setsid ngrok http 5000 --log stdout & pids+=("$!")
else
 echo '[SALST] ngrok not started (missing or SALST_NGROK=0)'
fi
if [[ "${1:-}" != '--backend-only' ]]; then
 echo '[SALST] Starting four software tags (they wait until farm setup is saved)...'
 setsid .venv/bin/python -u tags/run_all.py & pids+=("$!")
fi
echo '[SALST] Simulator controller: http://127.0.0.1:5000/controller'
echo '[SALST] Ready: http://127.0.0.1:5000 — Ctrl+C stops all processes started by this script.'
while true; do sleep 1 & wait "$!" || break; done
