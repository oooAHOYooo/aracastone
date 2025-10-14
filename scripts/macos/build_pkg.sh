#!/usr/bin/env bash
set -euo pipefail

# Build a macOS .pkg from the existing PyInstaller .app bundle.
# Prereqs: Xcode command line tools (pkgbuild), optional codesign identities.

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
APP_NAME="ArcaStone"
DIST_DIR="$ROOT_DIR/dist"
APP_BUNDLE="$DIST_DIR/$APP_NAME.app"
PKG_OUT_DIR="$DIST_DIR"
PKG_PATH="$PKG_OUT_DIR/$APP_NAME.pkg"

if [[ ! -d "$APP_BUNDLE" ]];
then
  echo "Error: $APP_BUNDLE not found. Build the app first (e.g. pyinstaller ArcaStone.spec)." >&2
  exit 1
fi

echo "Building component package: $PKG_PATH"
pkgbuild \
  --install-location /Applications \
  --component "$APP_BUNDLE" \
  "$PKG_PATH"

echo "Done: $PKG_PATH"


