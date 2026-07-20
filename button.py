import pygame as pg


class Button:
    """
    A clickable rectangular button that can be highlighted either by
    mouse hover OR keyboard focus (they use the same visual state).
    """

    def __init__(self, rect, text, font,
                 base_color=(60, 180, 75), hover_color=(80, 205, 100),
                 text_color=(255, 255, 255), border_color=(0, 0, 0)):
        self.rect = pg.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_color = border_color
        self.focused = False  # set true by keyboard navigation

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def draw(self, win, mouse_pos):
        hovered = self.is_hovered(mouse_pos)
        active = hovered or self.focused

        color = self.hover_color if active else self.base_color
        border_width = 3 if active else 2

        pg.draw.rect(win, color, self.rect, border_radius=12)
        pg.draw.rect(win, self.border_color, self.rect, width=border_width, border_radius=12)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        win.blit(text_surf, text_rect)

        return hovered
