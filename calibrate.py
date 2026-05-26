"""Dump a screenshot of the game client with the configured ROI boxes drawn,
so you can tune config.ROI. Writes calibration.png next to this file.

Run on the Windows game machine with AoE3 in windowed/borderless mode:
    python calibrate.py
"""
import sys

import config
from game_window import GameWindow


def dump_calibration(path="calibration.png"):
    """Capture the client area, draw the configured ROI boxes, save to `path`.

    Builds its OWN GameWindow (fresh mss context) so it is safe to call from a
    different thread than the controller loop. Returns the output path.
    """
    import cv2

    win = GameWindow(config.WINDOW_TITLE, config.GAME_EXE_HINT)
    win.find()
    img = win.capture_full().copy()
    w, h = win.size
    for name, (lf, tf, wf, hf) in config.ROI.items():
        x, y = int(lf * w), int(tf * h)
        cv2.rectangle(img, (x, y), (x + int(wf * w), y + int(hf * h)), (0, 0, 255), 2)
        cv2.putText(img, name, (x, max(10, y - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.imwrite(path, img)
    return path


def calibrate_villager_queue(window, inputc):
    """Auto-capture the villager-queue template: queue a villager, grab the
    first queue slot as the icon, then cancel the villager (refunds resources).

    Run in a live game on a clean/idle TC, AFTER the 'queue' ROI is calibrated
    (this clicks inside that ROI to cancel). Returns the template path.
    """
    import time

    import cv2
    import mss
    import numpy as np

    box = window.roi_box(config.ROI["queue"])
    inputc.select_all_tcs()
    time.sleep(0.15)
    inputc.train_villager()
    time.sleep(0.45)  # let the queue icon render

    with mss.mss() as sct:  # own capture context (thread-safe vs the control loop)
        img = np.array(sct.grab(box))[:, :, :3]

    # The leftmost square is the first queue slot -> save it as the icon template.
    side = min(img.shape[0], img.shape[1])
    cv2.imwrite(config.QUEUE_TEMPLATE_PATH, img[0:side, 0:side])

    # Cancel the queued villager by clicking the first slot (refunds the spend).
    inputc.click(box["left"] + side // 2, box["top"] + side // 2)
    return config.QUEUE_TEMPLATE_PATH


def main():
    if sys.platform != "win32":
        print("Run this on the Windows game machine.")
        return
    path = dump_calibration()
    print(f"Wrote {path} -- check each box frames its HUD number, "
          "then adjust the fractions in config.ROI.")


if __name__ == "__main__":
    main()
