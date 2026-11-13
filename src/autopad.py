#!/usr/bin/python3
# Sets the controller of a Switch 2 emulator ONCE, the first time it starts,
# so the controller works right away (no keyboard default). After that the
# controller settings are never touched again (your own changes stay).
#   autopad.py <emulator id>
# Runs in the installer and before every start; does something only while
# player 1 is still on keyboard:
# - Eglantine: the connected controllers are written (controller 1 -> player 1,
#   ... up to 8), with the same default mapping the emulator uses itself
#   when you switch the input from keyboard to the controller
# - every other emulator: a copy of the controller settings of Eglantine,
#   or the connected controllers if Eglantine has none yet
# Created by DeLorean23
import ctypes
import glob
import os
import sys
import time
import configparser

BASE = "/userdata/system/switch2"
EMU = sys.argv[1] if len(sys.argv) > 1 else "eglantine"
INI = os.path.join(BASE, "data", EMU, "user", "config", "qt-config.ini")
MAX_PLAYERS = 8


def log(msg):
    print("[autopad] " + msg, flush=True)


def find_sdl():
    pats = [os.path.join(BASE, "emus", EMU, "usr", "lib*", "libSDL3.so*"),
            os.path.join(BASE, "emus", EMU, "**", "libSDL3.so*"),
            "/usr/lib/libSDL3.so*", "/usr/lib64/libSDL3.so*"]
    for p in pats:
        for f in sorted(glob.glob(p, recursive=True)):
            if os.path.isfile(f):
                return f
    return None


class SDL_GUID(ctypes.Structure):
    _fields_ = [("data", ctypes.c_uint8 * 16)]


# used when SDL knows a device only as joystick (no gamepad mapping): the same
# fallback the emulators use (SDL gamepad button / axis numbers)
FALLBACK = {"a": ("button", "0", ""), "b": ("button", "1", ""), "x": ("button", "2", ""),
            "y": ("button", "3", ""), "back": ("button", "4", ""), "guide": ("button", "5", ""),
            "start": ("button", "6", ""), "leftstick": ("button", "7", ""),
            "rightstick": ("button", "8", ""), "leftshoulder": ("button", "9", ""),
            "rightshoulder": ("button", "10", ""), "dpup": ("button", "11", ""),
            "dpdown": ("button", "12", ""), "dpleft": ("button", "13", ""),
            "dpright": ("button", "14", ""), "leftx": ("axis", "0", ""), "lefty": ("axis", "1", ""),
            "rightx": ("axis", "2", ""), "righty": ("axis", "3", ""),
            "lefttrigger": ("axis", "4", ""), "righttrigger": ("axis", "5", "")}


