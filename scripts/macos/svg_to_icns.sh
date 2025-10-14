#!/usr/bin/env bash
set -euo pipefail

# Convert SVG logo to .icns for macOS app icon.
# Requires: inkscape (or rsvg-convert) and iconutil

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
SVG="$ROOT_DIR/assets/brand/arcastone.svg"
OUT_DIR="$ROOT_DIR/dist/arcastone.iconset"
ICNS="$ROOT_DIR/dist/arcastone.icns"

mkdir -p "$OUT_DIR"

sizes=(16 32 64 128 256 512 1024)

if command -v inkscape >/dev/null 2>&1; then
  render() { inkscape -w "$1" -h "$1" "$SVG" -o "$2"; }
elif command -v rsvg-convert >/dev/null 2>&1; then
  render() { rsvg-convert -w "$1" -h "$1" "$SVG" -o "$2"; }
else
  echo "Need inkscape or rsvg-convert installed." >&2
  exit 1
fi

for s in "${sizes[@]}"; do
  render "$s" "$OUT_DIR/icon_${s}x${s}.png"
  d=$((s*2))
  render "$d" "$OUT_DIR/icon_${s}x${s}@2x.png"
done

iconutil -c icns "$OUT_DIR" -o "$ICNS"
echo "Created $ICNS"


