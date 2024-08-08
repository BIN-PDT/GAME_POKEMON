from settings import *
from game_data import ATTACK_DATA
from sprites import (
    MonsterSprite,
    MonsterOutlineSprite,
    MonsterNameSprite,
    MonsterLevelSprite,
    MonsterStatsSprite,
)
from groups import BattleSprites
from support import draw_bar


class Battle:
    def __init__(
        self, player_monsters, opponent_monsters, monster_frames, bg_surf, fonts
    ):
        # GENERAL.
        self.screen = pygame.display.get_surface()
        self.monster_frames = monster_frames
        self.bg_surf = bg_surf
        self.fonts = fonts
        self.monster_data = {"player": player_monsters, "opponent": opponent_monsters}
        # GROUPS.
        self.battle_sprites = BattleSprites()
        self.player_sprites = pygame.sprite.Group()
        self.opponent_sprites = pygame.sprite.Group()
        # CONTROL.
        self.current_monster = None
        self.selection_mode = None
        self.selection_side = "player"
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

        sprite = MonsterSprite(pos, frames, groups, monster, index, pos_index, entity)
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

            if self.selection_mode == "general":
                limiter = len(BATTLE_CHOICES["full"])
            if self.selection_mode == "attacks":
                limiter = len(self.current_monster.monster.get_abilities(all=False))
            if self.selection_mode == "switch":
                limiter = len(self.available_monsters)
            if limiter > 0:
                if keys[pygame.K_DOWN]:
                    self.indexes[self.selection_mode] += 1
                    self.indexes[self.selection_mode] %= limiter
                if keys[pygame.K_UP]:
                    self.indexes[self.selection_mode] -= 1
                    self.indexes[self.selection_mode] %= limiter
            if keys[pygame.K_SPACE]:
                if self.selection_mode == "general":
                    # ATTACK.
                    if self.indexes["general"] == 0:
                        self.selection_mode = "attacks"
                    # DEFENSE.
                    if self.indexes["general"] == 1:
                        self.update_all_monsters("resume")
                        self.current_monster = None
                        self.selection_mode = None
                        self.indexes["general"] = 0
                    # SWITCH.
                    if self.indexes["general"] == 2:
                        self.selection_mode = "switch"
                    # CATCH.
                    if self.indexes["general"] == 3:
                        pass
            if keys[pygame.K_ESCAPE]:
                if self.selection_mode in ("attacks", "switch", "target"):
                    self.selection_mode = "general"

    # BATTLE SYSTEM.
    def check_active(self):
        for sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            if sprite.monster.initiative >= 100:
                self.update_all_monsters("pause")
                sprite.monster.initiative = 0
                sprite.set_highlight(True)
                self.current_monster = sprite
                self.selection_mode = "general"

    def update_all_monsters(self, option):
        for sprite in self.player_sprites.sprites() + self.opponent_sprites.sprites():
            sprite.monster.is_paused = True if option == "pause" else False

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
        # BACKGROUND.
        self.screen.blit(self.bg_surf, (0, 0))
        # FOREGROUND.
        self.input()
        self.battle_sprites.update(dt)
        self.check_active()
        self.battle_sprites.draw(self.current_monster)
        self.draw_ui()
