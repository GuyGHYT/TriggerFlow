import ctypes
import os
import platform
import atexit

_DLL_PATHS = [
    os.environ.get("VOICEMEETER_DLL"),
    r"C:\Program Files (x86)\VB\Voicemeeter\VoicemeeterRemote64.dll",
]


def _find_dll():
    for p in _DLL_PATHS:
        if not p:
            continue
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        "VoicemeeterRemote64.dll not found. Set VOICEMEETER_DLL or install Voicemeeter x64."
    )


def _load():
    if platform.architecture()[0] != "64bit":
        raise RuntimeError("Voicemeeter remote DLL requires 64-bit Python process")
    path = _find_dll()
    return ctypes.WinDLL(path)


_dll = None
_logged_in = False


def _ensure_loaded():
    global _dll
    if _dll is None:
        _dll = _load()


def _ensure_connected():
    """Ensure DLL is loaded and we're logged in to Voicemeeter Remote API."""
    global _logged_in
    _ensure_loaded()
    if not _logged_in:
        res = _dll.VBVMR_Login()
        if res != 0:
            raise RuntimeError(
                f"Voicemeeter login failed (code {res}). Ensure Voicemeeter x64 is installed and running."
            )
        _logged_in = True


def login():
    """Initialize connection to Voicemeeter. Returns True on success."""
    global _logged_in
    _ensure_loaded()
    res = _dll.VBVMR_Login()
    _logged_in = res == 0
    return _logged_in


def logout():
    global _logged_in
    _ensure_loaded()
    res = _dll.VBVMR_Logout()
    _logged_in = False
    return res == 0


@atexit.register
def _cleanup_voicemeeter():
    try:
        if _dll is not None and _logged_in:
            _dll.VBVMR_Logout()
    except Exception:
        pass


def set_parameter_float(name: str, value: float):
    """Set a Voicemeeter parameter by name. Returns True on success."""
    _ensure_connected()
    # VBVMR_SetParameterFloat(char* pParamName, float value)
    fn = _dll.VBVMR_SetParameterFloat
    fn.argtypes = [ctypes.c_char_p, ctypes.c_float]
    fn.restype = ctypes.c_int
    name_b = name.encode("utf-8")
    res = fn(name_b, ctypes.c_float(value))
    return res == 0


def get_parameter_float(name: str):
    """Get a Voicemeeter parameter value. Returns float or raises."""
    _ensure_connected()
    fn = _dll.VBVMR_GetParameterFloat
    fn.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_float)]
    fn.restype = ctypes.c_int
    out = ctypes.c_float()
    res = fn(name.encode("utf-8"), ctypes.byref(out))
    if res != 0:
        raise RuntimeError(f"VBVMR_GetParameterFloat failed for {name} (code {res})")
    return float(out.value)


def get_voicemeeter_type():
    _ensure_connected()
    fn = _dll.VBVMR_GetVoicemeeterType
    fn.argtypes = [ctypes.POINTER(ctypes.c_int)]
    fn.restype = ctypes.c_int
    out = ctypes.c_int()
    res = fn(ctypes.byref(out))
    if res != 0:
        raise RuntimeError("VBVMR_GetVoicemeeterType failed")
    return int(out.value)


def set_strip_gain(strip_index: int, gain_db: float):
    """Set strip gain (in dB) for a given strip index. Parameter name depends on Voicemeeter layout.

    Clients should supply the correct parameter name for their setup, e.g.:
      Strip[0].Gain (example)

    This helper uses the generic SetParameterFloat with a name you construct.
    """
    # Common parameter name examples can vary; caller should provide exact name
    # We'll expect caller to provide full parameter name via action params
    raise NotImplementedError("Use set_parameter_float with a full parameter name")


def toggle_mute(parameter_name: str):
    """Toggle a boolean-like parameter (0.0 or 1.0) by reading and setting it."""
    val = get_parameter_float(parameter_name)
    new = 0.0 if val >= 0.5 else 1.0
    return set_parameter_float(parameter_name, new)


def _strip_output_param(strip_index: int, bus: str) -> str:
    """Return the parameter name for a strip output bus (A1/A2/A3/B1/B2/B3).

    Note: Voicemeeter parameter names use 0-based strip indices, e.g. 'Strip[0].A1'.
    """
    bus = bus.upper()
    if bus not in ("A1", "A2", "A3", "B1", "B2", "B3"):
        raise ValueError("bus must be one of A1, A2, A3, B1, B2, B3")
    return f"Strip[{strip_index}].{bus}"


