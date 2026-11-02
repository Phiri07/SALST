#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."
export SALST_DATABASE_URL="${SALST_DATABASE_URL:-dbname=salst user=bobo}"
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -q -r backend/requirements.txt
.venv/bin/python backend/populate.py
