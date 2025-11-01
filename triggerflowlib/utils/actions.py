from triggerflowlib.plugins import spotify, voicemeeter, usercommands, voicemod
from triggerflowlib.utils import keyboard_utils


# Handlers accept a params dict (may be empty) and perform the action.
def _spotify_play_playlist(params: dict):
    uri = params.get("playlist_uri")
    if not uri:
        raise KeyError("spotify_play_playlist requires playlist_uri")
    return spotify.play_playlist(uri)


def _mute_mic(_params: dict):
    return keyboard_utils.mute_mic_keybind()


def _deafen_headset(_params: dict):
    return keyboard_utils.deafen_headset_keybind()


def _press_keys(params: dict):
    keys = params.get("keys")
    if not keys:
        raise KeyError("key_press requires keys list")
    return keyboard_utils.press_keybind(keys)


def _vm_set_parameter(params: dict):
    # expects {'parameter': 'Strip[0].Mute', 'value': 1.0}
    param = params.get("parameter")
    if not param:
        raise KeyError("voicemeeter_set_parameter requires parameter name")
    if "value" not in params:
        raise KeyError("voicemeeter_set_parameter requires value")
    val = params["value"]
    return voicemeeter.set_parameter_float(param, float(val))


def _vm_toggle(params: dict):
    param = params.get("parameter")
    if not param:
        raise KeyError("voicemeeter_toggle requires parameter name")
    return voicemeeter.toggle_mute(param)


def _vm_route_input(params: dict):
    # expects {'strip_index': 0, 'target_bus': 'A2', 'exclusive': True}
    if "strip_index" not in params:
        raise KeyError("voicemeeter_route_input requires strip_index")
    if "target_bus" not in params:
        raise KeyError("voicemeeter_route_input requires target_bus")
    strip_index = int(params["strip_index"])
    target_bus = str(params["target_bus"])
    exclusive = bool(params.get("exclusive", True))
    return voicemeeter.route_strip_to_bus(strip_index, target_bus, exclusive=exclusive)


ACTION_HANDLERS = {
    "spotify_play_playlist": _spotify_play_playlist,
    "mute_mic": _mute_mic,
    "deafen_headset": _deafen_headset,
    "key_press": _press_keys,
    "voicemeeter_set_parameter": _vm_set_parameter,
    "voicemeeter_toggle": _vm_toggle,
    "voicemeeter_route_input": _vm_route_input,
}


def _vm_toggle_b_pair(params: dict):
    """Toggle B1/B2 for two strips, typically an input and the first virtual input.

    expects: { 'strips': [<int>, <int>] }
    """
    strips = params.get("strips")
    if not strips or not isinstance(strips, (list, tuple)) or len(strips) != 2:
        raise KeyError(
            "voicemeeter_toggle_b_pair requires 'strips' list of two indices"
        )
    return voicemeeter.toggle_b1_b2_for_strips(strips)


# register the new action
ACTION_HANDLERS["voicemeeter_toggle_b_pair"] = _vm_toggle_b_pair


def _vm_toggle_a_pair(params: dict):
    """Toggle A1/A2 for two strips, typically an input and the first virtual input.

    expects: { 'strips': [<int>, <int>] }
    """
    strips = params.get("strips")
    if not strips or not isinstance(strips, (list, tuple)) or len(strips) != 2:
        raise KeyError(
            "voicemeeter_toggle_a_pair requires 'strips' list of two indices"
        )
    return voicemeeter.toggle_a1_a2_for_strips(strips)


ACTION_HANDLERS["voicemeeter_toggle_a_pair"] = _vm_toggle_a_pair


def _user_command(params: dict):
    """Dynamically calls a function from the usercommands module."""
    command_name = params.get("command_name")
    if not command_name:
        raise KeyError("user_command requires 'command_name'")

    # Get the function from the usercommands module
    func_to_call = getattr(usercommands, command_name, None)
    if not func_to_call or not callable(func_to_call):
        raise AttributeError(
            f"'{command_name}' is not a callable function in usercommands module."
        )

    # Extract the function's parameters from the 'parameters' sub-dictionary
    func_params = params.get("parameters", {})

    return func_to_call(**func_params)


ACTION_HANDLERS["user_command"] = _user_command


def _voicemod_select_voice(params: dict):
    """Select a Voicemod voice by ID."""
    voice_id = params.get("voice_id")
    if not voice_id:
        raise KeyError("voicemod_select_voice requires 'voice_id'")
    return voicemod.select_voice(voice_id)


def _voicemod_toggle_voice_changer(params: dict):
    """Toggle Voicemod voice changer on/off."""
    return voicemod.toggle_voice_changer()


def _voicemod_toggle_mute(params: dict):
    """Toggle Voicemod microphone mute."""
    return voicemod.toggle_mute()


def _voicemod_mute(params: dict):
    """Mute Voicemod microphone."""
    return voicemod.mute()


def _voicemod_unmute(params: dict):
    """Unmute Voicemod microphone."""
    return voicemod.unmute()


def _voicemod_toggle_hear_myself(params: dict):
    """Toggle Voicemod 'Hear Myself' feature."""
    return voicemod.toggle_hear_myself()


def _voicemod_play_sound(params: dict):
    """Play a Voicemod sound/meme."""
    sound_file = params.get("sound_file")
    if not sound_file:
        raise KeyError("voicemod_play_sound requires 'sound_file'")
    loop = params.get("loop", False)
    return voicemod.play_sound(sound_file, loop=loop)


def _voicemod_stop_sounds(params: dict):
    """Stop all Voicemod sounds."""
    return voicemod.stop_all_sounds()


ACTION_HANDLERS["voicemod_select_voice"] = _voicemod_select_voice
ACTION_HANDLERS["voicemod_toggle_voice_changer"] = _voicemod_toggle_voice_changer
ACTION_HANDLERS["voicemod_toggle_mute"] = _voicemod_toggle_mute
ACTION_HANDLERS["voicemod_mute"] = _voicemod_mute
ACTION_HANDLERS["voicemod_unmute"] = _voicemod_unmute
ACTION_HANDLERS["voicemod_toggle_hear_myself"] = _voicemod_toggle_hear_myself
ACTION_HANDLERS["voicemod_play_sound"] = _voicemod_play_sound
ACTION_HANDLERS["voicemod_stop_sounds"] = _voicemod_stop_sounds


def run_action(action: dict):
    """Run a declarative action dict.

    action: {'type': <str>, ...params}
    """
    if not isinstance(action, dict):
        raise ValueError("action must be a mapping")
    atype = action.get("type")
    if not atype:
        raise KeyError("action missing 'type' field")
    handler = ACTION_HANDLERS.get(atype)
    if not handler:
        raise KeyError(f"unsupported action type: {atype}")
    # copy params and remove type
    params = dict(action)
    params.pop("type", None)
    return handler(params)


# END FILE
