import tkinter as tk
import json
from triggerflowlib.utils.buttoncfgloader import ButtonConfigLoader
from triggerflowlib.utils import actions
from triggerflowlib.utils.process_watch import ConditionWatcher


def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    # Only allow imports from the local package to limit eval surface
    if name.startswith("triggerflowlib"):
        return __import__(name, globals or {}, locals or {}, fromlist, level)
    raise ImportError(f"Import not allowed: {name}")


def _safe_eval_lambda(lambda_str: str):
    """Evaluate a lambda string using a restricted import hook.

    This keeps legacy behavior for `command` strings but reduces risk by
    restricting imports. It's still not fully sandboxed; prefer `action` format.
    """
    safe_globals = {"__builtins__": {}}
    safe_globals["__import__"] = _safe_import
    return eval(lambda_str, safe_globals, {})


def CreateButtonLayout():
    root = tk.Tk()
    root.geometry("200x300")
    with open("versiondata.json", "r") as f:
        version_info = json.load(f)
        root.title(f"TriggerFlow (v{version_info['version']})")

    button_config = ButtonConfigLoader("config/buttons.yaml")

    # Start condition watcher for any keys starting with 't' (e.g., t1, t2, ...)
    if isinstance(button_config, dict):
        trigger_items = [
            v
            for k, v in button_config.items()
            if isinstance(k, str) and k.lower().startswith("t") and isinstance(v, dict)
        ]
        if trigger_items:
            watcher = ConditionWatcher(trigger_items)
            watcher.start()
            root._condition_watcher = watcher  # keep a reference to avoid GC

            # Render trigger labels that update when status changes
            triggers_frame = tk.Frame(root)
            triggers_frame.pack(pady=5)
            tk.Label(triggers_frame, text="Triggers:", anchor="w").pack(fill="x")
            labels = []

            # Initial placeholders based on provided config
            for t in trigger_items:
                label_text = (
                    t.get("label") or t.get("name") or t.get("process") or "Trigger"
                )
                lbl = tk.Label(
                    triggers_frame, text=f"{label_text}: Checking...", fg="gray"
                )
                lbl.pack(anchor="w")
                labels.append(lbl)

            root._trigger_labels = labels

            def _refresh_trigger_labels():
                try:
                    snapshot = root._condition_watcher.snapshot()
                    for i, item in enumerate(snapshot):
                        if i >= len(root._trigger_labels):
                            break
                        state = item.get("active")
                        name = item.get("label") or item.get("process") or f"T{i+1}"
                        if state is None:
                            txt, color = f"{name}: Checking...", "gray"
                        elif state:
                            txt, color = f"{name}: Running", "green"
                        else:
                            txt, color = f"{name}: Stopped", "red"
                        root._trigger_labels[i].config(text=txt, fg=color)
                finally:
                    # Schedule next refresh
                    root.after(1000, _refresh_trigger_labels)

            # Kick off periodic UI updates
            root.after(500, _refresh_trigger_labels)

    for button_key, button_data in button_config.items():
        # Only render keys that look like buttons (start with 'b')
        if not (isinstance(button_key, str) and button_key.lower().startswith("b")):
            continue
        if not button_data:
            continue

        # Prefer declarative `action` blocks
        if "action" in button_data:

            def make_action_runner(act):
                return lambda a=act: actions.run_action(a)

            button_command = make_action_runner(button_data["action"])
        else:
            # Legacy fallback: evaluate the command string to get a callable.
            command_str = button_data.get("command")
            if command_str:
                try:
                    button_command = _safe_eval_lambda(command_str)
                except Exception:
                    # If safe eval fails, fall back to a harmless noop that logs
                    button_command = lambda: print(
                        f"Failed to evaluate command for {button_key}"
                    )
            else:
                button_command = lambda: print("No command")

        button = tk.Button(
            root, text=button_data.get("text", "Default Text"), command=button_command
        )
        button.pack(pady=10)

    return root
