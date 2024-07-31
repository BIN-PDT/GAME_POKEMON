from settings import *


class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z=WORLD_LAYERS["main"]):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft=pos)
        self.z = z
        self.y_sort = self.rect.centery
        # COLLISION.
        self.hitbox = self.rect.copy()


class AnimatedSprite(Sprite):
    def __init__(self, pos, frames, groups, z=WORLD_LAYERS["main"]):
        self.frames, self.frame_index = frames, 0
        super().__init__(pos, self.frames[self.frame_index], groups, z)

    def animte(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index > len(self.frames):
            self.frame_index = 0

        self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        self.animte(dt)


class BorderSprite(Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)
        # COLLISION.
        self.hitbox = self.rect.copy()


class ColliableSprite(Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)
        # COLLISION.
        self.hitbox = self.rect.inflate(0, -0.6 * self.rect.height)


class MonsterPatchSprite(Sprite):
    def __init__(self, pos, surf, groups, biome):
        self.biome = biome
        z = WORLD_LAYERS["main" if self.biome != "sand" else "bg"]
        super().__init__(pos, surf, groups, z)
        self.y_sort -= 40
