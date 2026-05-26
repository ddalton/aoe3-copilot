"""Read HUD numbers from captured ROIs with PaddleOCR.

PaddleOCR is heavy on first init; we lazy-load and reuse the engine so the
model stays warm across ticks.
"""
import re

from config import GameState

_DIGITS = re.compile(r"\d+")


class HUDReader:
    def __init__(self, roi_map):
        self.roi_map = roi_map
        self._ocr = None

    def _engine(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
        return self._ocr

    def _text(self, img):
        result = self._engine().ocr(img, cls=False)
        if not result or not result[0]:
            return ""
        return " ".join(line[1][0] for line in result[0])

    def _int(self, img):
        nums = _DIGITS.findall(self._text(img).replace(",", ""))
        return int(nums[0]) if nums else None

    def read(self, window):
        """Capture + OCR every ROI; returns a GameState (ok=False on failure)."""
        gs = GameState()
        try:
            gs.food = self._int(window.capture(self.roi_map["food"])) or 0
            gs.wood = self._int(window.capture(self.roi_map["wood"])) or 0
            gs.coin = self._int(window.capture(self.roi_map["coin"])) or 0

            pop_nums = _DIGITS.findall(
                self._text(window.capture(self.roi_map["pop"])).replace(",", "")
            )
            if len(pop_nums) >= 2:
                gs.pop_cur, gs.pop_max = int(pop_nums[0]), int(pop_nums[1])

            gs.idle = self._int(window.capture(self.roi_map["idle"])) or 0
            gs.ok = True
        except Exception:
            gs.ok = False
        return gs

    def read_one(self, window, key):
        """Re-read a single ROI (e.g. 'coin') for the drop-confirmation check."""
        try:
            return self._int(window.capture(self.roi_map[key]))
        except Exception:
            return None
