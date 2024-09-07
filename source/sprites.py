from settings import *
from random import uniform, randint
from support import draw_bar
from timers import Timer
from monster import Monster


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
    def __init__(self, pos, surf, groups, biome, level, monsters):
        self.biome = biome
        self.monsters = {
            i: Monster(name, level + randint(-3, 3))
            for i, name in enumerate(monsters.split(","))
        }
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
    def __init__(
        self,
        pos,
        frames,
        groups,
        monster,
        index,
        pos_index,
        entity,
        apply_attack,
        create_monster,
        update_all_monsters,
    ):
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
        self.is_highlighted = False
        # ATTACK.
        self.target_sprite = None
        self.current_attack = None
        self.apply_attack = apply_attack
        self.create_monster = create_monster
        self.update_all_monsters = update_all_monsters
        # TIMERS.
        self.timers = {
            "remove highlight": Timer(250, command=lambda: self.set_highlight(False)),
            "kill": Timer(600, command=self.destroy),
        }

    def animate(self, dt):
        frames = self.frames[self.state]
        self.frame_index += self.animation_speed * dt
        if self.frame_index > len(frames):
            self.frame_index = 0
            # APPLY ATTACK.
            if self.state == "attack":
                self.apply_attack(
                    target=self.target_sprite,
                    attack=self.current_attack,
                    amount=self.monster.get_base_damage(self.current_attack),
                )
                self.state = "idle"

        self.image = frames[int(self.frame_index)]

        if self.is_highlighted:
            mask_surf = pygame.mask.from_surface(self.image).to_surface()
            mask_surf.set_colorkey("black")
            self.image = mask_surf

    def set_highlight(self, value):
        self.is_highlighted = value
        if value:
            self.timers["remove highlight"].activate()

    def activate_attack(self, target, attack):
        self.state = "attack"
        self.frame_index = 0

        self.target_sprite = target
        self.current_attack = attack
        self.monster.reduce_energy(attack)

    def delay_kill(self, monster_data):
        if not self.timers["kill"].is_active:
            self.next_monster_data = monster_data
            self.timers["kill"].activate()

    def destroy(self):
        if self.next_monster_data:
            self.create_monster(*self.next_monster_data)
        self.kill()
        self.update_all_monsters("resume")

    def update(self, dt):
        for timer in self.timers.values():
            timer.update()
        self.animate(dt)
        self.monster.update(dt)


class MonsterOutlineSprite(pygame.sprite.Sprite):
    def __init__(self, frames, groups, monster_sprite):
        self.z = BATTLE_LAYERS["outline"]
        super().__init__(groups)
        self.monster_sprite = monster_sprite
        self.frames = frames

        self.image = self.frames[self.monster_sprite.state][
            int(self.monster_sprite.frame_index)
        ]
        self.rect = self.image.get_frect(center=self.monster_sprite.rect.center)

    def update(self, _):
        self.image = self.frames[self.monster_sprite.state][
            int(self.monster_sprite.frame_index)
        ]
        # CHECK DEATH.
        if not self.monster_sprite.groups():
            self.kill()


class MonsterNameSprite(pygame.sprite.Sprite):
    def __init__(self, pos, groups, monster_sprite, font):
        self.z = BATTLE_LAYERS["name"]
        super().__init__(groups)
        self.monster_sprite = monster_sprite
        text_surf = font.render(monster_sprite.monster.name, False, COLORS["black"])
        padding = 10

        self.image = pygame.Surface(
            (text_surf.get_width() + 2 * padding, text_surf.get_height() + 2 * padding)
        )
        self.image.fill(COLORS["white"])
        self.image.blit(text_surf, (padding, padding))
        self.rect = self.image.get_frect(midtop=pos)

    def update(self, _):
        # CHECK DEATH.
        if not self.monster_sprite.groups():
            self.kill()


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
        # CHECK DEATH.
        if not self.monster_sprite.groups():
            self.kill()


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
                    f"{current:.0f}/{maximum:.0f}", False, COLORS["black"]
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
        # CHECK DEATH.
        if not self.monster_sprite.groups():
            self.kill()


class AttackSprite(AnimatedSprite):
    def __init__(self, pos, frames, groups):
        super().__init__(pos, frames, groups, BATTLE_LAYERS["overlay"])
        self.rect.center = pos

    def animte(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index <= len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()


class TimedSprite(Sprite):
    def __init__(self, pos, surf, groups, duration):
        super().__init__(pos, surf, groups, BATTLE_LAYERS["overlay"])
        self.rect.center = pos
        self.death_timer = Timer(duration, autostart=True, command=self.kill)

    def update(self, _):
        self.death_timer.update()
