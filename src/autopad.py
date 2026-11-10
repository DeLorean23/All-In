#!/usr/bin/python3
# Writes the connected controllers into the settings of a Switch 2 emulator,
# before every start, so the controller works right away (no keyboard default).
#   autopad.py <emulator id>
# Uses the SDL3 library of the emulator itself, with the same settings the
# emulator uses, so it finds the controllers exactly like the emulator does.
# Controller 1 -> player 1, controller 2 -> player 2, ... (up to 8)
# Created by DeLorean23
import ctypes
import glob
import os
import sys
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


def list_pads():
    lib = find_sdl()
    if not lib:
        log("no libSDL3 found, controllers not set")
        return []
    # same SDL settings as the emulator (they change how controllers are found)
    for k, v in {"SDL_JOYSTICK_HIDAPI_XBOX": "0", "SDL_JOYSTICK_HIDAPI_SWITCH": "0",
                 "SDL_JOYSTICK_HIDAPI_JOY_CONS": "1", "SDL_JOYSTICK_HIDAPI_STEAM": "1",
                 "SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS": "1"}.items():
        os.environ.setdefault(k, v)
    sdl = ctypes.CDLL(lib)
    sdl.SDL_Init.argtypes = [ctypes.c_uint32]
    sdl.SDL_Init.restype = ctypes.c_bool
    sdl.SDL_GetGamepads.argtypes = [ctypes.POINTER(ctypes.c_int)]
    sdl.SDL_GetGamepads.restype = ctypes.POINTER(ctypes.c_uint32)
    sdl.SDL_GetJoystickGUIDForID.argtypes = [ctypes.c_uint32]
    sdl.SDL_GetJoystickGUIDForID.restype = SDL_GUID
    sdl.SDL_GetGamepadNameForID.argtypes = [ctypes.c_uint32]
    sdl.SDL_GetGamepadNameForID.restype = ctypes.c_char_p
    sdl.SDL_GetGamepadMappingForID.argtypes = [ctypes.c_uint32]
    sdl.SDL_GetGamepadMappingForID.restype = ctypes.c_void_p
    sdl.SDL_free.argtypes = [ctypes.c_void_p]
    if not sdl.SDL_Init(0x00002000):          # SDL_INIT_GAMEPAD
        log("SDL_Init failed")
        return []
    pads = []
    count = ctypes.c_int(0)
    ids = sdl.SDL_GetGamepads(ctypes.byref(count))
    for i in range(count.value):
        jid = ids[i]
        g = sdl.SDL_GetJoystickGUIDForID(jid)
        data = bytearray(g.data)
        data[2] = data[3] = 0                  # the emulator clears the name crc
        guid = data.hex()
        name = (sdl.SDL_GetGamepadNameForID(jid) or b"").decode("utf-8", "ignore")
        mp = sdl.SDL_GetGamepadMappingForID(jid)
        mapping = ctypes.cast(mp, ctypes.c_char_p).value.decode("utf-8", "ignore") if mp else ""
        if mp:
            sdl.SDL_free(mp)
        pads.append({"guid": guid, "name": name, "inputs": parse_mapping(mapping)})
    if ids:
        sdl.SDL_free(ids)
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
    return ("range:1.000000,deadzone:0.100000,invert_y:+,invert_x:+,offset_y:-0.000000,"
            "axis_y:{},offset_x:-0.000000,axis_x:{},guid:{},port:{},engine:sdl").format(y, x, guid, port)


def main():
    pads = list_pads()
    if not pads:
        log("no controller found, settings unchanged")
        return
    cfg = configparser.RawConfigParser(strict=False, interpolation=None, delimiters=("=",))
    cfg.optionxform = str
    if os.path.exists(INI):
        try:
            cfg.read(INI, encoding="utf-8")
        except Exception as e:
            log("cannot read %s: %s" % (INI, e))
            return
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
    # players without a controller: off
    for n in range(len(pads), MAX_PLAYERS):
        if n == 0:
            continue
        cfg.set(c, "player_%d_connected\\default" % n, "false")
        cfg.set(c, "player_%d_connected" % n, "false")
    os.makedirs(os.path.dirname(INI), exist_ok=True)
    tmp = INI + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        cfg.write(f, space_around_delimiters=False)
    os.replace(tmp, INI)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("error: %s" % e)
