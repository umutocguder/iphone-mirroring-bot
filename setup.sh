#!/bin/sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-/opt/homebrew/bin/python3.14}"
"$PY" -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" -q install --upgrade pip
"$DIR/.venv/bin/pip" -q install pyobjc-framework-Quartz pyobjc-framework-Vision
chmod +x "$DIR/bot" "$DIR/stop" "$DIR/mirror_bot.py"
echo "Kurulum tamam. Test: $DIR/bot windows"
