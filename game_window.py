"""Locate the AoE3 DE window and capture fixed HUD regions from it.

Windows-only (win32gui / mss). Sets per-monitor DPI awareness on import so
GetWindowRect/ClientToScreen return true pixels that match the screenshot.
"""
import ctypes
import sys

import numpy as np

if sys.platform == "win32":
    import mss
    import psutil
    import win32gui
    import win32process

    # Make coordinates DPI-correct BEFORE any rect queries.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor v2
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class GameWindowError(RuntimeError):
    pass


class GameWindow:
    def __init__(self, title_substring, exe_hint=None):
        self.title_substring = title_substring.lower()
        self.exe_hint = exe_hint
        self.hwnd = None
        self.origin = (0, 0)  # client-area top-left in screen coords
        self.size = (0, 0)    # (width, height) of client area
        self._sct = mss.mss() if sys.platform == "win32" else None

    def find(self):
        matches = []

        def _cb(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            if self.title_substring in win32gui.GetWindowText(hwnd).lower():
                matches.append(hwnd)

        win32gui.EnumWindows(_cb, None)
        if not matches:
            raise GameWindowError(
                f"No visible window matching '{self.title_substring}'. "
                "Is the game running in windowed/borderless mode?"
            )
        # Prefer a window whose process matches the exe hint, else first match.
        self.hwnd = next((h for h in matches if self._confirm_exe(h)), matches[0])
        self.update_rect()
        return self.hwnd

    def _confirm_exe(self, hwnd):
        if not self.exe_hint:
            return True
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return psutil.Process(pid).name().lower() == self.exe_hint.lower()
        except Exception:
            return False

    def update_rect(self):
        if not self.hwnd:
            raise GameWindowError("window not found yet; call find() first")
        l, t, r, b = win32gui.GetClientRect(self.hwnd)
        x, y = win32gui.ClientToScreen(self.hwnd, (l, t))
        self.origin = (x, y)
        self.size = (r - l, b - t)
        if self.size[0] <= 0 or self.size[1] <= 0:
            raise GameWindowError("client area has zero size (minimized?)")

    def roi_box(self, frac):
        lf, tf, wf, hf = frac
        ox, oy = self.origin
        w, h = self.size
        return {
            "left": ox + int(lf * w),
            "top": oy + int(tf * h),
            "width": max(1, int(wf * w)),
            "height": max(1, int(hf * h)),
        }

    def capture(self, frac):
        """Capture one ROI; returns a BGR numpy array."""
        raw = self._sct.grab(self.roi_box(frac))
        return np.array(raw)[:, :, :3]

    def capture_full(self):
        """Capture the whole client area (for calibration); BGR numpy array."""
        ox, oy = self.origin
        w, h = self.size
        raw = self._sct.grab({"left": ox, "top": oy, "width": w, "height": h})
        return np.array(raw)[:, :, :3]

    def is_foreground(self):
        return win32gui.GetForegroundWindow() == self.hwnd

    def ensure_foreground(self):
        if not self.is_foreground():
            try:
                win32gui.SetForegroundWindow(self.hwnd)
            except Exception:
                pass  # Windows may refuse; injection may then no-op
