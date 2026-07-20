"""
Shared constants: colors, medal thresholds, and achievement definitions.
Keeping these in one place makes it easy to tune game feel / balance later.
"""

# ------------------------------------------------------------------ #
# COLOR PALETTES (day / night)
# ------------------------------------------------------------------ #
DAY_PALETTE = {
    "text":        (20, 20, 25),
    "text_light":  (255, 255, 255),
    "overlay":     (0, 0, 0, 0),          # no overlay tint during the day
    "panel":       (255, 255, 255, 235),
    "panel_border": (30, 30, 30),
    "accent":      (255, 195, 40),
}

NIGHT_PALETTE = {
    "text":        (235, 235, 245),
    "text_light":  (255, 255, 255),
    "overlay":     (10, 15, 45, 115),      # translucent navy tint drawn over the scene
    "panel":       (25, 25, 40, 235),
    "panel_border": (10, 10, 20),
    "accent":      (120, 170, 255),
}

# ------------------------------------------------------------------ #
# MEDALS -- awarded per-round based on the score reached
# ------------------------------------------------------------------ #
MEDAL_THRESHOLDS = [
    ("platinum", 50, (210, 230, 255)),
    ("gold",     30, (255, 205, 60)),
    ("silver",   20, (200, 200, 210)),
    ("bronze",   10, (205, 135, 80)),
]

def medal_for_score(score):
    """Return only the medal name."""
    for name, threshold, color in MEDAL_THRESHOLDS:
        if score >= threshold:
            return name
    return None


# ------------------------------------------------------------------ #
# BIRD SKINS
# ------------------------------------------------------------------ #
# key -> (display name, unlock description, min medal required to unlock, sort order)
BIRD_SKINS = {
    "red":   {"label": "Classic Red",  "unlock": None},
    "blue":  {"label": "Sky Blue",     "unlock": "achievement:score_10"},
    "green": {"label": "Forest Green", "unlock": "achievement:score_25"},
    "gold":  {"label": "Golden",       "unlock": "medal:platinum"},
}
SKIN_ORDER = ["red", "blue", "green", "gold"]

# ------------------------------------------------------------------ #
# ACHIEVEMENTS
# ------------------------------------------------------------------ #
# Each achievement: id -> {label, description}
# Unlock logic lives in achievements.py so it can react to game events.
ACHIEVEMENTS = {
    "first_flight": {
        "label": "First Flight",
        "desc": "Play your first round.",
    },
    "score_1": {
        "label": "Getting Started",
        "desc": "Score your first point.",
    },
    "score_10": {
        "label": "Perseverance",
        "desc": "Reach a score of 10 in one round.",
    },
    "score_25": {
        "label": "Halfway There",
        "desc": "Reach a score of 25 in one round.",
    },
    "score_50": {
        "label": "Flappy Master",
        "desc": "Reach a score of 50 in one round.",
    },
    "new_record": {
        "label": "Personal Best",
        "desc": "Beat your own high score.",
    },
    "night_owl": {
        "label": "Night Owl",
        "desc": "Play a round with Night Mode on.",
    },
    "collector": {
        "label": "Collector",
        "desc": "Unlock every bird skin.",
    },
    "platinum_medal": {
        "label": "Legendary",
        "desc": "Earn a Platinum medal.",
    },
}
ACHIEVEMENT_ORDER = [
    "first_flight", "score_1", "score_10", "score_25", "score_50",
    "new_record", "night_owl", "platinum_medal", "collector",
]
