"""Minimal always-on-top control panel (Tkinter, stdlib).

Two SEPARATE toggle buttons: one for villager production, one for house
production. Live status shows the OCR'd resources / pop / idle and the
controller's last action.

Note: keep this window OFF the HUD regions so it does not occlude what mss
captures, and be aware clicking it steals focus from the game (the controller
re-focuses the game before injecting keys).
"""
import os
import sys
import time
import tkinter as tk

_ON_BG = "#bfe6bf"
_OFF_BG = "#e6bfbf"


class CopilotUI:
    def __init__(self, shared, hotkeys=None, queue_calibrate_fn=None):
        self.shared = shared
        self.hotkeys = hotkeys or {}
        self.queue_calibrate_fn = queue_calibrate_fn
        self.root = tk.Tk()
        self.root.title("AoE3 Co-pilot")
        self.root.attributes("-topmost", True)
        self.root.geometry("280x340")

        self.res = tk.StringVar(value="F -  W -  C -")
        self.pop = tk.StringVar(value="pop -/-   idle -")
        self.action = tk.StringVar(value="starting...")

        tk.Label(self.root, textvariable=self.res, font=("Consolas", 12)).pack(pady=3)
        tk.Label(self.root, textvariable=self.pop, font=("Consolas", 12)).pack(pady=3)
        self.action_label = tk.Label(self.root, textvariable=self.action, fg="blue")
        self.action_label.pack(pady=3)

        self.vil_btn = tk.Button(self.root, width=26, command=self._toggle_villager)
        self.vil_btn.pack(pady=4)
        self.house_btn = tk.Button(self.root, width=26, command=self._toggle_house)
        self.house_btn.pack(pady=4)
        tk.Button(self.root, width=26, text="Calibrate ROIs",
                  command=self._calibrate).pack(pady=4)
        if self.queue_calibrate_fn:
            tk.Button(self.root, width=26, text="Cal. Villager Queue",
                      command=self._calibrate_queue).pack(pady=4)

        if self.hotkeys:
            hint = ("Global toggles -- "
                    f"villagers: {self.hotkeys.get('toggle_villager', '?')}, "
                    f"houses: {self.hotkeys.get('toggle_house', '?')}")
            tk.Label(self.root, text=hint, font=("Consolas", 8), fg="gray",
                     wraplength=270, justify="left").pack(pady=2)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._refresh_buttons()
        self._poll()

    def _toggle_villager(self):
        ev = self.shared.villager_enabled
        ev.clear() if ev.is_set() else ev.set()
        self._refresh_buttons()

    def _toggle_house(self):
        ev = self.shared.house_enabled
        ev.clear() if ev.is_set() else ev.set()
        self._refresh_buttons()

    def _refresh_buttons(self):
        v = self.shared.villager_enabled.is_set()
        h = self.shared.house_enabled.is_set()
        self.vil_btn.config(text=f"Villagers: {'RUNNING' if v else 'PAUSED'}",
                            bg=_ON_BG if v else _OFF_BG)
        self.house_btn.config(text=f"Houses: {'RUNNING' if h else 'PAUSED'}",
                              bg=_ON_BG if h else _OFF_BG)

    def _calibrate(self):
        """Hide the panel, dump a screenshot with ROI boxes, then reopen it."""
        from calibrate import dump_calibration
        self.action.set("calibrating...")
        self.root.withdraw()          # keep the panel out of the screenshot
        self.root.update()
        time.sleep(0.15)              # let the OS actually remove it
        try:
            path = dump_calibration()
            self.action.set(f"saved {path}")
            if sys.platform == "win32":
                os.startfile(os.path.abspath(path))  # noqa: open the image
        except Exception as e:
            self.action.set(f"calibrate error: {e}")
        finally:
            self.root.deiconify()

    def _calibrate_queue(self):
        """Pause villagers, hide the panel, run the queue calibration, restore."""
        if not self.queue_calibrate_fn:
            return
        was_on = self.shared.villager_enabled.is_set()
        self.shared.villager_enabled.clear()   # don't fight over input
        self.action.set("calibrating villager queue...")
        self.root.withdraw()
        self.root.update()
        time.sleep(0.15)
        try:
            path = self.queue_calibrate_fn()
            self.action.set(f"saved {path}")
        except Exception as e:
            self.action.set(f"queue cal error: {e}")
        finally:
            self.root.deiconify()
            if was_on:
                self.shared.villager_enabled.set()
            self._refresh_buttons()

    def _poll(self):
        gs, action, level = self.shared.get_latest()
        self.res.set(f"F {gs.food}   W {gs.wood}   C {gs.coin}")
        self.pop.set(f"pop {gs.pop_cur}/{gs.pop_max}   idle {gs.idle}")
        self.action.set(action)
        colour = {"error": "red", "warn": "#aa6600", "ok": "blue"}.get(level, "blue")
        self.action_label.config(fg=colour)
        self._refresh_buttons()  # reflect toggles made via global hotkeys
        self.root.after(400, self._poll)

    def _on_close(self):
        self.shared.stop.set()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
