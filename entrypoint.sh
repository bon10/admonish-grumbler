#!/bin/bash
set -e

# venv がボリュームマウントで壊れている場合、再作成
if ! python -c "import pip" 2>/dev/null; then
  echo "Recreating venv..."
  rm -rf /venv/*
  python -m venv /venv
fi

pip install --quiet -r requirements.txt

exec "$@"
