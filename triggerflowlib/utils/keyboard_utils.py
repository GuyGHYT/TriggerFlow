import pyautogui
import time
import platform
import ctypes

try:
    import keyboard as _kb
except Exception:
    _kb = None

# Tweak PyAutoGUI behavior for reliability
pyautogui.FAILSAFE = False  # avoid abort if mouse hits top-left
pyautogui.PAUSE = 0.02  # small delay between actions


def press_keybind(keys):
    """
    Press a combination of keys.
    'keys' should be a list of strings, e.g., ['ctrl', 'alt', 'shift', 'f12']

    Strategy (prioritized for Discord compatibility):
    1) On Windows, use SendInput with HARDWARE flag (most reliable for Discord)
    2) Fall back to PyAutoGUI.hotkey
    3) As a last resort, synthesize with keyDown/keyUp using PyAutoGUI.
    """
    if not keys or not isinstance(keys, (list, tuple)):
        print("press_keybind: invalid keys")
        return False
    norm = [str(k).strip().lower() for k in keys]

    # Try 'keyboard' library if available (often works well for Discord)
    if _kb is not None and platform.system() == "Windows":
        try:
            combo = _to_keyboard_combo(norm)
            _kb.send(combo, do_press=True, do_release=True)
            print(f"✓ Pressed keybind via keyboard lib: {combo}")
            return True
        except Exception as e:
            print(f"⚠ keyboard lib send failed: {e}")

    # Try Windows SendInput FIRST (Discord compatibility)
    if platform.system() == "Windows":
        ok = _win_sendinput_combo(norm)
        if ok:
            print(f"✓ Pressed keybind via SendInput: {' + '.join(norm)}")
            return True
        else:
            print("⚠ SendInput failed, trying PyAutoGUI...")

    # PyAutoGUI fallback
    try:
        pyautogui.hotkey(*norm, interval=0.05)
        print(f"✓ Pressed keybind via PyAutoGUI: {' + '.join(norm)}")
        return True
    except Exception as e:
        print(f"⚠ PyAutoGUI hotkey failed: {e}")

    # Final fallback: explicit keyDown/keyUp sequence
    try:
        mods = [
            k
            for k in norm
            if k
            in (
                "ctrl",
                "alt",
                "shift",
                "win",
                "lctrl",
                "rctrl",
                "lalt",
                "ralt",
                "lshift",
                "rshift",
                "lwin",
                "rwin",
            )
        ]
        mains = [k for k in norm if k not in mods]
        for m in mods:
            pyautogui.keyDown(m)
            time.sleep(0.01)
        for k in mains or [""]:
            if k:
                pyautogui.press(k)
                time.sleep(0.01)
        for m in reversed(mods):
            pyautogui.keyUp(m)
            time.sleep(0.01)
        print(f"✓ Pressed keybind via manual sequence: {' + '.join(norm)}")
        return True
    except Exception as e:
        print(f"✗ All methods failed: {e}")
        return False


def _to_keyboard_combo(keys):
    """Map our key tokens to 'keyboard' library combo string.

    Examples:
    ['ctrl','shift','m'] -> 'ctrl+shift+m'
    ['lctrl','rshift','f10'] -> 'left ctrl+right shift+f10'
    """
    name_map = {
        "lctrl": "left ctrl",
        "rctrl": "right ctrl",
        "lshift": "left shift",
        "rshift": "right shift",
        "lalt": "left alt",
        "ralt": "right alt",
        "lwin": "left windows",
        "rwin": "right windows",
        "win": "windows",
    }
    parts = []
    for k in keys:
        parts.append(name_map.get(k, k))
    return "+".join(parts)


def mute_mic_keybind():
    # A complex keybind that is unlikely to be pressed accidentally
    return press_keybind(["ctrl", "alt", "shift", "f10"])


def deafen_headset_keybind():
    # A different complex keybind
    return press_keybind(["ctrl", "alt", "shift", "f11"])


# -------------------------
# Windows SendInput fallback
# -------------------------


def _vk_code_for(key: str):
    k = key.lower()
    vk_map = {
        "ctrl": 0x11,  # VK_CONTROL
        "control": 0x11,
        "lctrl": 0xA2,  # VK_LCONTROL
        "rctrl": 0xA3,  # VK_RCONTROL
        "alt": 0x12,  # VK_MENU
        "lalt": 0xA4,  # VK_LMENU
        "ralt": 0xA5,  # VK_RMENU
        "shift": 0x10,  # VK_SHIFT
        "lshift": 0xA0,  # VK_LSHIFT
        "rshift": 0xA1,  # VK_RSHIFT
        "win": 0x5B,  # VK_LWIN
        "lwin": 0x5B,  # VK_LWIN
        "rwin": 0x5C,  # VK_RWIN
    }
    if k in vk_map:
        return vk_map[k]
    if k.startswith("f") and k[1:].isdigit():
        n = int(k[1:])
        if 1 <= n <= 24:
            return 0x70 + (n - 1)  # VK_F1 .. VK_F24
    if len(k) == 1:
        ch = k.upper()
        o = ord(ch)
        if 0x30 <= o <= 0x39 or 0x41 <= o <= 0x5A:
            return o  # digits 0-9, letters A-Z
    return None


def _win_sendinput_combo(keys):
    try:
        user32 = ctypes.windll.user32
    except Exception:
        return False

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_SCANCODE = 0x0008

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.c_ushort),
            ("wScan", ctypes.c_ushort),
            ("dwFlags", ctypes.c_uint),
            ("time", ctypes.c_uint),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        class _I(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]

        _anonymous_ = ("i",)
        _fields_ = [("type", ctypes.c_uint), ("i", _I)]

    # Map VK to scancode
    user32.MapVirtualKeyW.restype = ctypes.c_uint
    user32.MapVirtualKeyW.argtypes = [ctypes.c_uint, ctypes.c_uint]

    def send_key(vk, up=False):
        sc = user32.MapVirtualKeyW(vk, 0)  # MAPVK_VK_TO_VSC
        # Use VK code directly instead of scancode for better Discord compatibility
        flags = 0
        # Right-side modifiers and some keys require EXTENDED flag
        if vk in (0xA3, 0xA5, 0x5C):  # RCTRL, RALT, RWIN
            flags |= KEYEVENTF_EXTENDEDKEY
        if up:
            flags |= KEYEVENTF_KEYUP
        ki = KEYBDINPUT(wVk=vk, wScan=sc, dwFlags=flags, time=0, dwExtraInfo=None)
        inp = INPUT(type=INPUT_KEYBOARD, i=INPUT._I(ki=ki))
        n = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        return n == 1

    mods = [
        k
        for k in keys
        if k
        in (
            "ctrl",
            "alt",
            "shift",
            "win",
            "lctrl",
            "rctrl",
            "lalt",
            "ralt",
            "lshift",
            "rshift",
            "lwin",
            "rwin",
        )
    ]
    mains = [k for k in keys if k not in mods]

    # Press modifiers down
    for m in mods:
        vk = _vk_code_for(m)
        if vk is None or not send_key(vk, up=False):
            return False
        time.sleep(0.01)  # Increased delay for Discord recognition

    # Tap main keys
    if not mains:
        mains = [""]
    for k in mains:
        if not k:
            continue
        vk = _vk_code_for(k)
        if vk is None or not send_key(vk, up=False) or not send_key(vk, up=True):
            return False
        time.sleep(0.02)  # Increased delay

    # Release modifiers in reverse
    for m in reversed(mods):
        vk = _vk_code_for(m)
        if vk is None or not send_key(vk, up=True):
            return False
        time.sleep(0.01)  # Increased delay

    return True
