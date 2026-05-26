# AoE3 DE Macro Co-pilot

A lightweight macro autopilot for **Age of Empires III: Definitive Edition**
(tuned for the **Dutch**). It runs as a separate background program: it reads
your own HUD by screen capture + OCR and acts through hotkeys, keeping villager
production and housing going so you can focus on tactics. There is **no LLM in
the live loop** — it's a deterministic, closed control loop.

## What it does

- **Villagers:** reads the Town Center queue (icon template match) and trains a
  villager only when none is in production — so the queue never over-stacks.
  Confirms each train via a coin-drop check (Dutch settlers cost coin).
- **Houses (anti-pop-block):** when population headroom runs low, it grabs an
  idle villager (or a builder control group) and *arms* a house — **you click to
  place it**. 30 s cooldown so a cancel won't nag you.
- **Pause/resume:** independent toggles for villagers and houses, via the panel
  or global hotkeys (work even while the game is focused).

## Requirements

- **Windows** — must run on the same PC as the game. It uses `win32gui`,
  `pydirectinput`, and `mss`, which do **not** work on WSL/macOS/Linux.
- Native **Python 3.9+** from python.org (not the Microsoft Store / WSL build).
- Run AoE3 DE in **windowed / borderless** (not exclusive fullscreen) at a
  **locked resolution**.

## Quick start (after cloning on the Windows game PC)

Run these in **PowerShell or Command Prompt** (not WSL). For the global
pause/resume hotkeys to work, you may need to run the terminal **as
Administrator** (the `keyboard` library installs a system-wide hook).

```bat
git clone https://github.com/ddalton/aoe3-copilot.git
cd aoe3-copilot

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

> First run downloads the PaddleOCR models, so you need an internet connection
> the first time (and it may take a minute).

Then launch **AoE3 DE in windowed/borderless at a locked resolution**, start a
game, and run:

```bat
python main.py
```

A small always-on-top panel appears. Do the one-time calibration below.

## One-time calibration (per resolution/UI scale)

With a game running:

1. **Calibrate ROIs** — click the button, open `calibration.png`, and adjust the
   fractions in `config.ROI` until each red box frames its HUD number (resources,
   pop `cur/max`, idle count, and the TC `queue` strip — span the first 2–3 slots).
   Re-run after each edit until the boxes line up. Restart `main.py` to reload.
2. **Cal. Villager Queue** — on a clean/idle Town Center, click this once. It
   queues a villager, captures the icon as `villager_icon.png`, and cancels it
   (refunded). The template persists across games (it's saved next to the code);
   recapture only if you change resolution or UI scale.
3. **Verify hotkeys** in `config.HOTKEYS` against your in-game keybindings
   (`select_all_tcs`, `cycle_tc`, `train_villager`, `build_menu`/`build_house`,
   idle-villager). Pre-assign one villager to **control group 9** for the
   no-idle house fallback.

After this, future games just need: activate the venv and `python main.py`.

## Hotkeys (global, configurable)

| Action | Default |
|---|---|
| Toggle villager production | `Ctrl+Alt+V` |
| Toggle house production | `Ctrl+Alt+B` |

Pick combos that don't collide with your in-game binds (see `config.GLOBAL_HOTKEYS`).

## Config knobs (`config.py`)

- `MAX_TOWN_CENTERS` — `1` = single TC (camera stays put); raise it (e.g. `3`)
  in Fortress to cycle multiple TCs (over-queue-safe; moves the camera).
- `QUEUE_CHECK_INTERVAL`, `POP_HEADROOM_THRESHOLD`, `HOUSE_WOOD_COST`,
  `VILLAGER_COST` / `CONFIRM_RESOURCE`, `QUEUE_MATCH_THRESHOLD`.

## Scope / notes

- You own all tactics and **building placement**; the co-pilot only arms houses.
- It reads only **your** HUD — no enemy/battlefield vision. Declare strategy by
  pausing/resuming (e.g. hold pop for military).
- Key injection needs the game window focused; the panel re-focuses it before
  acting, and the global hotkeys avoid stealing focus.
