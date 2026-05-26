"""Detect whether a villager is in the Town Center's production queue by
template-matching a villager-icon image inside the command-panel 'queue' ROI.

The template (villager_icon.png) is produced by the "Cal. Villager Queue"
routine in calibrate.py, which queues a villager, captures the slot, and
cancels it. Reading the real queue (instead of timing presses) makes villager
production bullet-proof: we add one only when none is in production, so the
queue never over-stacks, and it is immune to train-time changes and age-ups.
"""
import os


class QueueReader:
    def __init__(self, queue_roi, template_path, threshold):
        self.queue_roi = queue_roi
        self.template_path = template_path
        self.threshold = threshold
        self._template = None
        self._tried_load = False

    def _template_img(self):
        if not self._tried_load:
            self._tried_load = True
            import cv2
            if os.path.exists(self.template_path):
                self._template = cv2.imread(self.template_path, cv2.IMREAD_COLOR)
        return self._template

    def is_producing(self, window):
        """True if a villager icon is found in the queue strip, False if not,
        None if the template is missing or the match cannot be run."""
        import cv2
        tmpl = self._template_img()
        if tmpl is None:
            return None
        try:
            img = window.capture(self.queue_roi)
        except Exception:
            return None
        if img.shape[0] < tmpl.shape[0] or img.shape[1] < tmpl.shape[1]:
            return None
        res = cv2.matchTemplate(img, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return bool(max_val >= self.threshold)

    def reload(self):
        """Drop the cached template so a fresh one is loaded after recalibration."""
        self._template = None
        self._tried_load = False
