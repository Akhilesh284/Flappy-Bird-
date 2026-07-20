# Flappy Bird — Enhanced Edition

Your original game, with the requested features layered on top. All original
mechanics (gravity, flap, pipes, scoring, collision) are untouched.

## New files
- `constants.py` — colors/palettes, medal thresholds, achievement & skin definitions
- `persistence.py` — reads/writes `save_data.json` (volume, night mode, skins, achievements)
- `achievements.py` — `AchievementManager`: unlock logic for achievements & bird skins
- `slider.py` — reusable `Slider` widget (used for the volume control)
- `birdup_<skin>.png` / `birddown_<skin>.png` — pre-generated skin art (red/blue/green/gold),
  hue-shifted from your original sprite so shading/highlights are preserved
- `README.md` — this file

`highscore.txt` still works exactly as before. A new `save_data.json` will be created
next to it the first time you run the game — that's where volume, night mode, unlocked
skins/achievements, and your best medal live.

## What's new

**Animated loading screen** — a short bouncing-bird + progress-bar intro before the menu.

**Achievement system** (`achievements.py`) — 9 achievements (first flight, score
milestones, beating your high score, playing at night, earning a Platinum medal,
unlocking every skin). Unlocking one pops up a toast banner in the corner.
View them all from the menu's **ACHIEVEMENTS** screen.

**Medals** — Bronze (10), Silver (20), Gold (30), Platinum (50), based on your score
each round. Shown on the Game Over screen and next to the title on the main menu
(your best-ever medal).

**Volume slider** — replaces the old on/off mute button in a new **SETTINGS** screen.
Drag it, or click it, or use ←/→ when it's focused via Tab. A small mute/unmute
shortcut icon still sits in the bottom-right corner in every screen.

**Day/Night mode** — toggle in Settings. Tints the whole scene with a translucent
navy overlay and switches text/UI colors to a legible light palette at night.
Persists between sessions.

**Multiple bird skins** — Classic Red (default), Sky Blue, Forest Green, and Golden.
Blue/Green unlock via achievements, Gold unlocks by earning a Platinum medal.
Browse and equip them from the menu's **BIRD SKINS** screen (arrows to preview,
EQUIP to select).

**Better UI/menus** — expanded main menu (Start / Bird Skins / Achievements /
Settings / Exit), dimmed backdrop panels behind all submenus so text stays
legible over the game scene, keyboard navigation (Tab/arrows/Enter) throughout,
and mouse support everywhere.

## Controls
- **Space / Click** — flap
- **Menus** — mouse click, or Tab/Arrow keys + Enter
- **Escape** — back out of Settings / Skins / Achievements to the menu
- **Left/Right** — cycle bird skins (on the Skins screen) or adjust the volume
  slider (on Settings, once it's focused)

## Sounds
Sound files weren't included, so `sounds/flap.wav` and `sounds/crash.mp3` are
optional — the game already loads them defensively and runs silently if
they're missing. Drop your own files at those paths (relative to `flappy.py`)
to bring sound back; the volume slider and mute icon will control them
automatically.

## Run it
```
pip install pygame
python flappy.py
```
