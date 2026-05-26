"""System-wide hotkeys to pause/resume production without focusing the panel.

Uses the `keyboard` library, which installs a low-level OS hook so the combos
fire even while AoE3 is the foreground window. Callbacks run on keyboard's own
thread; toggling threading.Events is thread-safe.

Note: on Windows `keyboard` usually works without admin, but may need elevation
in some setups. The combos must not collide with in-game keybindings.
"""
import sys


def start_global_hotkeys(shared, mapping):
    """Register the toggle hotkeys. Returns a callable that unregisters them."""
    if sys.platform != "win32":
        return lambda: None

    import keyboard

    def _toggle(ev):
        ev.clear() if ev.is_set() else ev.set()

    keyboard.add_hotkey(mapping["toggle_villager"],
                        lambda: _toggle(shared.villager_enabled))
    keyboard.add_hotkey(mapping["toggle_house"],
                        lambda: _toggle(shared.house_enabled))
    return keyboard.unhook_all
