"""Scancode-level hotkey injection for the DirectX game (pydirectinput).

Every action re-focuses the game window first, because injected keys go to
whichever window is foreground. SendKeys/pyautogui are ignored by DirectX
games, which is why we use pydirectinput (SendInput + scancodes).
"""
import sys
import time

if sys.platform == "win32":
    import pydirectinput
    pydirectinput.PAUSE = 0.02  # default delay between pydirectinput calls


class InputController:
    def __init__(self, hotkeys, window=None, key_delay=0.03):
        self.hotkeys = hotkeys
        self.window = window
        self.key_delay = key_delay

    def _focus(self):
        if self.window:
            self.window.ensure_foreground()
            time.sleep(0.03)

    def _press_combo(self, keys):
        """Hold modifiers, tap the final key (e.g. ctrl+shift+h)."""
        self._focus()
        *mods, last = keys
        for m in mods:
            pydirectinput.keyDown(m)
        pydirectinput.press(last)
        for m in reversed(mods):
            pydirectinput.keyUp(m)
        time.sleep(self.key_delay)

    def _press_seq(self, keys):
        """Press keys one after another."""
        self._focus()
        for k in keys:
            pydirectinput.press(k)
            time.sleep(self.key_delay)

    # --- high-level actions ---
    def select_all_tcs(self):
        self._press_combo(self.hotkeys["select_all_tcs"])

    def cycle_tc(self):
        """Select the next Town Center (centers the camera on it)."""
        self._press_seq(self.hotkeys["cycle_tc"])

    def train_villager(self):
        self._press_seq(self.hotkeys["train_villager"])

    def select_idle_villager(self):
        self._press_seq(self.hotkeys["select_idle_villager"])

    def select_builder_group(self):
        self._press_seq(self.hotkeys["builder_control_group"])

    def arm_house(self):
        """Open build menu and select house; the USER places it with a click."""
        self._press_seq(self.hotkeys["build_menu"])
        self._press_seq(self.hotkeys["build_house"])

    def click(self, x, y):
        """Left-click at absolute screen coords (used to cancel a queued unit)."""
        self._focus()
        pydirectinput.click(x, y)