def list_pads():
    lib = find_sdl()
    if not lib:
        log("no libSDL3 found, controllers not set")
        return []
    log("SDL library: " + lib)
    # same SDL settings as the emulator (they change how controllers are found)
    for k, v in {"SDL_JOYSTICK_HIDAPI_XBOX": "0", "SDL_JOYSTICK_HIDAPI_SWITCH": "0",
                 "SDL_JOYSTICK_HIDAPI_JOY_CONS": "1", "SDL_JOYSTICK_HIDAPI_STEAM": "1",
                 "SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS": "1"}.items():
        os.environ.setdefault(k, v)
    sdl = ctypes.CDLL(lib)
    U32P = ctypes.POINTER(ctypes.c_uint32)
    sdl.SDL_Init.argtypes = [ctypes.c_uint32]
    sdl.SDL_Init.restype = ctypes.c_bool
    sdl.SDL_GetError.restype = ctypes.c_char_p
    sdl.SDL_PumpEvents.restype = None
    sdl.SDL_UpdateJoysticks.restype = None
    sdl.SDL_GetJoysticks.argtypes = [ctypes.POINTER(ctypes.c_int)]
    sdl.SDL_GetJoysticks.restype = U32P
    sdl.SDL_IsGamepad.argtypes = [ctypes.c_uint32]
    sdl.SDL_IsGamepad.restype = ctypes.c_bool
    sdl.SDL_GetJoystickGUIDForID.argtypes = [ctypes.c_uint32]
    sdl.SDL_GetJoystickGUIDForID.restype = SDL_GUID
    sdl.SDL_GetJoystickNameForID.argtypes = [ctypes.c_uint32]
    sdl.SDL_GetJoystickNameForID.restype = ctypes.c_char_p
    sdl.SDL_GetGamepadMappingForID.argtypes = [ctypes.c_uint32]
    sdl.SDL_GetGamepadMappingForID.restype = ctypes.c_void_p
    sdl.SDL_free.argtypes = [ctypes.c_void_p]
    if not sdl.SDL_Init(0x00002000 | 0x00000200):      # SDL_INIT_GAMEPAD | SDL_INIT_JOYSTICK
        log("SDL_Init failed: " + (sdl.SDL_GetError() or b"").decode("utf-8", "ignore"))
        return []

    def joysticks():
        n = ctypes.c_int(0)
        arr = sdl.SDL_GetJoysticks(ctypes.byref(n))
        ids = [arr[i] for i in range(n.value)] if arr else []
        if arr:
            sdl.SDL_free(arr)
        return ids

    # SDL finds some controllers only after a moment (e.g. HIDAPI): ask for up to 3 s
    ids, last, stable = [], None, 0
    for _ in range(30):
        sdl.SDL_PumpEvents()
        sdl.SDL_UpdateJoysticks()
        ids = joysticks()
        if ids and ids == last:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
        last = ids
        time.sleep(0.1)
    log("SDL sees %d controller(s)" % len(ids))

    pads = []
    for jid in ids:
        g = sdl.SDL_GetJoystickGUIDForID(jid)
        data = bytearray(g.data)
        data[2] = data[3] = 0                  # the emulator clears the name crc
        guid = data.hex()
        name = (sdl.SDL_GetJoystickNameForID(jid) or b"").decode("utf-8", "ignore")
        inputs, kind = {}, "joystick (standard layout)"
        if sdl.SDL_IsGamepad(jid):
            mp = sdl.SDL_GetGamepadMappingForID(jid)
            if mp:
                inputs = parse_mapping(ctypes.cast(mp, ctypes.c_char_p).value.decode("utf-8", "ignore"))
                sdl.SDL_free(mp)
                kind = "gamepad"
        if not inputs:
            inputs = dict(FALLBACK)
        log("  found: %s [%s] %s" % (name, guid, kind))
        pads.append({"guid": guid, "name": name, "inputs": inputs})
    sdl.SDL_Quit()
    return pads


def parse_mapping(mapping):
    """SDL mapping string -> {name: (type, id, hat_dir)}"""
    inputs = {}
    for el in mapping.split(",")[2:]:
        if ":" not in el:
            continue
        key, val = el.split(":", 1)
        val = val.lstrip("+-~")
        if val.startswith("b"):
            inputs[key] = ("button", val[1:], "")
        elif val.startswith("a"):
            inputs[key] = ("axis", val[1:].rstrip("~"), "")
        elif val.startswith("h") and "." in val:
            hat, mask = val[1:].split(".", 1)
            d = {"1": "up", "2": "right", "4": "down", "8": "left"}.get(mask, "up")
            inputs[key] = ("hat", hat, d)
    return inputs


# Switch button -> SDL gamepad name, the same table the emulators use for their
# own automatic mapping (by position: A = east, B = south, X = north, Y = west)
BUTTONS = {
    "button_a": "b", "button_b": "a", "button_x": "y", "button_y": "x",
    "button_dup": "dpup", "button_ddown": "dpdown", "button_dleft": "dpleft", "button_dright": "dpright",
    "button_l": "leftshoulder", "button_r": "rightshoulder",
    "button_zl": "lefttrigger", "button_zr": "righttrigger",
    "button_plus": "start", "button_minus": "back",
    "button_lstick": "leftstick", "button_rstick": "rightstick",
    "button_home": "guide",
    "button_slleft": "leftshoulder", "button_srleft": "rightshoulder",
    "button_slright": "leftshoulder", "button_srright": "rightshoulder",
}


def button_param(inp, guid, port):
    if inp is None:
        return "[empty]"
    t, i, d = inp
    if t == "button":
        return "button:{},guid:{},port:{},engine:sdl".format(i, guid, port)
    if t == "axis":
        return "threshold:0.500000,invert:+,axis:{},guid:{},port:{},engine:sdl".format(i, guid, port)
    return "hat:{},direction:{},guid:{},port:{},engine:sdl".format(i, d, guid, port)


def stick_param(inputs, xk, yk, guid, port):
    x = inputs.get(xk, ("axis", "0", ""))[1]
    y = inputs.get(yk, ("axis", "1", ""))[1]
    return ("range:1.000000,deadzone:0.150000,invert_y:+,invert_x:+,offset_y:0.000000,"
            "axis_y:{},offset_x:-0.000000,axis_x:{},guid:{},port:{},engine:sdl").format(y, x, guid, port)


