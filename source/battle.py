from settings import *
from game_data import ATTACK_DATA
from sprites import (
    MonsterSprite,
    MonsterOutlineSprite,
    MonsterNameSprite,
    MonsterLevelSprite,
    MonsterStatsSprite,
    AttackSprite,
    TimedSprite,
)
from groups import BattleSprites
from support import draw_bar
from timers import Timer
from random import choice


class Battle:
    def __init__(
        self, player_monsters, opponent_monsters, monster_frames, bg_surf, fonts
    ):
        # GENERAL.
        self.battle_end = False
        self.screen = pygame.display.get_surface()
        self.monster_frames = monster_frames
        self.bg_surf = bg_surf
        self.fonts = fonts
        self.monster_data = {"player": player_monsters, "opponent": opponent_monsters}
        # TIMERS.
        self.timers = {"opponent delay": Timer(600, command=self.opponent_attack)}
        # GROUPS.
        self.battle_sprites = BattleSprites()
        self.player_sprites = pygame.sprite.Group()
        self.opponent_sprites = pygame.sprite.Group()
        # CONTROL.
        self.current_monster = None
        self.selection_mode = None
        self.selection_side = "player"
        self.selected_attack = None
        self.indexes = {
            "general": 0,
            "monster": 0,
            "attacks": 0,
            "switch": 0,
            "target": 0,
        }

        self.setup()

    def setup(self):
        for entity, monsters in self.monster_data.items():
            belligerents = {i: monster for i, monster in monsters.items() if i <= 2}
            for index, monster in belligerents.items():
                self.create_monster(monster, index, index, entity)
        # REMOVE OPPONENT MONSTERS DATA.
        for index in range(len(self.opponent_sprites)):
            del self.monster_data["opponent"][index]

    def create_monster(self, monster, index, pos_index, entity):
        frames = self.monster_frames["monsters"][monster.name]
        outlined_frames = self.monster_frames["outlines"][monster.name]

        if entity == "player":
            pos = list(BATTLE_POSITIONS["left"].values())[pos_index]
            groups = self.battle_sprites, self.player_sprites
            # FLIP THE FRAMES.
            frames = {
                state: [pygame.transform.flip(frame, True, False) for frame in frames]
                for state, frames in frames.items()
            }
            outlined_frames = {
                state: [pygame.transform.flip(frame, True, False) for frame in frames]
                for state, frames in outlined_frames.items()
            }
        else:
            pos = list(BATTLE_POSITIONS["right"].values())[pos_index]
            groups = self.battle_sprites, self.opponent_sprites

        sprite = MonsterSprite(
            pos=pos,
            frames=frames,
            groups=groups,
            monster=monster,
            index=index,
            pos_index=pos_index,
            entity=entity,
            apply_attack=self.apply_attack,
            create_monster=self.create_monster,
        )
        MonsterOutlineSprite(outlined_frames, self.battle_sprites, sprite)
        # UI.
        name_pos = (
            sprite.rect.midleft + Vector(10, -40)
            if entity == "player"
            else sprite.rect.midright + Vector(-35, -70)
        )
        name_sprite = MonsterNameSprite(
            name_pos, self.battle_sprites, sprite, self.fonts["regular"]
        )

        anchor = (
            name_sprite.rect.bottomleft
            if entity == "player"
            else name_sprite.rect.bottomright
        )
        MonsterLevelSprite(
            entity, anchor, self.battle_sprites, sprite, self.fonts["small"]
        )

        stats_pos = sprite.rect.midbottom + Vector(0, 40)
        MonsterStatsSprite(stats_pos, self.battle_sprites, sprite, self.fonts["small"])

    def input(self):
        if self.current_monster and self.selection_mode:
            keys = pygame.key.get_just_pressed()
            # LIMIT CHOICES.
            if self.selection_mode == "general":
                limiter = len(BATTLE_CHOICES["full"])
            if self.selection_mode == "attacks":
                limiter = len(self.current_monster.monster.get_abilities(all=False))
            if self.selection_mode == "switch":
                limiter = len(self.available_monsters)
            if self.selection_mode == "target":
                limiter = len(
                    self.opponent_sprites
                    if self.selection_side == "opponent"
                    else self.player_sprites
                )
            # SWITCH CHOICE.
            if keys[pygame.K_DOWN]:
                self.indexes[self.selection_mode] += 1
                self.indexes[self.selection_mode] %= limiter
            if keys[pygame.K_UP]:
                self.indexes[self.selection_mode] -= 1
                self.indexes[self.selection_mode] %= limiter
            # CHOOSE CHOICE.
            if keys[pygame.K_SPACE]:
                # SWITCH MODE.
                if self.selection_mode == "switch":
                    index, monster = list(self.available_monsters.items())[
                        self.indexes["switch"]
                    ]
                    self.current_monster.kill()
                    self.create_monster(
                        monster, index, self.current_monster.pos_index, "player"
                    )
                    self.selection_mode = None
                    self.update_all_monsters("resume")
                # TARGET MODE.
                if self.selection_mode == "target":
                    # TARGET.
                    group = (
                        self.opponent_sprites
                        if self.selection_side == "opponent"
                        else self.player_sprites
                    )
                    sprites = {sprite.pos_index: sprite for sprite in group}
                    target = sprites[list(sprites.keys())[self.indexes["target"]]]
                    # ATTACK.
                    if self.selected_attack:
                        self.current_monster.activate_attack(
                            target, self.selected_attack
                        )
                        self.current_monster = None
                        self.selection_mode = None
                        self.selected_attack = None
                    # CATCH.
                    else:
                        if target.monster.health < 0.9 * target.monster.get_stat(
                            "max_health"
                        ):
                            self.monster_data["player"][
                                len(self.monster_data["player"])
                            ] = target.monster
                            target.delay_kill(None)
                            self.update_all_monsters("resume")
                        else:
                            TimedSprite(
                                pos=target.rect.center,
                                surf=self.monster_frames["ui"]["cross"],
                                groups=self.battle_sprites,
                                duration=1000,
                            )
                # ATTACK MODE.
                if self.selection_mode == "attacks":
                    self.selection_mode = "target"
                    self.selected_attack = self.current_monster.monster.get_abilities(
                        all=False
                    )[self.indexes["attacks"]]
                    self.selection_side = ATTACK_DATA[self.selected_attack]["target"]
                # GENERAL MODE.
                if self.selection_mode == "general":
                    # ATTACK.
                    if self.indexes["general"] == 0:
                        self.selection_mode = "attacks"
                    # DEFENSE.
                    if self.indexes["general"] == 1:
                        self.current_monster.monster.is_defending = True
                        self.update_all_monsters("resume")
                        self.current_monster = None
                        self.selection_mode = None
                        self.indexes["general"] = 0
                    # SWITCH.
                    if self.indexes["general"] == 2:
                        self.selection_mode = "switch"
                    # CATCH.
                    if self.indexes["general"] == 3:
                        self.selection_mode = "target"
                        self.selection_side = "opponent"
                # RESET INDEXES.
                self.indexes = {key: 0 for key in self.indexes}
            # BACK.
            if keys[pygame.K_ESCAPE]:
                if self.selection_mode in ("attacks", "switch", "target"):
                    self.selection_mode = "general"

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    # BATTLE SYSTEM.
    def check_active(self):
        for sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            if sprite.monster.initiative >= 100:
                sprite.monster.is_defending = False
                self.update_all_monsters("pause")
                sprite.monster.initiative = 0
                sprite.set_highlight(True)
                self.current_monster = sprite
                # PLAYER SIDE.
                if sprite.entity == "player":
                    self.selection_mode = "general"
                # OPPONENT SIDE.
                else:
                    self.timers["opponent delay"].activate()

    def update_all_monsters(self, option):
        for sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            sprite.monster.is_paused = True if option == "pause" else False

    def apply_attack(self, target, attack, amount):
        # ATTACK ANIMATION.
        AttackSprite(
            pos=target.rect.center,
            frames=self.monster_frames["attacks"][ATTACK_DATA[attack]["animation"]],
            groups=self.battle_sprites,
        )
        # CALCULATE DAMAGE.
        attack_element = ATTACK_DATA[attack]["element"]
        target_element = target.monster.element

        if (
            attack_element == "fire"
            and target_element == "plant"
            or attack_element == "plant"
            and target_element == "water"
            or attack_element == "water"
            and target_element == "fire"
        ):
            amount *= 2
        if (
            attack_element == "fire"
            and target_element == "water"
            or attack_element == "water"
            and target_element == "plant"
            or attack_element == "plant"
            and target_element == "fire"
        ):
            amount /= 2

        target_defense = 1 - target.monster.get_stat("defense") / 2000
        if target.monster.is_defending:
            target_defense -= 0.2
        target_defense = max(0, min(1, target_defense))
        # UPDATE HEALTH.
        target.monster.health -= amount * target_defense
        self.check_death()
        # RESUME THE BATTLE.
        self.update_all_monsters("resume")

    def check_death(self):
        for sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            if sprite.monster.health <= 0:
                # PLAYER SIDE.
                if self.player_sprites in sprite.groups():
                    active_monsters = [
                        (sprite.index, sprite.monster) for sprite in self.player_sprites
                    ]
                    available_monsters = {
                        index: monster
                        for index, monster in self.monster_data["player"].items()
                        if (index, monster) not in active_monsters
                        and monster.health > 0
                    }
                    new_monster_data = (
                        [
                            (monster, index, sprite.pos_index, "player")
                            for index, monster in available_monsters.items()
                        ][0]
                        if available_monsters
                        else None
                    )
                # OPPONENT SIDE.
                else:
                    # REPLACE WITH NEW MONSTER.
                    new_monster_data = (
                        (
                            list(self.monster_data["opponent"].values())[0],
                            sprite.index,
                            sprite.pos_index,
                            "opponent",
                        )
                        if self.monster_data["opponent"]
                        else None
                    )
                    if self.monster_data["opponent"]:
                        del self.monster_data["opponent"][
                            min(self.monster_data["opponent"])
                        ]
                    # GET XP.
                    xp_amount = sprite.monster.level * 100 / len(self.player_sprites)
                    for player_sprite in self.player_sprites:
                        player_sprite.monster.update_xp(xp_amount)
                sprite.delay_kill(new_monster_data)

    def opponent_attack(self):
        ability = choice(self.current_monster.monster.get_abilities(all=False))
        target = choice(
            self.opponent_sprites.sprites()
            if ATTACK_DATA[ability]["target"] == "player"
            else self.player_sprites.sprites()
        )
        self.current_monster.activate_attack(target, ability)

    def check_end_battle(self):
        # OPPONENT DEFEATED.
        if not self.battle_end and len(self.opponent_sprites) == 0:
            self.battle_end = True
        # PLAYER DEFEATED.
        if len(self.player_sprites) == 0:
            pygame.quit()
            exit()

    # UI.
    def draw_ui(self):
        if self.current_monster:
            if self.selection_mode == "general":
                self.draw_general()
            if self.selection_mode == "attacks":
                self.draw_attacks()
            if self.selection_mode == "switch":
                self.draw_switch()

    def draw_general(self):
        ui_frames = self.monster_frames["ui"]
        for index, (_, data) in enumerate(BATTLE_CHOICES["full"].items()):
            if index == self.indexes["general"]:
                surf = ui_frames[f"{data['icon']}_highlight"]
            else:
                surf = pygame.transform.grayscale(ui_frames[data["icon"]])
            rect = surf.get_frect(
                midleft=self.current_monster.rect.midright + data["pos"]
            )
            self.screen.blit(surf, rect)

    def draw_attacks(self):
        # DATA.
        abilities = self.current_monster.monster.get_abilities(all=False)
        width, height = 150, 200
        visible_attacks = 4
        item_height = height / visible_attacks
        v_offset = max(0, self.indexes["attacks"] - visible_attacks + 1) * item_height
        # BACKGROUND.
        bg_rect = pygame.FRect(0, 0, width, height).move_to(
            midleft=self.current_monster.rect.midright + Vector(10, 0)
        )
        pygame.draw.rect(self.screen, COLORS["white"], bg_rect, 0, 5)
        # FOREGROUND.
        for index, ability in enumerate(abilities):
            is_selected = index == self.indexes["attacks"]
            # TEXT.
            if is_selected:
                element = ATTACK_DATA[ability]["element"]
                text_color = COLORS[element if element != "normal" else "black"]
            else:
                text_color = COLORS["light"]
            text_surf = self.fonts["regular"].render(ability, False, text_color)
            # RECT.
            offset = Vector(0, item_height / 2 + index * item_height - v_offset)
            text_rect = text_surf.get_frect(center=bg_rect.midtop + offset)
            text_bg_rect = pygame.FRect(0, 0, width, item_height).move_to(
                center=text_rect.center
            )
            # DRAW.
            if bg_rect.collidepoint(text_rect.center):
                if is_selected:
                    if text_bg_rect.collidepoint(bg_rect.topleft):
                        pygame.draw.rect(
                            self.screen,
                            COLORS["dark white"],
                            text_bg_rect,
                            border_top_left_radius=5,
                            border_top_right_radius=5,
                        )
                    elif text_bg_rect.collidepoint(bg_rect.bottomleft + Vector(1, -1)):
                        pygame.draw.rect(
                            self.screen,
                            COLORS["dark white"],
                            text_bg_rect,
                            border_bottom_left_radius=5,
                            border_bottom_right_radius=5,
                        )
                    else:
                        pygame.draw.rect(
                            self.screen, COLORS["dark white"], text_bg_rect
                        )
                self.screen.blit(text_surf, text_rect)

    def draw_switch(self):
        # DATA.
        active_monsters = [
            (sprite.index, sprite.monster) for sprite in self.player_sprites
        ]
        self.available_monsters = {
            index: monster
            for index, monster in self.monster_data["player"].items()
            if (index, monster) not in active_monsters and monster.health > 0
        }
        width, height = 300, 320
        visible_monsters = 4
        item_height = height / visible_monsters
        v_offset = max(0, self.indexes["switch"] - visible_monsters + 1) * item_height
        # BACKGROUND.
        bg_rect = pygame.FRect(0, 0, width, height).move_to(
            midleft=self.current_monster.rect.midright + Vector(10, 0)
        )
        pygame.draw.rect(self.screen, COLORS["white"], bg_rect, 0, 5)
        # FOREGROUND.
        for index, monster in enumerate(self.available_monsters.values()):
            is_selected = self.indexes["switch"] == index
            # ITEM.
            offset = Vector(0, index * item_height - v_offset)
            item_rect = pygame.FRect(bg_rect.topleft + offset, (width, item_height))
            # ICON.
            icon_surf = self.monster_frames["icons"][monster.name]
            icon_rect = icon_surf.get_frect(midleft=item_rect.midleft + Vector(20, 0))
            # NAME & LEVEL.
            text = f"{monster.name} ({monster.level})"
            text_color = COLORS["red" if is_selected else "black"]
            text_surf = self.fonts["regular"].render(text, False, text_color)
            text_rect = text_surf.get_frect(topleft=icon_rect.topleft + Vector(80, 0))
            # DRAW.
            if bg_rect.collidepoint(item_rect.center):
                # BACKGROUND.
                selected_rect = item_rect.copy()
                if is_selected:
                    if selected_rect.collidepoint(bg_rect.topleft):
                        pygame.draw.rect(
                            self.screen,
                            COLORS["dark white"],
                            selected_rect,
                            border_top_left_radius=5,
                            border_top_right_radius=5,
                        )
                    elif selected_rect.collidepoint(bg_rect.bottomleft + Vector(1, -1)):
                        pygame.draw.rect(
                            self.screen,
                            COLORS["dark white"],
                            selected_rect,
                            border_bottom_left_radius=5,
                            border_bottom_right_radius=5,
                        )
                    else:
                        pygame.draw.rect(
                            self.screen, COLORS["dark white"], selected_rect
                        )
                # ICON & NAME & LEVEL.
                self.screen.blit(icon_surf, icon_rect)
                self.screen.blit(text_surf, text_rect)
                # HEALTH BAR.
                draw_bar(
                    self.screen,
                    pygame.FRect(text_rect.bottomleft + Vector(0, 4), (100, 4)),
                    monster.health,
                    monster.get_stat("max_health"),
                    COLORS["red"],
                    COLORS["black"],
                )
                # ENERGY BAR.
                draw_bar(
                    self.screen,
                    pygame.FRect(text_rect.bottomleft + Vector(0, 10), (80, 4)),
                    monster.energy,
                    monster.get_stat("max_energy"),
                    COLORS["blue"],
                    COLORS["black"],
                )

    def update(self, dt):
        self.check_end_battle()
        # BACKGROUND.
        self.screen.blit(self.bg_surf, (0, 0))
        # FOREGROUND.
        self.input()
        self.update_timers()
        self.battle_sprites.update(dt)
        self.check_active()
        self.battle_sprites.draw(
            current_monster_sprite=self.current_monster,
            mode=self.selection_mode,
            side=self.selection_side,
            target_index=self.indexes["target"],
            player_sprites=self.player_sprites,
            opponent_sprites=self.opponent_sprites,
        )
        self.draw_ui()
