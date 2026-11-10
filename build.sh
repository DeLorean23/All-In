#!/bin/bash
# Builds the ready-to-use installer and its ZIP into dist/
#   dist/All-In Installer & Update.zip
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
DIST="$ROOT/dist"
NAME="All-In Installer & Update"
VERSION="${1:-$(date +%Y.%m.%d)}"

rm -rf "$DIST"
STAGE="$DIST/stage"
mkdir -p "$STAGE/roms/ports/images"
python3 - "$ROOT" "$STAGE/roms/ports/$NAME.sh" "$VERSION" <<'PY'
import base64, sys
root, out, ver = sys.argv[1:4]
def b64(p):
    return base64.encodebytes(open(p, "rb").read()).decode().rstrip("\n")
t = open(root + "/src/installer.template.sh").read()
for key, val in {"@@VERSION@@": ver,
                 "@@POSTER@@": b64(root + "/assets/cover.jpg"),
                 "@@HOTKEY@@": b64(root + "/src/hotkey.py"),
                 "@@DIALOGPAD@@": b64(root + "/src/dialogpad.py")}.items():
    assert key in t, key
    t = t.replace(key, val)
assert "@@" not in t
open(out, "w", newline="\n").write(t)
PY
chmod +x "$STAGE/roms/ports/$NAME.sh"
bash -n "$STAGE/roms/ports/$NAME.sh"
cp "$ROOT/assets/cover.jpg" "$STAGE/roms/ports/images/$NAME.jpg"
cp "$ROOT/README.md" "$STAGE/README.txt"
cp "$ROOT/LIESMICH.md" "$STAGE/LIESMICH.txt"
(cd "$STAGE" && zip -qr "$DIST/$NAME.zip" README.txt LIESMICH.txt roms)
cp "$STAGE/roms/ports/$NAME.sh" "$DIST/"
rm -rf "$STAGE"
echo "built: dist/$NAME.zip"
