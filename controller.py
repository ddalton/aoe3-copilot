"""The co-pilot brain: a sensor -> decide -> act loop on a background thread.

Villager and house production are independently gated by threading.Events
that the UI toggles. No LLM in this loop -- it is a deterministic controller.
"""
import threading
import time

import config


class SharedState:
    """Thread-safe flags + latest GameState shared between loop and UI."""

    def __init__(self):
        self.villager_enabled = threading.Event()
        self.house_enabled = threading.Event()
        self.stop = threading.Event()
        self.villager_enabled.set()
        self.house_enabled.set()
        self._lock = threading.Lock()
        self._latest = config.GameState()
        self._action = "starting"
        self._level = "ok"  # "ok" | "warn" | "error" -> UI status colour

    def set_latest(self, gs, action=None, level="ok"):
        with self._lock:
            self._latest = gs
            if action:
                self._action = action
            self._level = level

    def get_latest(self):
        with self._lock:
            return self._latest, self._action, self._level


class Controller:
    def __init__(self, window, reader, inputc, shared, queue_reader):
        self.window = window
        self.reader = reader
        self.inputc = inputc
        self.shared = shared
        self.queue_reader = queue_reader
        self._last_queue_check = 0.0
        self._last_house_trigger = 0.0
        self._villager_strikes = 0
        self._villager_failed = False  # persistent until a confirmed success

    def run(self):
        while not self.shared.stop.is_set():
            t0 = time.time()
            try:
                self._tick()
            except Exception as e:  # keep the loop alive on transient errors
                self.shared.set_latest(config.GameState(), f"error: {e}")
            time.sleep(max(0.0, config.LOOP_INTERVAL - (time.time() - t0)))

    def _tick(self):
        self.window.update_rect()           # survive the window being moved
        gs = self.reader.read(self.window)
        if not gs.ok:
            self.shared.set_latest(gs, "no OCR (check ROIs)", "warn")
            return

        action = None
        if self.shared.villager_enabled.is_set():
            action = self._villager_logic(gs) or action
        if self.shared.house_enabled.is_set():
            h = self._house_logic(gs)
            if h:
                action = h

        # Persistent red only while villager production is on AND flagged failed.
        failed = self.shared.villager_enabled.is_set() and self._villager_failed
        self.shared.set_latest(gs, action or "watching", "error" if failed else "ok")

    def _villager_logic(self, gs):
        # Rate-limit the queue read (each read selects/cycles the TCs).
        now = time.time()
        if now - self._last_queue_check < config.QUEUE_CHECK_INTERVAL:
            return None
        self._last_queue_check = now

        if config.MAX_TOWN_CENTERS <= 1:
            # Single TC: select all (no camera move) and service it.
            return self._service_tc(gs, self.inputc.select_all_tcs)

        # Multiple TCs: cycle through each and service it. "Train only when
        # empty" makes wrap-around harmless when there are fewer TCs than the
        # max -- a TC we just queued reads as producing on its next visit and is
        # skipped, so we never over-queue. (cycle_tc moves the camera.)
        status = "all TCs busy"
        for _ in range(config.MAX_TOWN_CENTERS):
            r = self._service_tc(gs, self.inputc.cycle_tc)
            if r and r != "villager in production":
                status = r
        return status

    def _service_tc(self, gs, select_fn):
        """Select TC(s) via select_fn; if no villager is in production, train one
        and confirm the spend. Returns a status string."""
        select_fn()
        producing = self.queue_reader.is_producing(self.window)
        if producing is None:
            return "queue read failed -- run 'Cal. Villager Queue'"
        if producing:
            return "villager in production"
        # Queue empty -> train, but only with pop room + funds. If capped we keep
        # monitoring, so a death/house frees room and the next read trains.
        if gs.pop_cur >= gs.pop_max:
            return "pop full (waiting for room)"
        if getattr(gs, config.CONFIRM_RESOURCE) < config.VILLAGER_COST:
            return f"low {config.CONFIRM_RESOURCE}"

        before = self.reader.read_one(self.window, config.CONFIRM_RESOURCE)
        if before is None:
            before = getattr(gs, config.CONFIRM_RESOURCE)
        self.inputc.train_villager()       # TC(s) still selected from above
        time.sleep(config.CONFIRM_DELAY)
        after = self.reader.read_one(self.window, config.CONFIRM_RESOURCE)

        if after is not None and (before - after) >= config.CONFIRM_DROP_MIN:
            self._villager_strikes = 0
            self._villager_failed = False        # success clears the red status
            return "queued villager"

        # No drop with room + funds => the command did not register.
        self._villager_strikes += 1
        if self._villager_strikes >= config.VILLAGER_FAIL_STRIKES:
            self._villager_failed = True
            return "villager cmd NOT registering -- check focus/hotkeys"
        return "villager retry..."

    def _house_logic(self, gs):
        now = time.time()
        if now - self._last_house_trigger < config.HOUSE_COOLDOWN:
            return None
        if gs.pop_max == 0:
            return None
        headroom = gs.pop_max - gs.pop_cur
        if (headroom <= config.POP_HEADROOM_THRESHOLD
                and gs.pop_max < config.POP_HARD_CAP
                and gs.wood >= config.HOUSE_WOOD_COST):
            # Prefer an idle villager; fall back to the builder control group.
            if gs.idle > 0:
                self.inputc.select_idle_villager()
            else:
                self.inputc.select_builder_group()
            self.inputc.arm_house()  # armed; user clicks to place
            self._last_house_trigger = now
            return "armed house -- click to place!"
        return None
