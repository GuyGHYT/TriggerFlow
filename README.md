# TriggerFlow

TriggerFlow maps buttons to actions (Spotify playback, keyboard macros, etc.) via a small plugin system.

## Files of note
- `main.py` — project entrypoint (if present)
- `test.py` — quick script to exercise the library
- `requirements.txt` — Python dependencies required to run the project
- `config/buttons.yaml` — YAML configuration for button mappings
- `triggerflowlib/` — library source: plugins, UI, utils

## Quick start (Windows PowerShell)

1. Verify Python is a real interpreter (avoid the Microsoft Store stub):
```powershell
python --version
python -c "import sys; print(sys.executable)"
```

2. Create & activate a virtual environment:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Upgrade pip and install dependencies:
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. (Optional) Set Spotify credentials for the Spotify plugin:
```powershell
$env:SPOTIPY_CLIENT_ID="46d3dd30d76540799c23419c05ad492a"
$env:SPOTIPY_CLIENT_SECRET="a4bfdba9f34f4f36a8a5e6cc3366be29"
$env:SPOTIPY_REDIRECT_URI="http://localhost:8888/callback"
```

5. Run the app or quick test:
```powershell
python .\main.py
# or
python .\test.py
```

## Configuration
- Edit `config/buttons.yaml` to add or change buttons and actions. The loader is `triggerflowlib/utils/buttoncfgloader.py`.

Example YAML (project format — declarative preferred):
```yaml
b3:
  text: "Play Top Hits"
  action:
    type: spotify_play_playlist
    playlist_uri: "spotify:playlist:xxxxxxxxxxxxxxxx"
```

### Trigger formatting (t#)

You can define triggers with keys starting with `t` (e.g., `t1`, `t2`). Triggers are displayed as updatable labels in the UI and refresh automatically when their status changes.

Supported trigger type: `process_running` — watches for a Windows process by name.

Example:

```yaml
t1:
  type: process_running
  process: "vrserver.exe"   # exact process name to watch
  label: "SteamVR"          # optional; shown in the UI (falls back to process)
  on_enter:                  # actions fired when the process starts
    - type: voicemeeter_toggle_a_pair
      strips: [0, 5]
  on_exit:                   # actions fired when the process stops
    - type: voicemeeter_toggle_a_pair
      strips: [0, 5]
```

UI behavior:
- Each `t#` renders as a label like `SteamVR: Running` / `Stopped` / `Checking...`.
- Labels auto-update roughly once per second.
- Pair this with your button actions (`b#`) as needed.

Legacy format (code strings) is supported but discouraged. To migrate simple patterns (Spotify playlist, mute/deafen) automatically, run the migration helper:

```powershell
python tools/migrate_commands.py
```

After running the script, review `config/buttons.yaml` and remove any leftover `command` entries that couldn't be converted.

## Troubleshooting
- MS Store Python (App Execution Alias): if `python` points to `WindowsApps` or prompts to install, install Python from https://python.org and ensure PATH points to the real `python.exe`, or disable the App Execution Alias in Windows Settings.
- PyAutoGUI/Pillow: `PyAutoGUI` depends on `Pillow`. If pip fails to build wheels, upgrade pip and install the Visual C++ Build Tools or use prebuilt wheels.
- PyAutoGUI permissions: on Windows you may need appropriate permissions to control input; try running PowerShell as Administrator or check privacy settings.
- Spotify OAuth: ensure the redirect URI in the Spotify Developer Dashboard matches `$env:SPOTIPY_REDIRECT_URI`.

## Pinning versions
For reproducible installs, pin versions in `requirements.txt`. Example:
```
spotipy==2.26.0
PyYAML==6.0
PyAutoGUI==0.9.53
Pillow==10.0.0
```

## Developer conveniences (optional)
- Add a helper script `scripts/make_venv.ps1` to create & optionally install deps.
- Add `requirements-dev.txt` with `pytest` for tests:
```
pytest
```

## Packaging (optional)
To build a Windows executable (so users don't need Python):
```powershell
python -m pip install pyinstaller
python -m PyInstaller --onefile main.py
```

## Security & secrets
- Do not commit Spotify client secrets or other credentials. Use environment variables or a secrets manager.
- Add `.env` to `.gitignore` if you use local env files.

## Contributing
- Add plugins in `triggerflowlib/plugins`. Follow the pattern used in `spotify.py`.

## License
This project is licensed under the MIT License — see the `LICENSE` file for details.

SPDX-License-Identifier: MIT

Copyright (c) 2025 GuyGHYT
