import pygame as pg
import sys, time, math

from bird import Bird
from pipe import Pipe
from button import Button
from slider import Slider
from achievements import AchievementManager
from constants import (
    DAY_PALETTE, NIGHT_PALETTE, MEDAL_THRESHOLDS, medal_for_score,
    BIRD_SKINS, SKIN_ORDER, ACHIEVEMENTS,
)

pg.init()
pg.mixer.init()


class Game:
    def __init__(self):
        # WINDOW CONFIG
        self.width = 600
        self.height = 768
        self.scale_factor = 1.5

        # SETTINGS
        self.win = pg.display.set_mode((self.width, self.height))
        pg.display.set_caption('Flappy Bird')
        self.clock = pg.time.Clock()

        self.font_tiny   = pg.font.Font('font.ttf', 15)
        self.font_small  = pg.font.Font('font.ttf', 20)
        self.font_medium = pg.font.Font('font.ttf', 26)
        self.font_large  = pg.font.Font('font.ttf', 31)
        self.font_title  = pg.font.Font('font.ttf', 52)

        # PERSISTED PLAYER DATA (volume, night mode, skins, achievements)
        self.achievements = AchievementManager()

        # SOUND (fails gracefully if files are missing)
        self.flap_sound = self.safe_load_sound('sounds/flap.wav')
        self.crash_sound = self.safe_load_sound('sounds/crash.mp3')
        self.pre_mute_volume = self.achievements.volume or 0.7
        self.apply_volume(self.achievements.volume)

        # GAME STATE
        # 'loading' -> 'menu' -> ('skins' | 'achievements' | 'settings') -> 'ready' -> 'playing' -> 'game_over'
        self.game_state = 'loading'
        self.loading_start = time.time()
        self.loading_duration = 1.6
        self.previous_state = 'menu'   # where BACK returns to from a submenu

        self.game_over_sound_played = False
        self.round_achievements_processed = False
        self.beat_high_score = False
        self.round_start_high = 0
        self.new_high_score_time = 0
        self.round_medal = None

        # achievement / skin unlock toast queue
        self.toast_queue = []
        self.current_toast = None
        self.current_toast_start = 0
        self.toast_duration = 2.6

        # night mode + palette
        self.night_mode = self.achievements.night_mode

        # bird and pipes
        self.bird = Bird(self.scale_factor, skin=self.achievements.selected_skin)
        self.pipes = []
        self.pipe_generate_counter = 70

        # focus indices for keyboard navigation
        self.menu_focus_index = 0
        self.gameover_focus_index = 0
        self.settings_focus_index = 0   # 0=volume 1=night toggle 2=back
        self.skins_focus_index = 2      # 0=left 1=right 2=equip 3=back
        self.skin_preview_index = SKIN_ORDER.index(self.achievements.selected_skin)
        self.achievements_scroll = 0

        self.default_values()
        self.loading_images()
        self.create_buttons()
        self.update_score_text()

        self.gameLoop()

    # ------------------------------------------------------------------ #
    # SETUP HELPERS
    # ------------------------------------------------------------------ #
    def safe_load_sound(self, path):
        try:
            return pg.mixer.Sound(path)
        except Exception:
            print(f"[Warning] Could not load sound: {path} (game will continue without it)")
            return None

    def play_sound(self, sound):
        if sound is not None:
            sound.play()

    def apply_volume(self, value):
        for snd in (self.flap_sound, self.crash_sound):
            if snd is not None:
                snd.set_volume(value)

    def set_volume(self, value):
        value = max(0.0, min(1.0, value))
        self.achievements.set_volume(value)
        self.apply_volume(value)
        if value > 0:
            self.pre_mute_volume = value
        self.volume_slider.value = value

    def toggle_mute(self):
        if self.achievements.volume > 0:
            self.pre_mute_volume = self.achievements.volume
            self.set_volume(0.0)
        else:
            self.set_volume(self.pre_mute_volume or 0.7)
        self.mute_icon.text = "UNMUTE" if self.achievements.volume == 0 else "MUTE"

    def toggle_night_mode(self):
        self.night_mode = not self.night_mode
        self.achievements.set_night_mode(self.night_mode)
        self.night_toggle_button.text = self.night_label()

    def night_label(self):
        return "NIGHT MODE: ON" if self.night_mode else "NIGHT MODE: OFF"

    def palette(self):
        return NIGHT_PALETTE if self.night_mode else DAY_PALETTE

    def create_buttons(self):
        btn_w, btn_h = 260, 55
        cx = self.width // 2
        red = dict(base_color=(190, 60, 60), hover_color=(215, 85, 85))
        blue = dict(base_color=(70, 110, 200), hover_color=(95, 135, 225))
        grey = dict(base_color=(120, 120, 130), hover_color=(145, 145, 155))

        # ---- Menu screen buttons ----
        self.start_button = Button((cx - btn_w // 2, 330, btn_w, btn_h), "START", self.font_medium)
        self.skins_button = Button((cx - btn_w // 2, 395, btn_w, btn_h), "BIRD SKINS", self.font_medium, **blue)
        self.achievements_button = Button((cx - btn_w // 2, 460, btn_w, btn_h), "ACHIEVEMENTS", self.font_medium, **blue)
        self.settings_button = Button((cx - btn_w // 2, 525, btn_w, btn_h), "SETTINGS", self.font_medium, **grey)
        self.menu_exit_button = Button((cx - btn_w // 2, 590, btn_w, btn_h), "EXIT", self.font_medium, **red)
        self.menu_buttons = [self.start_button, self.skins_button, self.achievements_button,
                              self.settings_button, self.menu_exit_button]

        # ---- Game-over screen buttons ----
        self.restart_button   = Button((cx - btn_w // 2, 430, btn_w, btn_h), "RESTART", self.font_medium)
        self.main_menu_button = Button((cx - btn_w // 2, 495, btn_w, btn_h), "MAIN MENU", self.font_medium, **blue)
        self.gameover_exit_button = Button((cx - btn_w // 2, 560, btn_w, btn_h), "EXIT", self.font_medium, **red)
        self.gameover_buttons = [self.restart_button, self.main_menu_button, self.gameover_exit_button]

        # ---- Settings screen ----
        self.volume_slider = Slider((cx - 120, 330, 240, 30), value=self.achievements.volume, label="VOLUME")
        self.night_toggle_button = Button((130, 420, 350, btn_h), self.night_label(),
                                           self.font_medium, **blue)
        self.settings_back_button = Button((cx - btn_w // 2, 640, btn_w, btn_h), "BACK", self.font_medium, **grey)

        # ---- Skins screen ----
        self.skin_left_button  = Button((cx - 220, 330, 60, 60), "<", self.font_large, **blue)
        self.skin_right_button = Button((cx + 160, 330, 60, 60), ">", self.font_large, **blue)
        self.skin_equip_button = Button((cx - btn_w // 2, 470, btn_w, btn_h), "EQUIP", self.font_medium)
        self.skins_back_button = Button((cx - btn_w // 2, 640, btn_w, btn_h), "BACK", self.font_medium, **grey)

        # ---- Achievements screen ----
        self.achievements_back_button = Button((cx - btn_w // 2, 690, btn_w, btn_h), "BACK", self.font_medium, **grey)

        # ---- Small persistent mute icon (bottom-right, mouse-only, all states) ----
        self.mute_icon = Button((self.width - 130, self.height - 56, 110, 40),
                                 "UNMUTE" if self.achievements.volume == 0 else "MUTE",
                                 self.font_small, **blue)

    def default_values(self):
        self.move_speed1 = 70
        self.move_speed2 = 250
        self.score = 0
        self.new_high_score_time = 0

        with open('highscore.txt', 'r') as file:
            self.high = int(file.read())

        self.round_start_high = self.high

    def loading_images(self):
        # background
        self.bk_ground1_img = pg.transform.scale_by(pg.image.load('bg.png').convert(), self.scale_factor)
        self.bk_ground2_img = pg.transform.scale_by(pg.image.load('bg.png').convert(), self.scale_factor)

        self.bk_ground1_rect = self.bk_ground1_img.get_rect()
        self.bk_ground2_rect = self.bk_ground2_img.get_rect()

        self.bk_ground1_rect.x = 0
        self.bk_ground2_rect.x = self.bk_ground1_rect.right
        self.bk_ground1_rect.y = -300
        self.bk_ground2_rect.y = -300

        # ground
        self.ground1_img = pg.transform.scale_by(pg.image.load('ground.png').convert(), self.scale_factor)
        self.ground2_img = pg.transform.scale_by(pg.image.load('ground.png').convert(), self.scale_factor)

        self.ground1_rect = self.ground1_img.get_rect()
        self.ground2_rect = self.ground2_img.get_rect()

        self.ground1_rect.x = 0
        self.ground2_rect.x = self.ground1_rect.right
        self.ground1_rect.y = 568
        self.ground2_rect.y = 568

        # night overlay (translucent surface reused every frame)
        self.night_overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        self.night_overlay.fill(NIGHT_PALETTE["overlay"])

        # preload + cache every skin's artwork once, at two sizes (menu bird, skins-screen preview)
        self.skin_menu_images = {}
        self.skin_preview_images = {}
        for skin_key in SKIN_ORDER:
            try:
                img = pg.image.load(f'birdup_{skin_key}.png').convert_alpha()
            except (pg.error, FileNotFoundError):
                img = pg.image.load('birdup.png').convert_alpha()
            self.skin_menu_images[skin_key] = pg.transform.scale_by(img, 1.8 * self.scale_factor)
            self.skin_preview_images[skin_key] = pg.transform.scale_by(img, 2.6 * self.scale_factor)

        # bird preview shown on the menu -- refreshed whenever the equipped skin changes
        self.refresh_bird_preview()

    def refresh_bird_preview(self):
        skin = self.achievements.selected_skin
        self.bird_at_starting = self.skin_menu_images.get(skin, self.skin_menu_images["red"])
        self.bird_at_starting_rect = self.bird_at_starting.get_rect(center=(290, 130))

    def skin_preview_image(self, skin_key):
        return self.skin_preview_images.get(skin_key, self.skin_preview_images["red"])

    # ------------------------------------------------------------------ #
    # MAIN LOOP
    # ------------------------------------------------------------------ #
    def gameLoop(self):
        last_time = time.time()
        while True:
            new_time = time.time()
            dt = new_time - last_time
            last_time = new_time

            self.handle_events(dt)
            self.update_everything(dt)
            self.draw_everything()
            self.check_collision()
            pg.display.update()
            self.clock.tick(60)

    # ------------------------------------------------------------------ #
    # EVENTS
    # ------------------------------------------------------------------ #
    def handle_events(self, dt):
        mouse_pos = pg.mouse.get_pos()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            # persistent mute icon works in any state except loading, mouse only
            if event.type == pg.MOUSEBUTTONDOWN and self.game_state != 'loading':
                if self.mute_icon.rect.collidepoint(mouse_pos):
                    self.toggle_mute()

            if self.game_state == 'loading':
                pass  # no input during the loading animation

            elif self.game_state == 'menu':
                self.handle_menu_events(event, mouse_pos)

            elif self.game_state == 'settings':
                self.handle_settings_events(event, mouse_pos)

            elif self.game_state == 'skins':
                self.handle_skins_events(event, mouse_pos)

            elif self.game_state == 'achievements':
                self.handle_achievements_events(event, mouse_pos)

            elif self.game_state == 'ready':
                if (event.type == pg.KEYDOWN and event.key in (pg.K_SPACE, pg.K_RETURN)) or \
                   (event.type == pg.MOUSEBUTTONDOWN and event.button == 1):
                    self.game_state = 'playing'
                    self.play_sound(self.flap_sound)
                    self.bird.flap(dt)
                    unlocked = self.achievements.record_round_played()
                    self.queue_achievement_toasts(unlocked, [])

            elif self.game_state == 'playing':
                if (event.type == pg.KEYDOWN and event.key == pg.K_SPACE) or \
                   (event.type == pg.MOUSEBUTTONDOWN and event.button == 1):
                    self.play_sound(self.flap_sound)
                    self.bird.flap(dt)

            elif self.game_state == 'game_over':
                self.handle_gameover_events(event, mouse_pos)

    def handle_menu_events(self, event, mouse_pos):
        if event.type == pg.KEYDOWN:
            if event.key in (pg.K_DOWN, pg.K_RIGHT, pg.K_TAB):
                self.menu_focus_index = (self.menu_focus_index + 1) % len(self.menu_buttons)
            elif event.key in (pg.K_UP, pg.K_LEFT):
                self.menu_focus_index = (self.menu_focus_index - 1) % len(self.menu_buttons)
            elif event.key in (pg.K_RETURN, pg.K_SPACE):
                self.activate_menu_button(self.menu_focus_index)

        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.menu_buttons):
                if btn.rect.collidepoint(mouse_pos):
                    self.activate_menu_button(i)

    def activate_menu_button(self, index):
        btn = self.menu_buttons[index]
        if btn is self.start_button:
            self.go_to_ready()
        elif btn is self.skins_button:
            self.previous_state = 'menu'
            self.skin_preview_index = SKIN_ORDER.index(self.achievements.selected_skin)
            self.game_state = 'skins'
        elif btn is self.achievements_button:
            self.previous_state = 'menu'
            self.game_state = 'achievements'
        elif btn is self.settings_button:
            self.previous_state = 'menu'
            self.game_state = 'settings'
        elif btn is self.menu_exit_button:
            pg.quit()
            sys.exit()

    # ---- Settings ---- #
    def handle_settings_events(self, event, mouse_pos):
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            self.game_state = self.previous_state
            return

        self.volume_slider.focused = (self.settings_focus_index == 0)
        if self.volume_slider.handle_event(event, mouse_pos):
            self.set_volume(self.volume_slider.value)

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_TAB or event.key == pg.K_DOWN:
                self.settings_focus_index = (self.settings_focus_index + 1) % 3
            elif event.key == pg.K_UP:
                self.settings_focus_index = (self.settings_focus_index - 1) % 3
            elif event.key in (pg.K_RETURN, pg.K_SPACE):
                if self.settings_focus_index == 1:
                    self.toggle_night_mode()
                elif self.settings_focus_index == 2:
                    self.game_state = self.previous_state

        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.night_toggle_button.rect.collidepoint(mouse_pos):
                self.toggle_night_mode()
            elif self.settings_back_button.rect.collidepoint(mouse_pos):
                self.game_state = self.previous_state

    # ---- Skins ---- #
    def handle_skins_events(self, event, mouse_pos):
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            self.game_state = self.previous_state
            return

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                self.skin_preview_index = (self.skin_preview_index - 1) % len(SKIN_ORDER)
            elif event.key == pg.K_RIGHT:
                self.skin_preview_index = (self.skin_preview_index + 1) % len(SKIN_ORDER)
            elif event.key == pg.K_TAB:
                self.skins_focus_index = (self.skins_focus_index + 1) % 4
            elif event.key in (pg.K_RETURN, pg.K_SPACE):
                if self.skins_focus_index == 0:
                    self.skin_preview_index = (self.skin_preview_index - 1) % len(SKIN_ORDER)
                elif self.skins_focus_index == 1:
                    self.skin_preview_index = (self.skin_preview_index + 1) % len(SKIN_ORDER)
                elif self.skins_focus_index == 2:
                    self.try_equip_preview_skin()
                elif self.skins_focus_index == 3:
                    self.game_state = self.previous_state

        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.skin_left_button.rect.collidepoint(mouse_pos):
                self.skin_preview_index = (self.skin_preview_index - 1) % len(SKIN_ORDER)
            elif self.skin_right_button.rect.collidepoint(mouse_pos):
                self.skin_preview_index = (self.skin_preview_index + 1) % len(SKIN_ORDER)
            elif self.skin_equip_button.rect.collidepoint(mouse_pos):
                self.try_equip_preview_skin()
            elif self.skins_back_button.rect.collidepoint(mouse_pos):
                self.game_state = self.previous_state

    def try_equip_preview_skin(self):
        skin_key = SKIN_ORDER[self.skin_preview_index]
        if self.achievements.select_skin(skin_key):
            self.refresh_bird_preview()

    # ---- Achievements ---- #
    def handle_achievements_events(self, event, mouse_pos):
        if event.type == pg.KEYDOWN and event.key in (pg.K_ESCAPE, pg.K_RETURN, pg.K_SPACE):
            self.game_state = self.previous_state
            return
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.achievements_back_button.rect.collidepoint(mouse_pos):
                self.game_state = self.previous_state

    def handle_gameover_events(self, event, mouse_pos):
        if event.type == pg.KEYDOWN:
            if event.key in (pg.K_DOWN, pg.K_RIGHT, pg.K_TAB):
                self.gameover_focus_index = (self.gameover_focus_index + 1) % len(self.gameover_buttons)
            elif event.key in (pg.K_UP, pg.K_LEFT):
                self.gameover_focus_index = (self.gameover_focus_index - 1) % len(self.gameover_buttons)
            elif event.key in (pg.K_RETURN, pg.K_SPACE):
                self.activate_gameover_button(self.gameover_focus_index)

        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.gameover_buttons):
                if btn.rect.collidepoint(mouse_pos):
                    self.activate_gameover_button(i)

    def activate_gameover_button(self, index):
        btn = self.gameover_buttons[index]
        if btn is self.restart_button:
            self.restart_game()
        elif btn is self.main_menu_button:
            self.go_to_menu()
        elif btn is self.gameover_exit_button:
            pg.quit()
            sys.exit()

    # ------------------------------------------------------------------ #
    # STATE TRANSITIONS
    # ------------------------------------------------------------------ #
    def go_to_ready(self):
        self.game_state = 'ready'
        self.reset_round()

    def go_to_menu(self):
        self.game_state = 'menu'
        self.reset_round()

    def restart_game(self):
        self.game_state = 'ready'
        self.reset_round()

    def reset_round(self):
        self.game_over_sound_played = False
        self.round_achievements_processed = False
        self.beat_high_score = False
        self.round_start_high = self.high
        self.round_medal = None
        self.score = 0
        self.update_score_text()

        self.pipes.clear()
        self.pipe_generate_counter = 71
        self.bird = Bird(self.scale_factor, skin=self.achievements.selected_skin)
        self.start_monitoring = False

    def queue_achievement_toasts(self, achievement_ids, skin_ids):
        for aid in achievement_ids:
            label = ACHIEVEMENTS[aid]["label"]
            self.toast_queue.append(f"ACHIEVEMENT UNLOCKED: {label}")
        for skin_key in skin_ids:
            if BIRD_SKINS[skin_key]["unlock"] is None:
                continue  # the default starter skin isn't a "surprise" unlock
            label = BIRD_SKINS[skin_key]["label"]
            self.toast_queue.append(f"NEW SKIN UNLOCKED: {label}")

    # ------------------------------------------------------------------ #
    # UPDATE
    # ------------------------------------------------------------------ #
    def update_everything(self, dt):
        self.update_toasts()

        if self.game_state == 'loading':
            if time.time() - self.loading_start >= self.loading_duration:
                self.game_state = 'menu'
            return

        if self.game_state != 'playing':
            return

        # parallax background
        self.bk_ground1_rect.x -= self.move_speed1 * dt
        self.bk_ground2_rect.x -= self.move_speed1 * dt

        if self.bk_ground1_rect.right < 0:
            self.bk_ground1_rect.x = self.bk_ground2_rect.right
        if self.bk_ground2_rect.right < 0:
            self.bk_ground2_rect.x = self.bk_ground1_rect.right

        # ground
        self.ground1_rect.x -= self.move_speed2 * dt
        self.ground2_rect.x -= self.move_speed2 * dt

        if self.ground1_rect.right < 0:
            self.ground1_rect.x = self.ground2_rect.right
        if self.ground2_rect.right < 0:
            self.ground2_rect.x = self.ground1_rect.right

        # pipes
        if self.pipe_generate_counter > 70:
            self.pipes.append(Pipe(self.scale_factor, self.move_speed2))
            self.pipe_generate_counter = 0
        self.pipe_generate_counter += 1

        for pipe in self.pipes:
            pipe.update(dt)

        if len(self.pipes) != 0 and self.pipes[0].rect_up.right < 0:
            self.pipes.pop(0)

        self.bird.update(dt)
        self.check_score()

    def update_toasts(self):
        now = time.time()
        if self.current_toast is None and self.toast_queue:
            self.current_toast = self.toast_queue.pop(0)
            self.current_toast_start = now
        elif self.current_toast is not None and now - self.current_toast_start > self.toast_duration:
            self.current_toast = None

    def check_collision(self):
        if self.game_state != 'playing' or not self.pipes:
            return

        hit_ground = self.bird.rect.bottom > 568
        hit_pipe = self.bird.rect.colliderect(self.pipes[0].rect_up) or \
                   self.bird.rect.colliderect(self.pipes[0].rect_down)

        if hit_ground or hit_pipe:
            self.bird.update_on = False
            self.game_state = 'game_over'
            if not self.game_over_sound_played:
                self.play_sound(self.crash_sound)
                self.game_over_sound_played = True

            if not self.round_achievements_processed:
                self.round_achievements_processed = True
                self.round_medal = medal_for_score(self.score)
                new_achievements, new_skins = self.achievements.record_round_result(
                    self.score, self.beat_high_score, self.round_medal)
                self.queue_achievement_toasts(new_achievements, new_skins)

    def check_score(self):
        if not self.pipes:
            return

        pipe = self.pipes[0]
        if (self.bird.rect.left > pipe.rect_down.left and
                self.bird.rect.right < pipe.rect_down.right and
                not getattr(self, 'start_monitoring', False)):
            self.start_monitoring = True

        if self.bird.rect.left > pipe.rect_down.right and getattr(self, 'start_monitoring', False):
            self.start_monitoring = False
            self.score += 1
            self.update_score_text()

        # Trigger the "new high score" flash exactly once per round: the moment
        # this round's score first passes whatever the high score was when the
        # round started. beat_high_score then stays True for the rest of the
        # round (including the game-over screen) instead of re-triggering on
        # every further point.
        if self.score > self.round_start_high and not self.beat_high_score:
            self.beat_high_score = True
            self.new_high_score_time = time.time()

        # Keep the persisted high score in sync independently of the flash logic.
        if self.score > self.high:
            self.high = self.score
            with open('highscore.txt', 'w') as file:
                file.write(str(self.high))

        self.high_text = self.font_small.render(f'HIGH : {self.high}', True, self.palette()["text"])

    def update_score_text(self):
        pal = self.palette()
        self.score_text = self.font_small.render(f'Score : {self.score}', True, pal["text"])
        self.score_text_rect = self.score_text.get_rect(center=(100, 30))
        self.high_text = self.font_small.render(f'HIGH : {self.high}', True, pal["text"])
        self.high_text_rect = self.high_text.get_rect(center=(460, 30))

    # ------------------------------------------------------------------ #
    # DRAW
    # ------------------------------------------------------------------ #
    def draw_everything(self):
        mouse_pos = pg.mouse.get_pos()

        if self.game_state == 'loading':
            self.draw_loading_screen()
            return

        pal = self.palette()

        # background
        self.win.blit(self.bk_ground1_img, self.bk_ground1_rect)
        self.win.blit(self.bk_ground2_img, self.bk_ground2_rect)

        in_round = self.game_state in ('ready', 'playing', 'game_over')

        if in_round:
            for pipe in self.pipes:
                pipe.drawPipe(self.win)

        # ground
        self.win.blit(self.ground1_img, self.ground1_rect)
        self.win.blit(self.ground2_img, self.ground2_rect)

        if in_round:
            self.win.blit(self.bird.image, self.bird.rect)

        # night tint sits over the scenery/bird but under the UI text/panels
        if self.night_mode:
            self.win.blit(self.night_overlay, (0, 0))

        if in_round:
            self.win.blit(self.score_text, self.score_text_rect)
            self.win.blit(self.high_text, self.high_text_rect)

            if self.beat_high_score and self.game_state == 'playing' and \
                    (time.time() - self.new_high_score_time) < 3:
                high_text = self.font_large.render(">>> NEW HIGH SCORE <<<", True, pal["accent"])
                high_rect = high_text.get_rect(center=(300, 240))
                self.win.blit(high_text, high_rect)

        if self.game_state == 'menu':
            self.draw_menu(mouse_pos)
        elif self.game_state == 'settings':
            self.draw_settings(mouse_pos)
        elif self.game_state == 'skins':
            self.draw_skins(mouse_pos)
        elif self.game_state == 'achievements':
            self.draw_achievements(mouse_pos)
        elif self.game_state == 'ready':
            self.draw_ready_prompt()
        elif self.game_state == 'game_over':
            self.draw_game_over(mouse_pos)

        # persistent mute icon, always on top
        self.mute_icon.draw(self.win, mouse_pos)

        self.draw_toast()

    # ---- Loading screen ---- #
    def draw_loading_screen(self):
        pal = self.palette()
        self.win.fill((90, 190, 205) if not self.night_mode else (18, 22, 48))

        elapsed = time.time() - self.loading_start
        progress = min(1.0, elapsed / self.loading_duration)

        # bouncing bird
        bounce_y = 300 + math.sin(elapsed * 6) * 18
        bird_rect = self.bird_at_starting.get_rect(center=(self.width // 2, bounce_y))
        self.win.blit(self.bird_at_starting, bird_rect)

        title = self.font_title.render("FLAPPY BIRD", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.width // 2, 200))
        self.win.blit(title, title_rect)

        # progress bar
        bar_w, bar_h = 320, 22
        bar_x = self.width // 2 - bar_w // 2
        bar_y = 420
        pg.draw.rect(self.win, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), border_radius=11, width=3)
        pg.draw.rect(self.win, (255, 215, 60), (bar_x + 3, bar_y + 3, int((bar_w - 6) * progress), bar_h - 6),
                     border_radius=8)

        dots = "." * (int(elapsed * 3) % 4)
        loading_text = self.font_medium.render(f"Loading{dots}", True, (255, 255, 255))
        loading_rect = loading_text.get_rect(center=(self.width // 2, bar_y + 50))
        self.win.blit(loading_text, loading_rect)

    # ---- Menu ---- #
    def draw_menu(self, mouse_pos):
        pal = self.palette()
        title_text = self.font_title.render("FLAPPY BIRD", True, pal["text"])
        title_rect = title_text.get_rect(center=(self.width // 2, 190))
        self.win.blit(title_text, title_rect)

        self.win.blit(self.bird_at_starting, self.bird_at_starting_rect)

        best_medal = self.achievements.data.get("best_medal")
        if best_medal:
            self.draw_medal_icon((self.width // 2 + 90, 130), best_medal, radius=22)

        for i, btn in enumerate(self.menu_buttons):
            btn.focused = (i == self.menu_focus_index)
            btn.draw(self.win, mouse_pos)

    # ---- Settings ---- #
    def draw_settings(self, mouse_pos):
        pal = self.palette()
        self.draw_panel_backdrop()

        title = self.font_large.render("SETTINGS", True, pal["text"])
        self.win.blit(title, title.get_rect(center=(self.width // 2, 250)))

        self.volume_slider.draw(self.win, self.font_small, pal["text"])

        self.night_toggle_button.focused = (self.settings_focus_index == 1)
        self.night_toggle_button.draw(self.win, mouse_pos)

        self.settings_back_button.focused = (self.settings_focus_index == 2)
        self.settings_back_button.draw(self.win, mouse_pos)

    # ---- Skins ---- #
    def draw_skins(self, mouse_pos):
        pal = self.palette()
        self.draw_panel_backdrop()

        title = self.font_large.render("BIRD SKINS", True, pal["text"])
        self.win.blit(title, title.get_rect(center=(self.width // 2, 230)))

        skin_key = SKIN_ORDER[self.skin_preview_index]
        skin_info = BIRD_SKINS[skin_key]
        unlocked = self.achievements.is_skin_unlocked(skin_key)

        preview_img = self.skin_preview_image(skin_key)
        preview_rect = preview_img.get_rect(center=(self.width // 2, 300))
        if not unlocked:
            preview_img = preview_img.copy()
            preview_img.set_alpha(90)
        self.win.blit(preview_img, preview_rect)

        name_color = pal["text"] if unlocked else (150, 150, 150)
        name_text = self.font_medium.render(skin_info["label"], True, name_color)
        self.win.blit(name_text, name_text.get_rect(center=(self.width // 2, 400)))

        if unlocked:
            status = "EQUIPPED" if skin_key == self.achievements.selected_skin else "Tap EQUIP to select"
            status_color = pal["accent"] if skin_key == self.achievements.selected_skin else pal["text"]
        else:
            status = self.skin_unlock_hint(skin_key)
            status_color = (170, 60, 60)
        status_text = self.font_small.render(status, True, status_color)
        self.win.blit(status_text, status_text.get_rect(center=(self.width // 2, 432)))

        self.skin_left_button.focused = (self.skins_focus_index == 0)
        self.skin_right_button.focused = (self.skins_focus_index == 1)
        self.skin_left_button.draw(self.win, mouse_pos)
        self.skin_right_button.draw(self.win, mouse_pos)

        self.skin_equip_button.text = "EQUIPPED" if skin_key == self.achievements.selected_skin else "EQUIP"
        equip_disabled = (not unlocked) or (skin_key == self.achievements.selected_skin)
        self.skin_equip_button.focused = (self.skins_focus_index == 2)
        if equip_disabled:
            pg.draw.rect(self.win, (170, 170, 175), self.skin_equip_button.rect, border_radius=12)
            pg.draw.rect(self.win, (0, 0, 0), self.skin_equip_button.rect, width=2, border_radius=12)
            txt = self.font_medium.render(self.skin_equip_button.text, True, (255, 255, 255))
            self.win.blit(txt, txt.get_rect(center=self.skin_equip_button.rect.center))
        else:
            self.skin_equip_button.draw(self.win, mouse_pos)

        self.skins_back_button.focused = (self.skins_focus_index == 3)
        self.skins_back_button.draw(self.win, mouse_pos)

        # small dots indicating position in the skin list
        dot_y = 560
        total = len(SKIN_ORDER)
        start_x = self.width // 2 - (total - 1) * 14 // 2
        for i in range(total):
            color = pal["accent"] if i == self.skin_preview_index else (170, 170, 170)
            pg.draw.circle(self.win, color, (start_x + i * 14, dot_y), 5)

    def skin_unlock_hint(self, skin_key):
        rule = BIRD_SKINS[skin_key]["unlock"]
        if rule is None:
            return "Unlocked"
        kind, _, value = rule.partition(":")
        if kind == "achievement":
            return f"Locked - {ACHIEVEMENTS[value]['label']}"
        if kind == "medal":
            return f"Locked - Earn a {value.capitalize()} medal"
        return "Locked"

    # ---- Achievements ---- #
    def draw_achievements(self, mouse_pos):
        pal = self.palette()
        self.draw_panel_backdrop()

        title = self.font_large.render("ACHIEVEMENTS", True, pal["text"])
        self.win.blit(title, title.get_rect(center=(self.width // 2, 130)))

        entries = self.achievements.all_achievements_status()
        start_y = 175
        row_h = 56
        for i, (aid, label, desc, unlocked) in enumerate(entries):
            y = start_y + i * row_h
            row_rect = pg.Rect(40, y, self.width - 80, row_h - 8)

            bg_color = (235, 250, 235) if unlocked else (230, 230, 230)
            if self.night_mode:
                bg_color = (35, 60, 40) if unlocked else (35, 35, 45)
            pg.draw.rect(self.win, bg_color, row_rect, border_radius=10)
            pg.draw.rect(self.win, (0, 0, 0), row_rect, width=1, border_radius=10)

            self.draw_check_or_lock((row_rect.x + 26, row_rect.centery), unlocked)

            label_color = pal["text"] if unlocked else (140, 140, 140)
            label_surf = self.font_small.render(label, True, label_color)
            self.win.blit(label_surf, (row_rect.x + 50, row_rect.y + 6))

            desc_color = (90, 90, 90) if unlocked else (150, 150, 150)
            if self.night_mode:
                desc_color = (190, 190, 200) if unlocked else (120, 120, 130)
            desc_surf = self.font_tiny.render(desc, True, desc_color)
            self.win.blit(desc_surf, (row_rect.x + 50, row_rect.y + 28))

        self.achievements_back_button.draw(self.win, mouse_pos)

    def draw_check_or_lock(self, center, unlocked):
        x, y = center
        if unlocked:
            pg.draw.circle(self.win, (60, 180, 75), (x, y), 14)
            pg.draw.lines(self.win, (255, 255, 255), False,
                           [(x - 6, y), (x - 2, y + 5), (x + 7, y - 7)], 3)
        else:
            pg.draw.circle(self.win, (150, 150, 150), (x, y), 14)
            pg.draw.rect(self.win, (255, 255, 255), (x - 5, y - 2, 10, 8), border_radius=1)
            pg.draw.arc(self.win, (255, 255, 255), (x - 5, y - 9, 10, 10), 0, math.pi, 2)

    # ---- Shared UI helpers ---- #
    def draw_panel_backdrop(self):
        """Slightly dims the gameplay scene so submenu panels/text stay readable."""
        dim = pg.Surface((self.width, self.height), pg.SRCALPHA)
        dim.fill((0, 0, 0, 90) if not self.night_mode else (0, 0, 0, 150))
        self.win.blit(dim, (0, 0))

    def draw_medal_icon(self, center, medal_name, radius=18):
        color_map = {name: color for name, _, color in MEDAL_THRESHOLDS}
        color = color_map.get(medal_name, (200, 200, 200))
        x, y = center
        pg.draw.circle(self.win, color, (x, y), radius)
        pg.draw.circle(self.win, (60, 45, 20), (x, y), radius, width=2)
        # simple 5-point star cut-out in the middle
        star_pts = []
        for i in range(10):
            r = radius * (0.5 if i % 2 else 0.9)
            ang = math.pi / 2 + i * math.pi / 5
            star_pts.append((x + r * math.cos(ang), y - r * math.sin(ang)))
        pg.draw.polygon(self.win, (255, 255, 255), star_pts, width=1)

    def draw_ready_prompt(self):
        pal = self.palette()
        prompt = self.font_medium.render('Press SPACE / Click to Fly', True, pal["text"])
        prompt_rect = prompt.get_rect(center=(self.width // 2, 300))
        self.win.blit(prompt, prompt_rect)


    def draw_game_over(self, mouse_pos):
        pal = self.palette()
        self.draw_panel_backdrop()

        game_over = self.font_large.render("GAME OVER", True, (220, 60, 60))
        game_over_rect = game_over.get_rect(center=(300, 150))
        self.win.blit(game_over, game_over_rect)

        final_score = self.font_medium.render(f"Score : {self.score}", True, pal["text_light"])
        final_score_rect = final_score.get_rect(center=(300, 210))
        self.win.blit(final_score, final_score_rect)

        if self.round_medal:
            self.draw_medal_icon((300, 265), self.round_medal, radius=26)
            medal_text = self.font_small.render(self.round_medal.upper() + " MEDAL", True, pal["text_light"])
            self.win.blit(medal_text, medal_text.get_rect(center=(300, 305)))

        if self.beat_high_score:
            congrats = self.font_large.render(f"NEW HIGH SCORE : {self.high}", True, (255, 205, 60))
            congrats_rect = congrats.get_rect(center=(300, 345))
            self.win.blit(congrats, congrats_rect)

        for i, btn in enumerate(self.gameover_buttons):
            btn.focused = (i == self.gameover_focus_index)
            btn.draw(self.win, mouse_pos)


    def draw_toast(self):
        if not self.current_toast:
            return
        elapsed = time.time() - self.current_toast_start
        # slide down then hold then fade out
        slide = min(1.0, elapsed / 0.3)
        fade_out = max(0.0, min(1.0, (self.toast_duration - elapsed) / 0.4))
        y = -50 + slide * 90
        alpha = int(255 * fade_out)

        text_surf = self.font_small.render(self.current_toast, True, (30, 25, 10))
        panel_w = text_surf.get_width() + 50
        panel_h = 50
        panel = pg.Surface((panel_w, panel_h), pg.SRCALPHA)
        pg.draw.rect(panel, (255, 215, 90, alpha), (0, 0, panel_w, panel_h), border_radius=14)
        pg.draw.rect(panel, (120, 85, 10, alpha), (0, 0, panel_w, panel_h), width=2, border_radius=14)
        text_surf.set_alpha(alpha)
        panel.blit(text_surf, (25, (panel_h - text_surf.get_height()) // 2))

        panel_rect = panel.get_rect(midtop=(self.width // 2, int(y)))
        self.win.blit(panel, panel_rect)


game = Game()
