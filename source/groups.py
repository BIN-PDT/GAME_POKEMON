from settings import *
from supports import import_image

from entities import Entity


class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.screen = pygame.display.get_surface()
        self.offset = Vector()
        self.shadow_surf = import_image("meta", "other", "shadow")
        self.notice_surf = import_image("meta", "ui", "notice")

    def draw(self, player):
        # DRAWING OFFSET.
        self.offset.x = -(player.rect.centerx - WINDOW_WIDTH / 2)
        self.offset.y = -(player.rect.centery - WINDOW_HEIGHT / 2)
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
                # DRAW NOTICE.
                if sprite is player and sprite.is_noticed:
                    rect = self.notice_surf.get_frect(midbottom=sprite.rect.midtop)
                    self.screen.blit(self.notice_surf, rect.topleft + self.offset)


class BattleSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.screen = pygame.display.get_surface()

    def draw(
        self,
        current_monster_sprite,
        mode,
        side,
        target_index,
        player_sprites,
        opponent_sprites,
    ):
        # GET TARGETED MONSTER.
        group = opponent_sprites if side == "opponent" else player_sprites
        sprites = {sprite.pos_index: sprite for sprite in group}
        target = sprites[list(sprites.keys())[target_index]] if sprites else None
        # DRAW.
        for sprite in sorted(self, key=lambda sprite: sprite.z):
            # DRAW OUTLINE SPRITE.
            if sprite.z == BATTLE_LAYERS["outline"]:
                if (
                    sprite.monster_sprite == current_monster_sprite
                    and not (mode == "target" and side == "player")
                    or mode == "target"
                    and sprite.monster_sprite == target
                ):
                    self.screen.blit(sprite.image, sprite.rect)
            # DRAW OTHER SPRITES.
            else:
                self.screen.blit(sprite.image, sprite.rect)
