from threading import Event, Thread
from typing import List, Dict, Any, Optional

import psutil

from triggerflowlib.utils import actions


class ProcessCondition:
    def __init__(
        self,
        process: str,
        label: Optional[str] = None,
        on_enter: Optional[List[Dict[str, Any]]] = None,
        on_exit: Optional[List[Dict[str, Any]]] = None,
    ):
        self.process = (process or "").lower()
        self.label = label or process or ""
        self.on_enter = on_enter or []
        self.on_exit = on_exit or []
        self.active: Optional[bool] = None

    def is_running(self) -> bool:
        if not self.process:
            return False
        for p in psutil.process_iter(attrs=["name"]):
            try:
                name = (p.info.get("name") or "").lower()
                if name == self.process:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False


class ConditionWatcher:
    """Polls for process conditions and fires actions on enter/exit.

    Expected trigger item shape:
      { "type": "process_running", "process": "vrserver.exe",
        "on_enter": [ {action...}, ... ],
        "on_exit":  [ {action...}, ... ] }
    """

    def __init__(self, triggers: List[Dict[str, Any]], poll_interval: float = 2.0):
        self._stop = Event()
        self._interval = max(0.5, float(poll_interval))
        self._conds: List[ProcessCondition] = []
        for t in triggers or []:
            if (
                isinstance(t, dict)
                and t.get("type") == "process_running"
                and t.get("process")
            ):
                self._conds.append(
                    ProcessCondition(
                        t.get("process"),
                        label=t.get("label") or t.get("name"),
                        on_enter=t.get("on_enter", []),
                        on_exit=t.get("on_exit", []),
                    )
                )
        self._thread = None

    def start(self):
        if not self._conds:
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = Thread(target=self._run, name="ConditionWatcher", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _run(self):
        while not self._stop.is_set():
            for cond in self._conds:
                try:
                    running = cond.is_running()
                    if cond.active is None:
                        cond.active = running
                    elif running and not cond.active:
                        # entered
                        for act in cond.on_enter:
                            try:
                                actions.run_action(act)
                            except Exception as e:
                                print(
                                    f"[ConditionWatcher] on_enter failed for {cond.process}: {e}"
                                )
                        cond.active = True
                    elif (not running) and cond.active:
                        # exited
                        for act in cond.on_exit:
                            try:
                                actions.run_action(act)
                            except Exception as e:
                                print(
                                    f"[ConditionWatcher] on_exit failed for {cond.process}: {e}"
                                )
                        cond.active = False
                except Exception as e:
                    print(f"[ConditionWatcher] error: {e}")
            # wait with stop support
            self._stop.wait(self._interval)

    def snapshot(self) -> List[Dict[str, Any]]:
        """Return a simple snapshot of current conditions for UI rendering.

        Each item contains: {"label": str, "process": str, "active": Optional[bool]}
        """
        out: List[Dict[str, Any]] = []
        for c in self._conds:
            out.append(
                {
                    "label": c.label,
                    "process": c.process,
                    "active": c.active,
                }
            )
        return out