TEMPLATES = ("eglantine", "eglantine-pgo")       # controller settings copied from here
MARKER = os.path.join(BASE, "data", EMU, ".controller-set")


def ini_of(emu):
    return os.path.join(BASE, "data", emu, "user", "config", "qt-config.ini")


def read_cfg(path):
    cfg = configparser.RawConfigParser(strict=False, interpolation=None, delimiters=("=",))
    cfg.optionxform = str
    if os.path.exists(path):
        cfg.read(path, encoding="utf-8")
    return cfg


def save_cfg(cfg, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        cfg.write(f, space_around_delimiters=False)
    os.replace(tmp, path)


def has_pad(cfg):
    """player 1 is set to a controller (not keyboard / nothing)"""
    if not cfg.has_option("Controls", "player_0_button_a"):
        return False
    v = cfg.get("Controls", "player_0_button_a")
    return "engine:" in v and "engine:keyboard" not in v


def done(msg):
    log(msg)
    try:
        open(MARKER, "w").close()
    except OSError:
        pass


def write_detected(cfg, pads):
    if not cfg.has_section("Controls"):
        cfg.add_section("Controls")
    c = "Controls"
    ports = {}
    for n, pad in enumerate(pads[:MAX_PLAYERS]):
        guid = pad["guid"]
        port = ports.get(guid, -1) + 1
        ports[guid] = port
        p = "player_%d_" % n
        inputs = pad["inputs"]
        for sw, sdlname in BUTTONS.items():
            cfg.set(c, p + sw + "\\default", "false")
            cfg.set(c, p + sw, '"%s"' % button_param(inputs.get(sdlname), guid, port))
        cfg.set(c, p + "lstick\\default", "false")
        cfg.set(c, p + "lstick", '"%s"' % stick_param(inputs, "leftx", "lefty", guid, port))
        cfg.set(c, p + "rstick\\default", "false")
        cfg.set(c, p + "rstick", '"%s"' % stick_param(inputs, "rightx", "righty", guid, port))
        for m in ("motionleft", "motionright"):
            cfg.set(c, p + m + "\\default", "false")
            cfg.set(c, p + m, '"guid:{},port:{},motion:0,engine:sdl"'.format(guid, port))
        cfg.set(c, p + "button_screenshot\\default", "false")
        cfg.set(c, p + "button_screenshot", "[empty]")
        cfg.set(c, p + "type\\default", "false")
        cfg.set(c, p + "type", "0")                     # Pro Controller
        cfg.set(c, p + "connected\\default", "false")
        cfg.set(c, p + "connected", "true")
        cfg.set(c, p + "vibration_enabled\\default", "true")
        cfg.set(c, p + "vibration_enabled", "true")
        log("player %d: %s (%s, port %d)" % (n + 1, pad["name"], guid, port))
    for n in range(len(pads), MAX_PLAYERS):
        if n == 0:
            continue
        cfg.set(c, "player_%d_connected\\default" % n, "false")
        cfg.set(c, "player_%d_connected" % n, "false")


def main():
    if os.path.exists(MARKER):
        return                                        # set once already: never touch again
    ini = ini_of(EMU)
    try:
        cfg = read_cfg(ini)
    except Exception as e:
        log("cannot read %s: %s" % (ini, e))
        return
    if has_pad(cfg):
        done("%s: controller already set, kept" % EMU)
        return
    # copy of the controller settings of Eglantine
    for src in TEMPLATES:
        if src == EMU:
            continue
        try:
            scfg = read_cfg(ini_of(src))
        except Exception:
            continue
        if not has_pad(scfg):
            continue
        if not cfg.has_section("Controls"):
            cfg.add_section("Controls")
        n = 0
        for k, v in scfg.items("Controls"):
            if k.startswith("player_"):
                cfg.set("Controls", k, v)
                n += 1
        save_cfg(cfg, ini)
        done("%s: controller settings copied from %s (%d entries, once)" % (EMU, src, n))
        return
    # no template: write the connected controllers
    pads = list_pads()
    if not pads:
        log("no controller found, settings unchanged (tried again on the next start)")
        return
    write_detected(cfg, pads)
    save_cfg(cfg, ini)
    done("%s: connected controller(s) set (once)" % EMU)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("error: %s" % e)
