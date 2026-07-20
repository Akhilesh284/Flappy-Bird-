"""
AchievementManager owns the unlocked/locked state of achievements and bird
skins, persists them, and reports back newly-unlocked items each round so
the game can pop up a toast notification.
"""
from constants import ACHIEVEMENTS, SKIN_ORDER, BIRD_SKINS
import persistence


class AchievementManager:
    def __init__(self):
        self.data = persistence.load_data()

    # -------------------------------------------------------------- #
    def is_unlocked(self, achievement_id):
        return bool(self.data["achievements"].get(achievement_id, False))

    def is_skin_unlocked(self, skin_key):
        return skin_key in self.data["unlocked_skins"]

    @property
    def selected_skin(self):
        return self.data.get("selected_skin", "red")

    def select_skin(self, skin_key):
        if self.is_skin_unlocked(skin_key):
            self.data["selected_skin"] = skin_key
            persistence.save_data(self.data)
            return True
        return False

    @property
    def volume(self):
        return self.data.get("volume", 0.7)

    def set_volume(self, value):
        self.data["volume"] = max(0.0, min(1.0, value))
        persistence.save_data(self.data)

    @property
    def night_mode(self):
        return bool(self.data.get("night_mode", False))

    def set_night_mode(self, value):
        self.data["night_mode"] = bool(value)
        persistence.save_data(self.data)

    # -------------------------------------------------------------- #
    def _unlock(self, achievement_id, newly_unlocked_list):
        if not self.is_unlocked(achievement_id):
            self.data["achievements"][achievement_id] = True
            newly_unlocked_list.append(achievement_id)

    def _unlock_skin(self, skin_key, newly_unlocked_skins_list):
        if skin_key not in self.data["unlocked_skins"]:
            self.data["unlocked_skins"].append(skin_key)
            newly_unlocked_skins_list.append(skin_key)

    def _sync_skin_unlocks(self, newly_unlocked_skins_list):
        """Skins unlock automatically once their prerequisite is met."""
        for key in SKIN_ORDER:
            unlock_rule = BIRD_SKINS[key]["unlock"]
            if unlock_rule is None:
                self._unlock_skin(key, newly_unlocked_skins_list)
                continue
            kind, _, value = unlock_rule.partition(":")
            if kind == "achievement" and self.is_unlocked(value):
                self._unlock_skin(key, newly_unlocked_skins_list)
            elif kind == "medal" and self._best_medal_at_least(value):
                self._unlock_skin(key, newly_unlocked_skins_list)

    _MEDAL_RANK = {"bronze": 1, "silver": 2, "gold": 3, "platinum": 4}

    def _best_medal_at_least(self, medal_name):
        best = self.data.get("best_medal")
        if not best:
            return False
        return self._MEDAL_RANK.get(best, 0) >= self._MEDAL_RANK.get(medal_name, 99)

    # -------------------------------------------------------------- #
    def record_round_played(self):
        """Call once at the start of every round (ready -> playing)."""
        newly_unlocked = []
        self._unlock("first_flight", newly_unlocked)
        if self.night_mode:
            self._unlock("night_owl", newly_unlocked)
        if newly_unlocked:
            persistence.save_data(self.data)
        return newly_unlocked

    def record_round_result(self, score, beat_high_score, medal_name):
        """Call once when a round ends (collision / game_over)."""
        newly_unlocked = []
        newly_unlocked_skins = []

        if score >= 1:
            self._unlock("score_1", newly_unlocked)
        if score >= 10:
            self._unlock("score_10", newly_unlocked)
        if score >= 25:
            self._unlock("score_25", newly_unlocked)
        if score >= 50:
            self._unlock("score_50", newly_unlocked)
        if beat_high_score:
            self._unlock("new_record", newly_unlocked)

        if medal_name:
            rank = self._MEDAL_RANK.get(medal_name, 0)
            current_best = self._MEDAL_RANK.get(self.data.get("best_medal"), 0)
            if rank > current_best:
                self.data["best_medal"] = medal_name
            if medal_name == "platinum":
                self._unlock("platinum_medal", newly_unlocked)

        self._sync_skin_unlocks(newly_unlocked_skins)

        if len(self.data["unlocked_skins"]) >= len(SKIN_ORDER):
            self._unlock("collector", newly_unlocked)

        persistence.save_data(self.data)
        return newly_unlocked, newly_unlocked_skins

    def all_achievements_status(self):
        """List of (id, label, desc, unlocked) in display order."""
        from constants import ACHIEVEMENT_ORDER
        out = []
        for aid in ACHIEVEMENT_ORDER:
            info = ACHIEVEMENTS[aid]
            out.append((aid, info["label"], info["desc"], self.is_unlocked(aid)))
        return out
