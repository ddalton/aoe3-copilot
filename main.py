"""Entry point: wire the sensor/controller thread to the Tkinter UI.

Run on the Windows machine running AoE3 DE, in windowed/borderless mode:
    python main.py
"""
import sys
import threading

import config
from calibrate import calibrate_villager_queue
from controller import Controller, SharedState
from game_window import GameWindow
from hotkey_listener import start_global_hotkeys
from input_controller import InputController
from ocr import HUDReader
from queue_reader import QueueReader
from ui import CopilotUI


def main():
    if sys.platform != "win32":
        print("This co-pilot must run on the Windows machine running AoE3 DE.")
        print("It needs win32gui / pydirectinput / mss + a visible game window.")
        return

    window = GameWindow(config.WINDOW_TITLE, config.GAME_EXE_HINT)
    window.find()
    print(f"Found game window hwnd={window.hwnd} client size={window.size}")

    reader = HUDReader(config.ROI)
    inputc = InputController(config.HOTKEYS, window=window)
    queue_reader = QueueReader(config.ROI["queue"], config.QUEUE_TEMPLATE_PATH,
                               config.QUEUE_MATCH_THRESHOLD)
    shared = SharedState()
    controller = Controller(window, reader, inputc, shared, queue_reader)

    threading.Thread(target=controller.run, daemon=True).start()
    unhook = start_global_hotkeys(shared, config.GLOBAL_HOTKEYS)

    def cal_queue():
        path = calibrate_villager_queue(window, inputc)
        queue_reader.reload()  # pick up the freshly captured template
        return path

    try:
        CopilotUI(shared, config.GLOBAL_HOTKEYS, queue_calibrate_fn=cal_queue).run()
    finally:
        shared.stop.set()  # stop the loop when the UI closes
        unhook()           # remove the global hotkeys


if __name__ == "__main__":
    main()
