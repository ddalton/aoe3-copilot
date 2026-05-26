"""Central configuration for the AoE3 DE macro co-pilot.

CALIBRATE the ROI fractions and VERIFY the hotkeys on the target Windows
machine before relying on this. All ROIs are expressed as
(left_frac, top_frac, width_frac, height_frac) of the game CLIENT area, so
they survive resolution changes as long as the HUD layout is the same.
Run `python calibrate.py` to dump a screenshot with the boxes drawn.
"""
import os
from dataclasses import dataclass

# Substring match against the window title (robust to suffixes).
WINDOW_TITLE = "Age of Empires III"
# Soft confirmation only; verify the real name in Task Manager.
GAME_EXE_HINT = "AoE3DE_s.exe"

# --- HUD ROIs as FRACTIONS of the client area. THESE ARE PLACEHOLDERS. ---
# Calibrate against calibration.png. The resource bar sits along the top;
# the idle-villager badge is bottom-left in most layouts.
ROI = {
    "food": (0.300, 0.006, 0.045, 0.030),
    "wood": (0.355, 0.006, 0.045, 0.030),
    "coin": (0.410, 0.006, 0.045, 0.030),
    "pop":  (0.520, 0.006, 0.055, 0.030),   # reads "cur/max"
    "idle": (0.020, 0.930, 0.040, 0.040),   # idle villager count badge
    "queue": (0.420, 0.880, 0.160, 0.060),  # TC training-queue strip in the command
                                            # panel; calibrate to span the first 2-3 slots
}

# --- Hotkeys. VERIFY against your in-game keybindings (grid hotkeys vary). ---
HOTKEYS = {
    "select_all_tcs":        ("ctrl", "shift", "h"),  # default in AoE3 DE
    "cycle_tc":              ("h",),   # cycle to next TC (centers camera) -- VERIFY
    "train_villager":        ("q",),   # with TC selected (grid) -- VERIFY
    "select_idle_villager":  (".",),   # -- VERIFY / rebind
    "builder_control_group": ("9",),   # pre-assign ONE villager to group 9
    "build_menu":            ("a",),   # open build menu (grid) -- VERIFY
    "build_house":           ("q",),   # house within build menu -- VERIFY
}

# --- Control thresholds ---
QUEUE_CHECK_INTERVAL = 2.0      # seconds between queue reads (vs ~25s train time)
MAX_TOWN_CENTERS = 1            # TCs serviced per cycle. 1 = single TC (camera stays
                                # put). Raise toward your max (e.g. 3) once you build
                                # extra TCs in Fortress; >1 cycles TCs (moves camera)
                                # and stays over-queue-safe via "train only if empty".
POP_HEADROOM_THRESHOLD = 4      # arm a house when (pop_max - pop_cur) <= this
POP_HARD_CAP = 200              # never build houses past the hard pop cap
HOUSE_WOOD_COST = 100           # -- VERIFY current house wood cost
HOUSE_COOLDOWN = 30.0           # seconds; don't re-nudge a house within this
LOOP_INTERVAL = 1.0             # sensor/decision tick (seconds)

# --- Villager train confirmation (resource-drop check) ---
# Dutch settlers cost 100 COIN (other civs pay 100 food) -- so watch coin.
VILLAGER_COST = 100
CONFIRM_RESOURCE = "coin"       # GameState attribute to watch for the spend
CONFIRM_DELAY = 0.15            # seconds to let the HUD reflect the deduction
CONFIRM_DROP_MIN = 50           # min observed drop to count as success (vs trickle)
VILLAGER_FAIL_STRIKES = 2       # consecutive no-drops before flagging input failure

# --- Villager-queue reading (template match) ---
# "Cal. Villager Queue" writes this icon by queuing a villager, capturing the
# slot, and cancelling it. The reader template-matches it inside the queue ROI.
# Stored next to the code so it persists across games / working dirs. Recapture
# only if you change resolution or UI scale.
QUEUE_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "villager_icon.png")
QUEUE_MATCH_THRESHOLD = 0.70    # matchTemplate score above which a villager counts

# --- Global (system-wide) hotkeys to pause/resume without focusing the panel.
# Pick combos that do NOT collide with your in-game keybindings: these fire
# regardless of which window is focused, so a clash would toggle mid-game.
GLOBAL_HOTKEYS = {
    "toggle_villager": "ctrl+alt+v",
    "toggle_house": "ctrl+alt+b",
}


@dataclass
class GameState:
    food: int = 0
    wood: int = 0
    coin: int = 0
    pop_cur: int = 0
    pop_max: int = 0
    idle: int = 0
    ok: bool = False  # whether OCR succeeded this tick
