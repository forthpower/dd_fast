#!/usr/bin/env bash
set -euo pipefail

# macOS desktop app build using PyInstaller

APP_NAME="dd_fast"
ENTRY="app.py"

# Ensure dependencies
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install --upgrade pyinstaller >/dev/null 2>&1

# Build .app bundle
pyinstaller \
  --noconfirm \
  --windowed \
  --name "$APP_NAME" \
  --add-data "file_duplicator.py:." \
  "$ENTRY"

echo
echo "Build finished. You can find the app here: dist/$APP_NAME.app"
echo "The app will open as a desktop application when launched."

