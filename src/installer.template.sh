#!/bin/bash
# All-In Installer & Update for Batocera v43
# Installs several Switch 2 emulators into one system "Switch 2":
#   Eglantine (normal + PGO)  https://github.com/Djihads80/Eglantine
#   Lichii    (normal + PGO)  https://github.com/zortos293/Lichii
#   Orchid    (normal + PGO)  https://github.com/MythosOfs/Orchid
#   Fritchii  (normal + PGO)  https://github.com/Frizti/Fritchii
# Every game can get its own emulator (hold the button on a game -> game options).
# Running it again updates every emulator that has a newer build.
# Created by DeLorean23
# https://github.com/DeLorean23/All-In
# License: MIT

set -uo pipefail

ALLIN_VERSION="@@VERSION@@"

#   id | name | GitHub repo | build
EMUS=(
    "eglantine|Eglantine|Djihads80/Eglantine|normal"
    "eglantine-pgo|Eglantine PGO|Djihads80/Eglantine|pgo"
    "lichii|Lichii|zortos293/Lichii|normal"
    "lichii-pgo|Lichii PGO|zortos293/Lichii|pgo"
    "orchid|Orchid|MythosOfs/Orchid|normal"
    "orchid-pgo|Orchid PGO|MythosOfs/Orchid|pgo"
    "fritchii|Fritchii|Frizti/Fritchii|normal"
    "fritchii-pgo|Fritchii PGO|Frizti/Fritchii|pgo"
)
DEFAULT_EMU="eglantine"

BASE="/userdata/system/switch2"
EMU_DIR="$BASE/emus"          # one unpacked AppImage per emulator
DATA_DIR="$BASE/data"         # one portable data folder per emulator (settings, shader cache)
SHARED="$BASE/shared"         # used by all emulators: saves (nand), mods (load), sd card
BACKUP="$BASE/backup"
ICONS="$BASE/icons"
TMP="$BASE/tmp"
STATE="$BASE/allin-installed.txt"
ROM_DIR="/userdata/roms/switch2"
BIOS_DIR="/userdata/bios/switch2"
KEYS_DIR="$BIOS_DIR/keys"
FW_DIR="$BIOS_DIR/firmware"
ES_CFG="/userdata/system/configs/emulationstation/es_systems_switch2.cfg"
APPDIR="/userdata/system/.local/share/applications"
OLD_EGL="/userdata/system/eglantine"      # folder of the old Eglantine Installer & Updater
LOG_DIR="/userdata/system/logs"
LOG="$LOG_DIR/allin-installer.log"

SELF="$(readlink -f "$0")"
SELF_DIR="$(dirname "$SELF")"
SELF_NAME="$(basename "$SELF")"
SELF_STEM="${SELF_NAME%.*}"

# ---------------------------------------------------------------------------
# Open a visible terminal window (Ports scripts run without one by default)
# ---------------------------------------------------------------------------
if [[ "${1:-}" != "--in-terminal" ]]; then
    mkdir -p "$LOG_DIR"
    export DISPLAY="${DISPLAY:-:0.0}"
    if command -v xterm >/dev/null 2>&1; then
        exec xterm -fullscreen -fa "Monospace" -fs 11 -bg black -fg white \
            -T "All-In Installer & Update" -e /bin/bash "$SELF" --in-terminal
    fi
    echo "xterm not found - cannot open a terminal window." >> "$LOG"
    exit 1
