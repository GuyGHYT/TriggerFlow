"""Voicemod integration via WebSocket API.

Voicemod Pro required for API access.
Enable the API in Voicemod settings and note the port (default 59129).
"""

import json
import socket
import os


_VOICEMOD_PORT = int(os.environ.get("VOICEMOD_PORT", "59129"))
_VOICEMOD_HOST = os.environ.get("VOICEMOD_HOST", "localhost")


def _send_command(action: str, payload: dict = None):
    """Send a command to Voicemod via WebSocket-like TCP connection.
    
    Returns the response dict or raises on error.
    """
    message = {
        "action": action,
        "id": "triggerflow-request"
    }
    if payload:
        message["payload"] = payload
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect((_VOICEMOD_HOST, _VOICEMOD_PORT))
        
        # Send JSON message
        msg_str = json.dumps(message) + "\n"
        sock.sendall(msg_str.encode("utf-8"))
        
        # Read response
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if b"\n" in response:
                break
        
        sock.close()
        
        if response:
            return json.loads(response.decode("utf-8"))
        return None
        
    except Exception as e:
        raise RuntimeError(f"Voicemod API error: {e}")


def get_voices():
    """Get list of available voices."""
    resp = _send_command("getVoices")
    return resp.get("voices", []) if resp else []


def select_voice(voice_id: str):
    """Select a voice by ID.
    
    Args:
        voice_id: Voice identifier (e.g., "nofx", "baby", "robot", etc.)
    """
    resp = _send_command("loadVoice", {"voiceID": voice_id})
    return resp.get("actionType") == "loadVoice" if resp else False


def toggle_voice_changer():
    """Toggle voice changer on/off."""
    resp = _send_command("toggleVoiceChanger")
    return resp is not None


def mute():
    """Mute microphone."""
    resp = _send_command("toggleMuteMic", {"mute": True})
    return resp is not None


def unmute():
    """Unmute microphone."""
    resp = _send_command("toggleMuteMic", {"mute": False})
    return resp is not None


def toggle_mute():
    """Toggle microphone mute."""
    resp = _send_command("toggleMuteMic")
    return resp is not None


def toggle_hear_myself():
    """Toggle 'Hear Myself' feature."""
    resp = _send_command("toggleHearMyVoice")
    return resp is not None


def get_current_voice():
    """Get currently selected voice."""
    resp = _send_command("getCurrentVoice")
    return resp.get("voice") if resp else None


def set_background_effects(enabled: bool):
    """Enable or disable background effects."""
    resp = _send_command("toggleBackground", {"enabled": enabled})
    return resp is not None


def play_sound(sound_file: str, loop: bool = False):
    """Play a sound/meme.
    
    Args:
        sound_file: Path or name of sound to play
        loop: Whether to loop the sound
    """
    resp = _send_command("playMeme", {"fileName": sound_file, "loop": loop})
    return resp is not None


def stop_all_sounds():
    """Stop all currently playing sounds."""
    resp = _send_command("stopAllMemeSounds")
    return resp is not None


# Note: Audio device switching typically requires OS-level changes.
# Voicemod selects devices in its settings, but switching programmatically
# may require Windows Audio API (WASAPI) or third-party tools like AudioSwitcher.
# For now, you can control voice effects and mute, which covers most use cases.
