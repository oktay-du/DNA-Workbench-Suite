#!/usr/bin/env bash
# Build a Linux AppImage that opens the same workspace window as dna_cli.py desktop.
# The first launch copies a writable tree beside the AppImage, matching the Windows
# EXE layout. WebKitGTK and Python 3.12 come from the host.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
OUT="${1:-$ROOT/dist}"
APPDIR="$(mktemp -d)"
cleanup() { rm -rf "$APPDIR"; }
trap cleanup EXIT

(
  cd "$HERE"
  python3 - "$APPDIR" << 'PY'
import shutil, sys
from pathlib import Path
import public_package

app = Path(sys.argv[1])
for source, target in public_package.entries():
    destination = app / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
PY
)

mkdir -p "$APPDIR/usr/share/applications"
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/sh
set -eu
HERE="$(dirname "$(readlink -f "$0")")"
if [ -n "${APPIMAGE:-}" ]; then
  DEST="$(dirname "$(readlink -f "$APPIMAGE")")/DNA-Workbench"
else
  DEST="$HERE"
fi
if [ ! -f "$DEST/DNA_Software/Launcher/dna_cli.py" ]; then
  mkdir -p "$DEST"
  cp -a "$HERE/DNA_Software" "$DEST/DNA_Software"
  if [ -d "$HERE/Samples" ]; then
    cp -a "$HERE/Samples" "$DEST/Samples"
  fi
fi
exec python3 "$DEST/DNA_Software/Launcher/dna_cli.py" desktop
EOF
chmod 755 "$APPDIR/AppRun"

cat > "$APPDIR/dna-workbench.desktop" << 'EOF'
[Desktop Entry]
Name=DNA Workbench
Exec=AppRun
Icon=dna-workbench
Type=Application
Categories=Science;Education;
Comment=Local genomics workspace
EOF
cp "$APPDIR/dna-workbench.desktop" "$APPDIR/usr/share/applications/dna-workbench.desktop"

python3 - "$APPDIR/dna-workbench.png" << 'PY'
import sys
from PIL import Image, ImageDraw
image = Image.new("RGBA", (256, 256), (17, 127, 120, 255))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((48, 48, 208, 208), radius=28, fill=(255, 255, 255, 255))
draw.ellipse((96, 96, 160, 160), fill=(17, 127, 120, 255))
image.save(sys.argv[1])
PY

TOOL="${APPIMAGETOOL:-}"
if [ -z "$TOOL" ]; then
  TOOL="$(mktemp)"
  curl --proto '=https' --tlsv1.2 -fsSL \
    -o "$TOOL" \
    https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod 755 "$TOOL"
fi

chmod -R a+rX "$APPDIR"
chmod a+rx "$APPDIR/AppRun"
mkdir -p "$OUT"
ARCH=x86_64 "$TOOL" --appimage-extract-and-run "$APPDIR" "$OUT/DNA-Workbench-x86_64.AppImage"
echo "$OUT/DNA-Workbench-x86_64.AppImage"