fi

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG") 2>&1
echo "===== $(date) ====="

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
show_banner() {
cat <<'BANNER'
                                                                                                      .    .
                                                                                                 .      *
                                                                                       _
                                   _       ____,--'`                      __|"/_____ __\"!_   .---.  *   .
                           __..--"`..-='"``                   _________.-----------.'o8888_\-" _." \       .
                     _.-""` .oooo"                        _.-"  `````.' .-"'````""\ \ '. / ""--"". __|  .
                  .-  ,`  '""'`                     ___<"_-._____ .-"_."-._________! \  "-!-``-._   \    *
                ."   /_.-_.-`      ____..--------`"'__..-----''`  \ "----'           |     ____  ".  \  .
              ,"  ` _.-._ _ ___  /'--====--.---''`      __.._      "           _____ /__ ." __ ".  \ | -- - -
          -- /  `    _/        -'--/.^^.7__/__        ." ___ '. ====\=========""''`," "`/ ."  \`||  \
            | ``    <_ -       \____...______/\_____ / `/   '.\\     \       ____.'____/  |(^ | !| _!
             \ ``     '--.      \.._______  /   `'""!|`| (^  ||`"-----===="""          |` '.__' /"`
              "-.`    `._ ._              `"'"------||  \__ .'/ ----================""" "._____. ____
                 `"Oo._     `"oo.____                `'._____' ____
                      `"==-..______. ```
                                 ````                                                         ____________
                                                                    ________________.


                     All-In Installer & Update
                       Created by DeLorean23
BANNER
printf '\n'
}

fail() {
    echo
    echo "[ERROR] $*"
    echo "Log: $LOG"
    rm -rf "$TMP"
    echo
    wait_key
    exit 1
}

# Writes the controller helper that answers y/n with A/B
write_pad_helper() {
cat > "$1" <<'PY'
import sys, select
try:
    from evdev import InputDevice, list_devices, ecodes as e
except Exception:
    sys.exit(0)
devs = []
for p in list_devices():
    try:
        d = InputDevice(p)
        keys = set(d.capabilities().get(e.EV_KEY, []))
        if e.BTN_SOUTH in keys and e.BTN_EAST in keys:
            devs.append(d)
        else:
            d.close()
    except Exception:
        pass
if not devs:
    sys.exit(0)
fds = {d.fd: d for d in devs}
while True:
    r, _, _ = select.select(list(fds), [], [], 1.0)
    for fd in r:
        try:
            for ev in fds[fd].read():
                if ev.type == e.EV_KEY and ev.value == 1:
                    if ev.code == e.BTN_SOUTH:
                        print("y", flush=True); sys.exit(0)
                    if ev.code == e.BTN_EAST:
                        print("n", flush=True); sys.exit(0)
        except OSError:
            fds.pop(fd, None)
    if not fds:
        sys.exit(0)
PY
}

ask_yes_no() {  # returns 0 for yes, 1 for no
    local prompt="$1" answer="" key pad_pid helper out
    helper="$(mktemp /tmp/allin-pad-XXXX.py)"
    out="$(mktemp /tmp/allin-pad-XXXX.txt)"
    write_pad_helper "$helper"
    python3 "$helper" > "$out" 2>/dev/null &
    pad_pid=$!
    printf '%s [y/n] (Controller: A = yes, B = no): ' "$prompt"
    while [[ -z "$answer" ]]; do
        if read -rsn1 -t 0.2 key; then
            case "$key" in
                y|Y) answer="y" ;;
                n|N) answer="n" ;;
            esac
        fi
        if [[ -z "$answer" && -s "$out" ]]; then
            answer="$(head -c1 "$out")"
        fi
    done
    kill "$pad_pid" 2>/dev/null; wait "$pad_pid" 2>/dev/null
    rm -f "$helper" "$out"
    echo "$answer"
    [[ "$answer" == "y" ]]
}

wait_key() {  # waits for Enter (keyboard) or A / B (controller)
    local key pad_pid helper out
    helper="$(mktemp /tmp/allin-pad-XXXX.py)"
    out="$(mktemp /tmp/allin-pad-XXXX.txt)"
    write_pad_helper "$helper"
    python3 "$helper" > "$out" 2>/dev/null &
    pad_pid=$!
    printf 'Press A / Enter to exit '
    while true; do
        if read -rsn1 -t 0.2 key; then break; fi
        [[ -s "$out" ]] && break
    done
    kill "$pad_pid" 2>/dev/null; wait "$pad_pid" 2>/dev/null
    rm -f "$helper" "$out"
    echo
}

extract_payload() {  # extract_payload <name> <target file>
    awk -v n="$1" '$0=="__"n"_BEGIN__"{f=1;next} $0=="__"n"_END__"{f=0} f' "$SELF" | base64 -d > "$2"
}

# Cover for this Ports entry: write it into the Ports gamelist
update_gamelist() {
python3 - "$SELF_DIR/gamelist.xml" "./$SELF_NAME" "./images/$SELF_STEM.jpg" "$SELF_STEM" <<'PY'
import os, sys
import xml.etree.ElementTree as ET
gl, path, image, name = sys.argv[1:5]
if os.path.exists(gl):
    try:
        tree = ET.parse(gl); root = tree.getroot()
    except ET.ParseError:
        sys.exit(0)
else:
    root = ET.Element("gameList"); tree = ET.ElementTree(root)
game = None
for g in root.findall("game"):
    p = g.findtext("path") or ""
    if os.path.basename(p) == os.path.basename(path):
        game = g; break
if game is None:
    game = ET.SubElement(root, "game")
    ET.SubElement(game, "path").text = path
for tag, val in (("name", name), ("image", image), ("thumbnail", image)):
    el = game.find(tag)
    if el is None:
        el = ET.SubElement(game, tag)
    el.text = val
tree.write(gl, encoding="utf-8", xml_declaration=True)
print("gamelist updated")
PY
}

emu_field() {  # emu_field <id> <1=id 2=name 3=repo 4=build>
    local e
    for e in "${EMUS[@]}"; do
        [[ "${e%%|*}" == "$1" ]] && { cut -d'|' -f"$2" <<< "$e"; return; }
    done
}
installed() { [[ -x "$EMU_DIR/$1/AppRun" ]]; }
installed_version() { head -n1 "$EMU_DIR/$1/version.txt" 2>/dev/null; }

link_dir() {  # link_dir <link> <target>: <link> points to <target>, files of a real folder are kept
    mkdir -p "$2" "$(dirname "$1")"
    if [[ -L "$1" ]]; then
        [[ "$(readlink "$1")" == "$2" ]] || ln -sfn "$2" "$1"
    elif [[ -d "$1" ]]; then
        cp -an "$1"/. "$2"/ 2>/dev/null
        rm -rf "$1"
        ln -s "$2" "$1"
    else
        rm -f "$1"
        ln -s "$2" "$1"
    fi
}

# Folders shared by all emulators
setup_shared() {
    mkdir -p "$ROM_DIR" "$KEYS_DIR" "$FW_DIR" "$SHARED/nand/system/Contents" \
             "$SHARED/load" "$SHARED/sdmc" "$SHARED/dump" "$ICONS" \
             /userdata/system/configs/emulationstation "$APPDIR"
    link_dir "$SHARED/nand/system/Contents/registered" "$FW_DIR"
}

# Portable data folder of one emulator: own settings, shared saves/keys/firmware
setup_data() {  # setup_data <id>
    local u="$DATA_DIR/$1/user"
    mkdir -p "$u/config"
    link_dir "$u/nand" "$SHARED/nand"
    link_dir "$u/load" "$SHARED/load"
    link_dir "$u/sdmc" "$SHARED/sdmc"
    link_dir "$u/dump" "$SHARED/dump"
    link_dir "$u/keys" "$KEYS_DIR"
    if [[ ! -f "$u/config/qt-config.ini" ]]; then
        cat > "$u/config/qt-config.ini" <<'INI'
[Renderer]
backend\default=false
backend=1
use_asynchronous_shaders\default=false
use_asynchronous_shaders=true
use_disk_shader_cache\default=false
use_disk_shader_cache=true
INI
    fi
}

# Takes over saves and settings of the old "Eglantine Installer & Updater" (once)
migrate_old_eglantine() {
    local old="$OLD_EGL/user" id
    [[ -d "$old" && ! -f "$BASE/.migrated" ]] || return 0
    echo "Taking over saves and settings of the old Eglantine installation..."
    [[ -d "$old/nand" ]] && cp -an "$old/nand"/. "$SHARED/nand"/ 2>/dev/null
    [[ -d "$old/load" ]] && cp -an "$old/load"/. "$SHARED/load"/ 2>/dev/null
    [[ -d "$old/sdmc" ]] && cp -an "$old/sdmc"/. "$SHARED/sdmc"/ 2>/dev/null
    if [[ -d "$old/config" ]]; then
        for id in eglantine eglantine-pgo; do
            mkdir -p "$DATA_DIR/$id/user/config"
            cp -an "$old/config"/. "$DATA_DIR/$id/user/config"/ 2>/dev/null
        done
    fi
    rm -f "$APPDIR/eglantine.desktop"
    touch "$BASE/.migrated"
    echo "Done."
    echo
}

# Helper scripts (written on every run)
write_helpers() {
    mkdir -p "$BASE"
    extract_payload HOTKEY "$BASE/hotkey.py"
    extract_payload DIALOGPAD "$BASE/dialogpad.py"

    cat > "$BASE/launch.sh" <<'SH'
#!/bin/bash
# Starts a game in the chosen emulator, fullscreen.
#   launch.sh <emulator> <core> <game>
#   game: a Switch 2 game folder (name.s2) or a file (.nsp .nsz .nup .xci .xcz .nca .nro .nso .kip)
# Emulator: the one picked for this game in EmulationStation, else the one of the
# system, else the default.
BASE="/userdata/system/switch2"
LOG="/userdata/system/logs/switch2.log"
CONF="/userdata/system/batocera.conf"
DEFAULT="__DEFAULT_EMU__"
EMU="${1:-}"; CORE="${2:-}"; ROM="${3:-}"

ok() { [[ -n "$1" && "$1" != %* && "$1" != "auto" && -x "$BASE/emus/$1/AppRun" ]]; }

if ! ok "$EMU"; then
    if ok "$CORE"; then
        EMU="$CORE"
    else
        NAME="$(basename "$ROM")"
        for key in "switch2[\"$NAME\"].emulator" "switch2[\"$NAME\"].core" "switch2.emulator" "switch2.core"; do
            v="$(grep -F -- "$key=" "$CONF" 2>/dev/null | tail -n1 | cut -d= -f2- | tr -d '\r')"
            if ok "$v"; then EMU="$v"; break; fi
        done
    fi
fi
ok "$EMU" || EMU="$DEFAULT"
if ! ok "$EMU"; then
    for d in "$BASE"/emus/*/; do
        d="$(basename "$d")"
        if ok "$d"; then EMU="$d"; break; fi
    done
fi
ok "$EMU" || { echo "No Switch 2 emulator installed." >> "$LOG"; exit 1; }

if [[ -d "$ROM" ]]; then
    MAIN="$ROM/base/exefs/main"
    [[ -f "$MAIN" ]] || MAIN="$(find "$ROM" -type f -path '*/exefs/main' 2>/dev/null | sort | head -n1)"
    [[ -f "$MAIN" ]] || { echo "No exefs/main in: $ROM" >> "$LOG"; exit 1; }
elif [[ -f "$ROM" ]]; then
    MAIN="$ROM"
else
    echo "Game not found: $ROM" >> "$LOG"; exit 1
fi

cd "$BASE/data/$EMU" || exit 1     # "user" folder here = portable data folder
{ echo "===== $(date) ====="; echo "Game: $ROM"; echo "Emulator: $EMU ($(head -n1 "$BASE/emus/$EMU/version.txt" 2>/dev/null))"; } >> "$LOG"

setsid "$BASE/emus/$EMU/AppRun" -f -g "$MAIN" >> "$LOG" 2>&1 &
PID=$!
python3 "$BASE/hotkey.py" "$PID" >> "$LOG" 2>&1 &
HK=$!
python3 "$BASE/dialogpad.py" "$PID" >> "$LOG" 2>&1 &
DP=$!
wait "$PID"
RC=$?
kill "$HK" "$DP" 2>/dev/null
exit "$RC"
SH
    sed -i "s/__DEFAULT_EMU__/$DEFAULT_EMU/" "$BASE/launch.sh"

    # opens an emulator without a game (F1 file manager -> Applications)
    cat > "$BASE/app.sh" <<'SH'
#!/bin/bash
BASE="/userdata/system/switch2"
ID="${1:-eglantine}"
cd "$BASE/data/$ID" || exit 1
exec "$BASE/emus/$ID/AppRun"
SH
    chmod +x "$BASE/launch.sh" "$BASE/app.sh"
}

# System "Switch 2" with every installed emulator, and the F1 entries
write_system() {
    local e id name first=1 emus=""
    for e in "${EMUS[@]}"; do
        id="${e%%|*}"
        name="$(cut -d'|' -f2 <<< "$e")"
        if installed "$id"; then
            setup_data "$id"
            local def=""
            [[ "$id" == "$DEFAULT_EMU" ]] && def=' default="true"'
            emus+="      <emulator name=\"$id\">
        <cores>
          <core$def>$id</core>
        </cores>
      </emulator>
"
            # F1 entry
            cat > "$APPDIR/switch2-$id.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Switch 2 $name
Comment=Switch 2 emulator $name (settings)
Exec=$BASE/app.sh $id
Path=$DATA_DIR/$id
Icon=$ICONS/$id.png
Terminal=false
Categories=Game;batocera.linux;
DESKTOP
            chmod +x "$APPDIR/switch2-$id.desktop"
        else
            rm -f "$APPDIR/switch2-$id.desktop"
        fi
    done
    cat > "$ES_CFG" <<XML
<?xml version="1.0"?>
<systemList>
  <system>
    <name>switch2</name>
    <fullname>Switch 2</fullname>
    <path>/userdata/roms/switch2</path>
    <extension>.s2 .S2 .nsp .NSP .nsz .NSZ .nup .NUP .xci .XCI .xcz .XCZ .nca .NCA .nro .NRO .nso .NSO .kip .KIP</extension>
    <command>$BASE/launch.sh "%EMULATOR%" "%CORE%" "%ROM_RAW%"</command>
    <platform>ignore</platform>
    <theme>switch2</theme>
    <emulators>
$emus    </emulators>
  </system>
</systemList>
XML
}

# ---------------------------------------------------------------------------
# Start
# ---------------------------------------------------------------------------
clear
show_banner

[[ "$(uname -m)" == "x86_64" ]] || fail "This installer only supports x86_64 PCs."
command -v curl >/dev/null 2>&1    || fail "curl not found."
command -v python3 >/dev/null 2>&1 || fail "python3 not found."

GLIBC="$(ldd --version 2>/dev/null | head -n1 | grep -oE '[0-9]+\.[0-9]+$')"
if [[ -n "$GLIBC" ]]; then
    if ! python3 -c "import sys; a=tuple(map(int,'$GLIBC'.split('.'))); sys.exit(0 if a>=(2,39) else 1)"; then
        echo "[WARNING] glibc $GLIBC found. The emulators need glibc 2.39 or newer and may not start."
        echo
    fi
fi

FRESH=1
[[ -f "$STATE" ]] && FRESH=0

# --- latest builds on GitHub -------------------------------------------------
echo "Checking for the latest builds..."
rm -rf "$TMP"
mkdir -p "$TMP" || fail "Cannot create $TMP"
REPOS=()
for e in "${EMUS[@]}"; do
    r="$(cut -d'|' -f3 <<< "$e")"
    [[ " ${REPOS[*]-} " == *" $r "* ]] || REPOS+=("$r")
done
for r in "${REPOS[@]}"; do
    f="$TMP/$(tr '/' '_' <<< "$r").json"
    if ! curl -fsSL -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/$r/releases?per_page=30" -o "$f"; then
        echo "  $r: not reachable"
        rm -f "$f"
    fi
done

# id|tag|title|url|size|file   (or id|NONE)
LATEST="$(python3 - "$TMP" "${EMUS[@]}" <<'PY'
import json, os, sys
tmp, emus = sys.argv[1], sys.argv[2:]
def ok_name(n, pgo):
    n = n.lower()
    if not n.endswith(".appimage") or "linux" not in n:
        return False
    if not any(a in n for a in ("x86_64", "x86-64", "amd64", "x64")):
        return False
    if any(a in n for a in ("aarch64", "arm64", "armhf")):
        return False
    return ("pgo" in n) == pgo
for e in emus:
    eid, _, repo, build = e.split("|")
    f = os.path.join(tmp, repo.replace("/", "_") + ".json")
    out = eid + "|NONE"
    try:
        rels = json.load(open(f))
    except Exception:
        rels = []
    if isinstance(rels, list):
        rels = [r for r in rels if isinstance(r, dict) and not r.get("draft")]
        rels.sort(key=lambda r: r.get("published_at") or "", reverse=True)
        done = False
        for r in rels:
            for a in r.get("assets", []):
                if ok_name(a.get("name", ""), build == "pgo"):
                    title = (r.get("name") or r["tag_name"]).replace("|", "/").strip()
                    out = "|".join([eid, r["tag_name"], title, a["browser_download_url"],
                                    str(a.get("size", 0)), a["name"]])
                    done = True
                    break
            if done:
                break
    print(out)
PY
)"

# --- what needs to be done ----------------------------------------------------
TODO=()
echo
printf ' %-15s %-34s %s\n' "Emulator" "Latest build" "Status"
echo " ----------------------------------------------------------------------"
while IFS='|' read -r id tag title url size file; do
    [[ -n "$id" ]] || continue
    name="$(emu_field "$id" 2)"
    cur="$(installed_version "$id")"
    if [[ "$tag" == "NONE" ]]; then
        if installed "$id"; then st="installed ($cur), no new build found"
        else st="no Linux build available"; fi
        printf ' %-15s %-34s %s\n' "$name" "-" "$st"
        continue
    fi
    if ! installed "$id"; then
        st="new"
        TODO+=("$id|$tag|$title|$url|$size|$file")
    elif [[ "$cur" != "$tag|$file" ]]; then
        st="update (installed: ${cur%%|*})"
        TODO+=("$id|$tag|$title|$url|$size|$file")
    else
        st="up to date"
    fi
    printf ' %-15s %-34s %s\n' "$name" "${title:0:34}" "$st"
done <<< "$LATEST"
echo

if (( ${#TODO[@]} == 0 )); then
    ANY=0
    for e in "${EMUS[@]}"; do installed "${e%%|*}" && ANY=1; done
    (( ANY == 1 )) || fail "No Linux builds found on GitHub (or the GitHub API limit was reached, try again later)."
    echo "up to date"
    echo
    setup_shared
    write_helpers
    write_system
    mkdir -p "$SELF_DIR/images"
    extract_payload POSTER "$SELF_DIR/images/$SELF_STEM.jpg"
    update_gamelist >> "$LOG" 2>&1
    rm -rf "$TMP"
    wait_key
    exit 0
fi

echo "----------------------------------------------------------------------"
echo " WARNING: This is an unofficial system."
echo " Future Batocera updates may affect it."
if (( FRESH == 1 )); then
    echo
    echo " After the installation Batocera needs a REBOOT."
    echo " You will be asked before it reboots."
fi
echo "----------------------------------------------------------------------"
echo

if (( FRESH == 1 )); then
    QUESTION="Install ${#TODO[@]} Switch 2 emulators?"
else
    QUESTION="Install ${#TODO[@]} new build(s)?"
fi
if ! ask_yes_no "$QUESTION"; then
    echo
    echo "Cancelled. Nothing was changed."
    echo
    rm -rf "$TMP"
    wait_key
    exit 0
fi
echo

# --- download, unpack, install --------------------------------------------------
setup_shared
migrate_old_eglantine
DONE_LIST=(); FAILED=()
n=0
for item in "${TODO[@]}"; do
    IFS='|' read -r id tag title url size file <<< "$item"
    name="$(emu_field "$id" 2)"
    n=$((n + 1))
    echo "[$n/${#TODO[@]}] $name - $title"
    app="$TMP/$id.AppImage"
    if ! curl -fL --retry 3 -# -o "$app" "$url"; then
        echo "  Download failed."; FAILED+=("$name"); rm -f "$app"; echo; continue
    fi
    got="$(stat -c %s "$app" 2>/dev/null || echo 0)"
    if [[ "$size" != "0" && "$got" != "$size" ]]; then
        echo "  Download incomplete ($got of $size bytes)."; FAILED+=("$name"); rm -f "$app"; echo; continue
    fi
    echo "  Unpacking..."
    chmod +x "$app"
    rm -rf "$TMP/squashfs-root"
    if ! ( cd "$TMP" && "$app" --appimage-extract >/dev/null 2>&1 ) || [[ ! -x "$TMP/squashfs-root/AppRun" ]]; then
        echo "  Unpacking failed."; FAILED+=("$name"); rm -rf "$app" "$TMP/squashfs-root"; echo; continue
    fi
    rm -f "$app"
    # keep the previous version as backup
    if [[ -d "$EMU_DIR/$id" ]]; then
        rm -rf "$BACKUP/$id"
        mkdir -p "$BACKUP"
        mv "$EMU_DIR/$id" "$BACKUP/$id"
    fi
    mkdir -p "$EMU_DIR"
    mv "$TMP/squashfs-root" "$EMU_DIR/$id" || { echo "  Install failed."; FAILED+=("$name"); echo; continue; }
    echo "$tag|$file" > "$EMU_DIR/$id/version.txt"
    for f in "$EMU_DIR/$id/.DirIcon" "$EMU_DIR/$id"/*.png "$EMU_DIR/$id"/*.svg; do
        if [[ -f "$f" ]]; then cp -fL "$f" "$ICONS/$id.png"; break; fi
    done
    setup_data "$id"
    DONE_LIST+=("$name")
    echo "  Installed."
    echo
done
rm -rf "$TMP"

write_helpers
write_system
echo "$ALLIN_VERSION" > "$STATE"
mkdir -p "$SELF_DIR/images"
extract_payload POSTER "$SELF_DIR/images/$SELF_STEM.jpg"

echo "======================================================================"
join() { local IFS=","; echo "$*" | sed 's/,/, /g'; }
(( ${#DONE_LIST[@]} > 0 )) && echo " Installed:  $(join "${DONE_LIST[@]}")"
(( ${#FAILED[@]} > 0 ))    && echo " FAILED:     $(join "${FAILED[@]}") (run the installer again later)"
echo
echo " Default emulator:  $(emu_field "$DEFAULT_EMU" 2)"
echo " Other emulator for one game: hold the button on the game ->"
echo "   game options -> advanced game options -> emulator"
echo
echo " Place your games in:     $ROM_DIR"
echo "   Switch 2: game folder name.s2   Files: .nsp .nsz .nup .xci .xcz .nca .nro .nso .kip"
echo " Place your firmware in:  $FW_DIR"
echo " Place your keys in:      $KEYS_DIR  (only needed for Switch 1 files)"
echo " Settings: F1 file manager -> Applications -> Switch 2 ..."
echo "======================================================================"
if [[ -f "$SELF_DIR/Eglantine Installer & Updater.sh" ]]; then
    echo
    echo " NOTE: Please delete the old \"Eglantine Installer & Updater\" from Ports."
    echo "       Running it again would replace the Switch 2 system of this installer."
fi
if [[ -d "$OLD_EGL/bin" ]]; then
    echo
    echo " NOTE: The old Eglantine folder $OLD_EGL is no longer used."
    echo "       Your saves were copied. You can delete the folder to free space."
fi
echo

if (( ${#DONE_LIST[@]} == 0 )); then
    update_gamelist >> "$LOG" 2>&1
    wait_key
    exit 1
fi

if (( FRESH == 0 )); then
    update_gamelist >> "$LOG" 2>&1
    curl -s http://127.0.0.1:1234/reloadgames >/dev/null 2>&1
    echo "Update complete"
    echo
    wait_key
    exit 0
fi

echo "Installation complete"
echo
if ! ask_yes_no "Reboot now?"; then
    update_gamelist >> "$LOG" 2>&1
    echo
    echo "No reboot. The system \"Switch 2\" appears after the next reboot."
    echo
    wait_key
    exit 0
fi

# Reboot: stop EmulationStation first so it can't overwrite the Ports gamelist.
# Runs detached, because stopping EmulationStation also closes this window.
echo "Rebooting..."
declare -f update_gamelist > /tmp/allin-gamelist.sh
FINISH="/tmp/allin-finish.sh"
cat > "$FINISH" <<SH
#!/bin/bash
LOG="$LOG"
sleep 1
if [[ -x /etc/init.d/S31emulationstation ]]; then
    /etc/init.d/S31emulationstation stop >> "\$LOG" 2>&1
else
    killall -TERM emulationstation >> "\$LOG" 2>&1
fi
for i in \$(seq 1 30); do pgrep -x emulationstation >/dev/null || break; sleep 1; done
SELF_DIR="$SELF_DIR"; SELF_NAME="$SELF_NAME"; SELF_STEM="$SELF_STEM"
source /tmp/allin-gamelist.sh
update_gamelist >> "\$LOG" 2>&1
sync
reboot
SH
chmod +x "$FINISH"
setsid nohup /bin/bash "$FINISH" >/dev/null 2>&1 < /dev/null &
sleep 1
exit 0

__POSTER_BEGIN__
@@POSTER@@
__POSTER_END__
__HOTKEY_BEGIN__
@@HOTKEY@@
__HOTKEY_END__
__DIALOGPAD_BEGIN__
@@DIALOGPAD@@
__DIALOGPAD_END__
