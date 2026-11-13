#!/usr/bin/python3
# Controller support for emulator pop-up windows (e.g. "Use the recommended
# settings?" before a game starts). Only active while a dialog window has the
# focus, so it never sends keys into a running game.
#   D-pad left / right -> Shift+Tab / Tab   (switch between buttons)
#   D-pad up / down    -> Up / Down         (lists)
#   A                  -> Enter             (confirm the marked button)
#   B                  -> Escape            (No / Cancel)
# Usage: dialogpad.py <emulator pid>
import ctypes
import ctypes.util
import os
import select
import sys
import time

PID = int(sys.argv[1]) if len(sys.argv) > 1 else 0


def log(msg):
    print("[dialogpad] " + msg, flush=True)


def alive():
    if not PID:
        return True
    try:
        os.kill(PID, 0)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# X11: is the focused window a dialog?
# --------------------------------------------------------------------------
class X11:
    def __init__(self):
        name = ctypes.util.find_library("X11") or "libX11.so.6"
        x = ctypes.CDLL(name)
        x.XOpenDisplay.restype = ctypes.c_void_p
        x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x.XDefaultRootWindow.restype = ctypes.c_ulong
        x.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        x.XInternAtom.restype = ctypes.c_ulong
        x.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        x.XGetWindowProperty.argtypes = [
            ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_long, ctypes.c_long,
            ctypes.c_int, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_void_p)]
        x.XFree.argtypes = [ctypes.c_void_p]
        x.XGetInputFocus.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong),
                                     ctypes.POINTER(ctypes.c_int)]
        x.XQueryTree.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong),
                                 ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_void_p),
                                 ctypes.POINTER(ctypes.c_uint)]
        x.XSetErrorHandler.restype = ctypes.c_void_p
        self._err = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)(lambda d, e: 0)
        x.XSetErrorHandler(self._err)
        self.x = x
        self.d = x.XOpenDisplay(None)
        if not self.d:
            raise RuntimeError("no X display")
        self.root = x.XDefaultRootWindow(self.d)
        atom = lambda n: x.XInternAtom(self.d, n, 0)
        self.a_active = atom(b"_NET_ACTIVE_WINDOW")
        self.a_type = atom(b"_NET_WM_WINDOW_TYPE")
        self.a_dialog = atom(b"_NET_WM_WINDOW_TYPE_DIALOG")
        self.a_transient = atom(b"WM_TRANSIENT_FOR")

    def _prop(self, win, prop):
        t, f = ctypes.c_ulong(), ctypes.c_int()
        n, after = ctypes.c_ulong(), ctypes.c_ulong()
        data = ctypes.c_void_p()
        ok = self.x.XGetWindowProperty(self.d, win, prop, 0, 64, 0, 0,
                                       ctypes.byref(t), ctypes.byref(f), ctypes.byref(n),
                                       ctypes.byref(after), ctypes.byref(data))
        if ok != 0 or not data.value:
            return []
        try:
            if f.value != 32:
                return []
            arr = ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))
            return [arr[i] for i in range(n.value)]
        finally:
            self.x.XFree(data)

    def _is_dialog(self, win):
        return self.a_dialog in self._prop(win, self.a_type) or bool(self._prop(win, self.a_transient))

    def _focus_chain(self):
        """Focused window and its parents (works with and without a window manager)."""
        focus, rev = ctypes.c_ulong(), ctypes.c_int()
        self.x.XGetInputFocus(self.d, ctypes.byref(focus), ctypes.byref(rev))
        win, out = focus.value, []
        for _ in range(8):
            if win in (0, 1, self.root):
                break
            out.append(win)
            root, parent = ctypes.c_ulong(), ctypes.c_ulong()
            kids, n = ctypes.c_void_p(), ctypes.c_uint()
            if not self.x.XQueryTree(self.d, win, ctypes.byref(root), ctypes.byref(parent),
                                     ctypes.byref(kids), ctypes.byref(n)):
                break
            if kids.value:
                self.x.XFree(kids)
            win = parent.value
        return out

    def dialog_focused(self):
        act = self._prop(self.root, self.a_active)
        if act and act[0] and self._is_dialog(act[0]):
            return True
        return any(self._is_dialog(w) for w in self._focus_chain())


# --------------------------------------------------------------------------
# Controller -> keyboard
# --------------------------------------------------------------------------
def main():
    os.environ.setdefault("DISPLAY", ":0.0")
    try:
        from evdev import InputDevice, list_devices, UInput, ecodes as e
    except Exception as ex:
        log("python evdev missing, pop-up control off (%s)" % ex)
        return
    xs = None
    for _ in range(20):          # X may need a moment
        try:
            xs = X11()
            break
        except Exception:
            time.sleep(0.5)
    if xs is None:
        log("no X display, pop-up control off")
        return

    pads = {}
    for p in list_devices():
        try:
            d = InputDevice(p)
            keys = set(d.capabilities().get(e.EV_KEY, []))
            if e.BTN_SOUTH in keys and e.BTN_EAST in keys:
                pads[d.fd] = d
            else:
                d.close()
        except Exception:
            pass
    if not pads:
        log("no controller found, pop-up control off")
        return
    log("watching %d controller(s): %s" % (len(pads), ", ".join(d.name for d in pads.values())))
    try:
        ui = UInput({e.EV_KEY: [e.KEY_TAB, e.KEY_LEFTSHIFT, e.KEY_UP, e.KEY_DOWN,
                                e.KEY_ENTER, e.KEY_ESC]}, name="Dialog Pad Keyboard")
    except Exception as ex:
        log("cannot create the virtual keyboard: %s" % ex)
        return

    def tap(key, shift=False):
        if shift:
            ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
        ui.write(e.EV_KEY, key, 1); ui.syn()
        ui.write(e.EV_KEY, key, 0)
        if shift:
            ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
        ui.syn()

    hat = {e.ABS_HAT0X: 0, e.ABS_HAT0Y: 0}
    checked, active, was = 0.0, False, False
    while alive() and pads:
        r, _, _ = select.select(list(pads), [], [], 0.3)
        now = time.time()
        if now - checked > 0.25:
            try:
                active = xs.dialog_focused()
            except Exception:
                active = False
            if active != was:
                log("pop-up window " + ("found: controller -> keys" if active else "closed"))
                was = active
            checked = now
        for fd in r:
            try:
                events = list(pads[fd].read())
            except OSError:
                pads.pop(fd, None)
                continue
            if not active:
                continue
            for ev in events:
                if ev.type == e.EV_KEY and ev.value == 1:
                    if ev.code == e.BTN_SOUTH:
                        tap(e.KEY_ENTER)
                    elif ev.code == e.BTN_EAST:
                        tap(e.KEY_ESC)
                    elif ev.code == e.BTN_DPAD_LEFT:
                        tap(e.KEY_TAB, shift=True)
                    elif ev.code == e.BTN_DPAD_RIGHT:
                        tap(e.KEY_TAB)
                    elif ev.code == e.BTN_DPAD_UP:
                        tap(e.KEY_UP)
                    elif ev.code == e.BTN_DPAD_DOWN:
                        tap(e.KEY_DOWN)
                elif ev.type == e.EV_ABS and ev.code in hat:
                    old, hat[ev.code] = hat[ev.code], ev.value
                    if ev.value == 0 or ev.value == old:
                        continue
                    if ev.code == e.ABS_HAT0X:
                        tap(e.KEY_TAB, shift=ev.value < 0)
                    else:
                        tap(e.KEY_UP if ev.value < 0 else e.KEY_DOWN)
    try:
        ui.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