def set_strip_outputs(
    strip_index: int,
    a1: float = None,
    a2: float = None,
    a3: float = None,
    b1: float = None,
    b2: float = None,
    b3: float = None,
):
    """Set Strip output routing flags. Pass 1.0 to enable, 0.0 to disable, None to leave unchanged.

    Example: set_strip_outputs(0, a1=0.0, a2=1.0) will route strip 0 to A2 only.
    """
    if a1 is not None:
        set_parameter_float(_strip_output_param(strip_index, "A1"), float(a1))
    if a2 is not None:
        set_parameter_float(_strip_output_param(strip_index, "A2"), float(a2))
    if a3 is not None:
        set_parameter_float(_strip_output_param(strip_index, "A3"), float(a3))
    if b1 is not None:
        set_parameter_float(_strip_output_param(strip_index, "B1"), float(b1))
    if b2 is not None:
        set_parameter_float(_strip_output_param(strip_index, "B2"), float(b2))
    if b3 is not None:
        set_parameter_float(_strip_output_param(strip_index, "B3"), float(b3))
    return True


def route_strip_to_bus(strip_index: int, target_bus: str, exclusive: bool = True):
    """Route a strip to a target bus (A1/A2/A3/B1/B2/B3).

    If exclusive is True, other buses in the same family (A or B) are disabled.
    strip_index is 0-based.
    """
    target_bus = target_bus.upper()
    if target_bus not in ("A1", "A2", "A3", "B1", "B2", "B3"):
        raise ValueError("target_bus must be one of A1, A2, A3, B1, B2, B3")
    if exclusive:
        if target_bus.startswith("A"):
            set_strip_outputs(strip_index, a1=0.0, a2=0.0, a3=0.0)
        else:
            set_strip_outputs(strip_index, b1=0.0, b2=0.0, b3=0.0)
    # enable target
    set_parameter_float(_strip_output_param(strip_index, target_bus), 1.0)
    return True


def toggle_b1_b2(strip_index: int):
    """Toggle between B1 and B2 for a given strip (exclusive within B buses)."""
    import time

    # Force parameter refresh
    _ensure_connected()
    if hasattr(_dll, "VBVMR_IsParametersDirty"):
        _dll.VBVMR_IsParametersDirty()

    time.sleep(0.02)

    b1 = get_parameter_float(_strip_output_param(strip_index, "B1"))
    b2 = get_parameter_float(_strip_output_param(strip_index, "B2"))

    print(f"[toggle_b1_b2] Strip {strip_index}: B1={b1:.1f}, B2={b2:.1f}")

    if b1 >= 0.5 and b2 < 0.5:
        # switch to B2
        print(f"  → Switching to B2")
        set_strip_outputs(strip_index, b1=0.0, b2=1.0)
    elif b2 >= 0.5 and b1 < 0.5:
        # switch to B1
        print(f"  → Switching to B1")
        set_strip_outputs(strip_index, b1=1.0, b2=0.0)
    else:
        # default to B1 if neither or both
        print(f"  → Defaulting to B1")
        set_strip_outputs(strip_index, b1=1.0, b2=0.0)

    time.sleep(0.02)
    return True


def toggle_b1_b2_for_strips(strip_indices):
    """Toggle B1/B2 for each strip index provided."""
    for idx in strip_indices:
        toggle_b1_b2(int(idx))
    return True


def toggle_a1_a2(strip_index: int):
    """Toggle between A1 and A2 for a given strip (exclusive within A buses)."""
    import time

    # Force parameter refresh by calling IsParametersDirty
    _ensure_connected()
    if hasattr(_dll, "VBVMR_IsParametersDirty"):
        _dll.VBVMR_IsParametersDirty()

    time.sleep(0.02)  # Small delay to ensure Voicemeeter updates

    a1 = get_parameter_float(_strip_output_param(strip_index, "A1"))
    a2 = get_parameter_float(_strip_output_param(strip_index, "A2"))

    # Debug output
    print(f"[toggle_a1_a2] Strip {strip_index}: A1={a1:.1f}, A2={a2:.1f}")

    if a1 >= 0.5 and a2 < 0.5:
        # switch to A2
        print(f"  → Switching to A2")
        set_strip_outputs(strip_index, a1=0.0, a2=1.0)
    elif a2 >= 0.5 and a1 < 0.5:
        # switch to A1
        print(f"  → Switching to A1")
        set_strip_outputs(strip_index, a1=1.0, a2=0.0)
    else:
        # default to A1 if neither or both
        print(f"  → Defaulting to A1 (neither or both were active)")
        set_strip_outputs(strip_index, a1=1.0, a2=0.0)

    time.sleep(0.02)  # Small delay after setting
    return True


def toggle_a1_a2_for_strips(strip_indices):
    """Toggle A1/A2 for each strip index provided."""
    for idx in strip_indices:
        toggle_a1_a2(int(idx))
    return True
