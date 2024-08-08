from settings import *
from random import uniform
from support import draw_bar


# OVERWOLRD SPRITES.
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


class TransitionSprite(Sprite):
    def __init__(self, pos, size, target, groups):
        surf = pygame.Surface(size)
        super().__init__(pos, surf, groups)
        self.target = target


# BATTLE SPRITES.
class MonsterSprite(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, monster, index, pos_index, entity):
        self.z = BATTLE_LAYERS["monster"]
        # DATA.
        self.index = index
        self.entity = entity
        self.monster = monster

        self.pos_index = pos_index
        self.frames, self.frame_index = frames, 0
        self.state = "idle"
        self.animation_speed = ANIMATION_SPEED + uniform(-1, 1)
        # SPRITE SETUP.
        super().__init__(groups)
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(center=pos)

    def animate(self, dt):
        frames = self.frames[self.state]
        self.frame_index += self.animation_speed * dt
        if self.frame_index > len(frames):
            self.frame_index = 0

        self.image = frames[int(self.frame_index)]

    def update(self, dt):
        self.animate(dt)


class MonsterNameSprite(pygame.sprite.Sprite):
    def __init__(self, pos, groups, monster_sprite, font):
        self.z = BATTLE_LAYERS["name"]
        super().__init__(groups)
        text_surf = font.render(monster_sprite.monster.name, False, COLORS["black"])
        padding = 10

        self.image = pygame.Surface(
            (text_surf.get_width() + 2 * padding, text_surf.get_height() + 2 * padding)
        )
        self.image.fill(COLORS["white"])
        self.image.blit(text_surf, (padding, padding))
        self.rect = self.image.get_frect(midtop=pos)


class MonsterLevelSprite(pygame.sprite.Sprite):
    def __init__(self, entity, pos, groups, monster_sprite, font):
        self.z = BATTLE_LAYERS["name"]
        super().__init__(groups)
        self.monster_sprite = monster_sprite
        self.font = font

        self.image = pygame.Surface((60, 26))
        self.rect = (
            self.image.get_frect(topleft=pos)
            if entity == "player"
            else self.image.get_frect(topright=pos)
        )
        self.xp_rect = pygame.FRect(0, self.rect.height - 2, self.rect.width, 2)

    def update(self, _):
        # BACKGROUND.
        self.image.fill(COLORS["white"])
        # LEVEL.
        text_surf = self.font.render(
            f"LV: {self.monster_sprite.monster.level}", False, COLORS["black"]
        )
        text_rect = text_surf.get_frect(
            center=(self.rect.width / 2, self.rect.height / 2)
        )
        self.image.blit(text_surf, text_rect)
        # XP.
        draw_bar(
            self.image,
            self.xp_rect,
            self.monster_sprite.monster.xp,
            self.monster_sprite.monster.level_up,
            COLORS["black"],
            COLORS["white"],
            0,
        )


class MonsterStatsSprite(pygame.sprite.Sprite):
    def __init__(self, pos, groups, monster_sprite, font):
        self.z = BATTLE_LAYERS["overlay"]
        super().__init__(groups)
        self.monster_sprite = monster_sprite
        self.font = font
        self.stat_colors = (COLORS["red"], COLORS["blue"], COLORS["gray"])

        self.image = pygame.Surface((150, 65))
        self.rect = self.image.get_frect(midbottom=pos)

    def update(self, _):
        # BACKGROUND.
        self.image.fill(COLORS["white"])
        # FOREGROUND.
        for index, (current, maximum) in enumerate(
            self.monster_sprite.monster.get_info()
        ):
            color = self.stat_colors[index]
            if index < 2:
                # STAT.
                text_surf = self.font.render(
                    f"{current}/{maximum}", False, COLORS["black"]
                )
                pos = 0.05 * self.rect.width, index * self.rect.height / 2 + (
                    5 if index == 0 else 0
                )
                text_rect = text_surf.get_frect(topleft=pos)
                self.image.blit(text_surf, text_rect)
                # BAR.
                bar_rect = pygame.FRect(
                    text_rect.bottomleft, (0.9 * self.rect.width, 4)
                )
                draw_bar(
                    self.image, bar_rect, current, maximum, color, COLORS["black"], 2
                )
            else:
                bar_rect = pygame.FRect((0, self.rect.height - 2), (self.rect.width, 2))
                draw_bar(
                    self.image, bar_rect, current, maximum, color, COLORS["white"], 0
                )
