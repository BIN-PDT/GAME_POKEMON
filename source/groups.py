from entities import Entity

from settings import *
from support import import_image


class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.screen = pygame.display.get_surface()
        self.offset = Vector()
        self.shadow_surf = import_image("meta", "other", "shadow")

    def draw(self, player_center):
        # DRAWING OFFSET.
        self.offset.x = -(player_center[0] - WINDOW_WIDTH / 2)
        self.offset.y = -(player_center[1] - WINDOW_HEIGHT / 2)
        # DRAWING ORDER.
        bg_sprites = filter(lambda sprite: sprite.z < WORLD_LAYERS["main"], self)
        main_sprites = sorted(
            filter(lambda sprite: sprite.z == WORLD_LAYERS["main"], self),
            key=lambda sprite: sprite.y_sort,
        )
        fg_sprites = filter(lambda sprite: sprite.z > WORLD_LAYERS["main"], self)
        # DRAW.
        for layer in (bg_sprites, main_sprites, fg_sprites):
            for sprite in layer:
                # DRAW SHADOW.
                if isinstance(sprite, Entity):
                    pos = sprite.rect.topleft + self.offset + Vector(40, 110)
                    self.screen.blit(self.shadow_surf, pos)
                # DRAW SPRITE.
                self.screen.blit(sprite.image, sprite.rect.topleft + self.offset)
