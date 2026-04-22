#!/bin/bash
set -e

APP_NAME="Kaiten Installer"
DMG_NAME="Kaiten-Installer.dmg"

echo "=== Kaiten Installer build ==="

# Deps
pip3 install -r requirements.txt --quiet

# Clean
rm -rf build dist "$DMG_NAME"

# Build .app
pyinstaller \
  --windowed \
  --name "$APP_NAME" \
  --add-data "assets:assets" \
  --hidden-import customtkinter \
  --hidden-import paramiko \
  --hidden-import httpx \
  --hidden-import anthropic \
  --hidden-import gspread \
  --hidden-import google.oauth2.service_account \
  --collect-data customtkinter \
  main.py

echo "→ .app создан: dist/$APP_NAME.app"

# Build .dmg
create-dmg \
  --volname "$APP_NAME" \
  --window-pos 200 120 \
  --window-size 540 340 \
  --icon-size 128 \
  --icon "$APP_NAME.app" 150 160 \
  --hide-extension "$APP_NAME.app" \
  --app-drop-link 390 160 \
  "$DMG_NAME" \
  "dist/$APP_NAME.app"

echo "=== Готово: $DMG_NAME ==="
