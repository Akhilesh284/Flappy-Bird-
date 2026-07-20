import pygame as pg


class Slider:
    """A horizontal 0.0-1.0 slider, draggable with the mouse or adjustable
    with LEFT/RIGHT when focused (keyboard navigation)."""

    def __init__(self, rect, value=0.5, label="", track_color=(210, 210, 210),
                 fill_color=(70, 110, 200), knob_color=(255, 255, 255),
                 border_color=(0, 0, 0)):
        self.rect = pg.Rect(rect)
        self.value = max(0.0, min(1.0, value))
        self.label = label
        self.track_color = track_color
        self.fill_color = fill_color
        self.knob_color = knob_color
        self.border_color = border_color
        self.dragging = False
        self.focused = False

    def _knob_x(self):
        return self.rect.x + int(self.value * self.rect.width)

    def handle_event(self, event, mouse_pos):
        changed = False
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            grab_zone = self.rect.inflate(0, 16)
            if grab_zone.collidepoint(mouse_pos):
                self.dragging = True
                self._set_from_mouse(mouse_pos[0])
                changed = True
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pg.MOUSEMOTION and self.dragging:
            self._set_from_mouse(mouse_pos[0])
            changed = True
        elif event.type == pg.KEYDOWN and self.focused:
            if event.key == pg.K_LEFT:
                self.value = max(0.0, self.value - 0.05)
                changed = True
            elif event.key == pg.K_RIGHT:
                self.value = min(1.0, self.value + 0.05)
                changed = True
        return changed

    def _set_from_mouse(self, mouse_x):
        rel = (mouse_x - self.rect.x) / self.rect.width
        self.value = max(0.0, min(1.0, rel))

    def draw(self, win, font, text_color=(0, 0, 0)):
        track_rect = pg.Rect(self.rect.x, self.rect.y + self.rect.height // 2 - 4,
                              self.rect.width, 8)
        pg.draw.rect(win, self.track_color, track_rect, border_radius=4)

        fill_width = int(self.value * self.rect.width)
        if fill_width > 0:
            fill_rect = pg.Rect(self.rect.x, track_rect.y, fill_width, 8)
            pg.draw.rect(win, self.fill_color, fill_rect, border_radius=4)

        knob_radius = 12 if not self.focused else 14
        knob_center = (self._knob_x(), self.rect.y + self.rect.height // 2)
        pg.draw.circle(win, self.knob_color, knob_center, knob_radius)
        pg.draw.circle(win, self.border_color, knob_center, knob_radius, width=2)

        if self.label:
            label_surf = font.render(f"{self.label} : {int(self.value * 100)}", True, text_color)
            label_rect = label_surf.get_rect(midbottom=(self.rect.centerx, self.rect.y - 6))
            win.blit(label_surf, label_rect)
