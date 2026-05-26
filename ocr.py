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
            # PaddleOCR 3.x API: no show_log/use_angle_cls. The doc-orientation
            # and unwarping stages are useless on tiny HUD crops, so disable them.
            # enable_mkldnn=False avoids a oneDNN PIR-attribute crash in
            # paddlepaddle 3.x CPU inference on some machines.
            self._ocr = PaddleOCR(
                lang="en",
                use_textline_orientation=False,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                enable_mkldnn=False,
            )
        return self._ocr

    def _text(self, img):
        # PaddleOCR 3.x: predict() returns OCRResult objects exposing rec_texts.
        result = self._engine().predict(img)
        if not result:
            return ""
        res = result[0]
        texts = res.get("rec_texts") if hasattr(res, "get") else None
        return " ".join(texts) if texts else ""

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
