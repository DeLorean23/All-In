import os, sys, select, signal, time
pid = int(sys.argv[1])
try:
    from evdev import InputDevice, list_devices, ecodes as e
except Exception:
    sys.exit(0)

def alive():
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def stop():
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(pid, sig)
        except OSError:
            return
        for _ in range(30):
            if not alive():
                return
            time.sleep(0.1)

HOTKEYS = {e.BTN_SELECT, e.BTN_MODE}
devs = {}
for p in list_devices():
    try:
        d = InputDevice(p)
        keys = set(d.capabilities().get(e.EV_KEY, []))
        if e.BTN_START in keys and keys & HOTKEYS:
            devs[d.fd] = (d, set())
        else:
            d.close()
    except Exception:
        pass

while alive() and devs:
    r, _, _ = select.select(list(devs), [], [], 0.5)
    for fd in r:
        d, held = devs[fd]
        try:
            for ev in d.read():
                if ev.type != e.EV_KEY:
                    continue
                if ev.value == 1:
                    held.add(ev.code)
                elif ev.value == 0:
                    held.discard(ev.code)
                if e.BTN_START in held and held & HOTKEYS:
                    stop()
                    sys.exit(0)
        except OSError:
            devs.pop(fd, None)
