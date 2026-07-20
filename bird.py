import pygame as pg


class Bird(pg.sprite.Sprite):
    def __init__(self, scale_factor, skin="red"):
        super(Bird, self).__init__()
        self.skin = skin
        self.img_list = self._load_images(skin, scale_factor)

        self.image_index    = 1
        self.image          = self.img_list[self.image_index]
        self.original_image = self.image
        self.angle          = 0
        self.rect           = self.image.get_rect(center=(100, 200))
        self.y_velocity     = 0
        self.gravity        = 10
        self.flap_speed     = 250
        self.anim_counter   = 0
        self.update_on = True

    @staticmethod
    def _load_images(skin, scale_factor):
        # Falls back to the base sprites if a skin variant file is missing,
        # so the game never crashes over a cosmetic asset.
        try:
            up = pg.image.load(f'birdup_{skin}.png').convert_alpha()
            down = pg.image.load(f'birddown_{skin}.png').convert_alpha()
        except (pg.error, FileNotFoundError):
            up = pg.image.load('birdup.png').convert_alpha()
            down = pg.image.load('birddown.png').convert_alpha()
        return [pg.transform.scale_by(up, scale_factor),
                pg.transform.scale_by(down, scale_factor)]

    def update(self, dt):
        if self.update_on:
            self.playAnimation()
            self.applyGravity(dt)

            if self.rect.y <= 0:
                self.rect.y = 0
                self.flap_speed = 0
            elif self.rect.y > 0 and self.flap_speed == 0:
                self.flap_speed = 250
            self.rotateBird()

    def applyGravity(self, dt):
        self.y_velocity += self.gravity * dt
        self.rect.y += self.y_velocity

    def flap(self, dt):
        self.y_velocity = -self.flap_speed * dt

    def playAnimation(self):
        if self.anim_counter == 5:
            self.original_image = self.img_list[self.image_index]

            if self.image_index == 0:
                self.image_index = 1
            else:
                self.image_index = 0

            self.anim_counter = 0
        self.anim_counter += 1

    def rotateBird(self):
        # Going up
        if self.y_velocity < 0:
            self.angle = 15
        # Falling
        else:
            self.angle -= 1
            if self.angle < -90:
                self.angle = -90

        center = self.rect.center
        self.image = pg.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=center)

    def resetPosition(self):
        self.rect.center = (100, 100)
        self.y_velocity = 0
        self.anim_counter = 0
