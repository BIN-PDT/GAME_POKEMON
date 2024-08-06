from settings import *
from support import draw_bar
from game_data import MONSTER_DATA, ATTACK_DATA


class MonsterIndex:
    def __init__(self, monsters, fonts, monster_frames):
        self.screen = pygame.display.get_surface()
        self.monsters = monsters
        self.fonts = fonts
        # TRASITION.
        self.tint_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.tint_surf.set_alpha(200)
        # DIMENSIONS.
        self.main_rect = pygame.FRect(
            0, 0, 0.6 * WINDOW_WIDTH, 0.8 * WINDOW_HEIGHT
        ).move_to(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
        # ITEM LIST.
        self.icon_frames = monster_frames["icons"]
        self.visiable_items = 6
        self.list_width = 0.3 * self.main_rect.width
        self.item_height = self.main_rect.height / self.visiable_items
        self.index = 0
        self.selected_index = None
        self.shadow_surf = pygame.Surface((4, self.main_rect.height))
        self.shadow_surf.set_alpha(100)
        # ITEM.
        self.monster_frames = monster_frames["monsters"]
        self.ui_frames = monster_frames["ui"]
        self.frame_index = 0
        # MAX STATS.
        self.max_stats = {}
        for data in MONSTER_DATA.values():
            for stat, value in data["stats"].items():
                if stat != "element":
                    stat = stat.removeprefix("max_")
                    self.max_stats[stat] = max(self.max_stats.get(stat, 0), value)

    def input(self):
        keys = pygame.key.get_just_pressed()
        # SWITCH.
        if keys[pygame.K_UP]:
            self.index -= 1
        if keys[pygame.K_DOWN]:
            self.index += 1
        self.index = max(0, min(len(self.monsters) - 1, self.index))
        # ARRANGE.
        if keys[pygame.K_SPACE]:
            if self.selected_index != None:
                selected_monster = self.monsters[self.selected_index]
                current_monster = self.monsters[self.index]
                self.monsters[self.selected_index] = current_monster
                self.monsters[self.index] = selected_monster
                self.selected_index = None
            else:
                self.selected_index = self.index

    def display_list(self):
        # BACKGROUND.
        bg_rect = pygame.FRect(
            self.main_rect.topleft, (self.list_width, self.main_rect.height)
        )
        pygame.draw.rect(self.screen, COLORS["gray"], bg_rect, 0, 0, 12, 0, 12)
        # ITEMS.
        v_offset = max(0, self.index - self.visiable_items + 1) * self.item_height
        for index, monster in self.monsters.items():
            name = monster.name
            bg_color = COLORS["gray" if self.index != index else "light"]
            text_color = COLORS["white" if self.selected_index != index else "gold"]
            # BACKGROUND.
            l = self.main_rect.left
            t = self.main_rect.top + index * self.item_height - v_offset
            item_rect = pygame.FRect(l, t, self.list_width, self.item_height)
            # FOREGROUND.
            icon_surf = self.icon_frames[name]
            icon_rect = icon_surf.get_frect(center=item_rect.midleft + Vector(45, 0))
            text_surf = self.fonts["regular"].render(name, False, text_color)
            text_rect = text_surf.get_frect(midleft=item_rect.midleft + Vector(90, 0))
            # DRAW.
            if item_rect.colliderect(self.main_rect):
                if item_rect.collidepoint(self.main_rect.topleft):
                    pygame.draw.rect(self.screen, bg_color, item_rect, 0, 0, 12)
                elif item_rect.collidepoint(self.main_rect.bottomleft + Vector(1, -1)):
                    pygame.draw.rect(self.screen, bg_color, item_rect, 0, 0, 0, 0, 12)
                else:
                    pygame.draw.rect(self.screen, bg_color, item_rect)
                self.screen.blit(icon_surf, icon_rect)
                self.screen.blit(text_surf, text_rect)
        # BREAK LINES.
        for index in range(1, min(self.visiable_items, len(self.monsters))):
            l = self.main_rect.left
            r = l + self.list_width
            y = self.main_rect.top + index * self.item_height
            pygame.draw.line(self.screen, COLORS["light-gray"], (l, y), (r, y))
        # SHADOW LINE.
        shadow_pos = self.main_rect.topleft + Vector(self.list_width - 4, 0)
        self.screen.blit(self.shadow_surf, shadow_pos)

    def display_main(self, dt):
        monster = self.monsters[self.index]
        frames = self.monster_frames[monster.name]["idle"]
        # BACKGROND.
        rect = pygame.FRect(
            self.main_rect.left + self.list_width,
            self.main_rect.top,
            self.main_rect.width - self.list_width,
            self.main_rect.height,
        )
        pygame.draw.rect(self.screen, COLORS["dark"], rect, 0, 0, 0, 12, 0, 12)
        # MONSTER DISPLAY.
        top_rect = pygame.FRect(rect.topleft, (rect.width, 0.4 * rect.height))
        pygame.draw.rect(self.screen, COLORS[monster.element], top_rect, 0, 0, 0, 12)
        # MONSTER ANIMATION.
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index > len(frames):
            self.frame_index = 0
        monster_surf = frames[int(self.frame_index)]
        monster_rect = monster_surf.get_frect(center=top_rect.center)
        self.screen.blit(monster_surf, monster_rect)
        # NAME.
        name_surf = self.fonts["bold"].render(monster.name, False, COLORS["white"])
        name_rect = name_surf.get_frect(topleft=top_rect.topleft + Vector(10, 10))
        self.screen.blit(name_surf, name_rect)
        # LEVEL.
        level_surf = self.fonts["regular"].render(
            f"LV: {monster.level}", False, COLORS["white"]
        )
        level_rect = level_surf.get_frect(
            bottomleft=top_rect.bottomleft + Vector(10, -16)
        )
        self.screen.blit(level_surf, level_rect)
        # EXP BAR.
        draw_bar(
            surface=self.screen,
            frame=pygame.FRect(level_rect.bottomleft, (100, 4)),
            current=monster.xp,
            maximum=monster.level_up,
            fg_color=COLORS["white"],
            bg_color=COLORS["dark"],
        )
        # ELEMENT.
        element_surf = self.fonts["regular"].render(
            monster.element, False, COLORS["white"]
        )
        element_rect = element_surf.get_frect(
            bottomright=top_rect.bottomright + Vector(-10, -10)
        )
        self.screen.blit(element_surf, element_rect)
        # HEALTH & ENERGY BAR DATA.
        bar_data = {
            "width": 0.45 * rect.width,
            "height": 30,
            "top": top_rect.bottom + 0.03 * rect.width,
            "left_side": rect.left + 0.25 * rect.width,
            "right_side": rect.left + 0.75 * rect.width,
        }
        # HEALTH BAR.
        healthbar_rect = pygame.FRect(
            (0, 0), (bar_data["width"], bar_data["height"])
        ).move_to(midtop=(bar_data["left_side"], bar_data["top"]))
        draw_bar(
            surface=self.screen,
            frame=healthbar_rect,
            current=monster.health,
            maximum=monster.get_stat("max_health"),
            fg_color=COLORS["red"],
            bg_color=COLORS["black"],
            radius=2,
        )
        hp_text = f"HP: {monster.health}/{monster.get_stat('max_health')}"
        hp_surf = self.fonts["regular"].render(hp_text, False, COLORS["white"])
        hp_rect = hp_surf.get_frect(midleft=healthbar_rect.midleft + Vector(10, 0))
        self.screen.blit(hp_surf, hp_rect)
        # ENERGY BAR.
        energybar_rect = pygame.FRect(
            (0, 0), (bar_data["width"], bar_data["height"])
        ).move_to(midtop=(bar_data["right_side"], bar_data["top"]))
        draw_bar(
            surface=self.screen,
            frame=energybar_rect,
            current=monster.energy,
            maximum=monster.get_stat("max_energy"),
            fg_color=COLORS["blue"],
            bg_color=COLORS["black"],
            radius=2,
        )
        ep_text = f"EP: {monster.energy}/{monster.get_stat('max_energy')}"
        ep_surf = self.fonts["regular"].render(ep_text, False, COLORS["white"])
        ep_rect = ep_surf.get_frect(midleft=energybar_rect.midleft + Vector(10, 0))
        self.screen.blit(ep_surf, ep_rect)
        # INFO DATA.
        sides = {"left": healthbar_rect.left, "right": energybar_rect.left}
        info_height = rect.bottom - healthbar_rect.bottom
        # STATS.
        stats_rect = (
            pygame.FRect(
                sides["left"], healthbar_rect.bottom, healthbar_rect.width, info_height
            )
            .inflate(0, -60)
            .move(0, 15)
        )
        stats_text_surf = self.fonts["regular"].render("Stats", False, COLORS["white"])
        stats_text_rect = stats_text_surf.get_frect(bottomleft=stats_rect.topleft)
        self.screen.blit(stats_text_surf, stats_text_rect)

        monster_stats = monster.get_stats()
        stat_height = stats_rect.height / len(monster_stats)

        for index, (stat, value) in enumerate(monster_stats.items()):
            stat_rect = pygame.FRect(
                stats_rect.left,
                stats_rect.top + index * stat_height,
                stats_rect.width,
                stat_height,
            )
            # ICON.
            icon_surf = self.ui_frames[stat]
            icon_rect = icon_surf.get_frect(midleft=stat_rect.midleft + Vector(5, 0))
            self.screen.blit(icon_surf, icon_rect)
            # TEXT.
            text_surf = self.fonts["regular"].render(stat, False, COLORS["white"])
            text_rect = text_surf.get_frect(topleft=icon_rect.topleft + Vector(30, -10))
            self.screen.blit(text_surf, text_rect)
            # BAR.
            bar_rect = pygame.FRect(
                text_rect.left,
                text_rect.bottom + 2,
                stat_rect.width - (text_rect.left - stat_rect.left),
                4,
            )
            draw_bar(
                surface=self.screen,
                frame=bar_rect,
                current=value,
                maximum=self.max_stats[stat] * monster.level,
                fg_color=COLORS["white"],
                bg_color=COLORS["black"],
            )
        # ABILITIES.
        ability_rect = stats_rect.copy().move_to(left=sides["right"])
        ability_text_surf = self.fonts["regular"].render(
            "Ability", False, COLORS["white"]
        )
        ability_text_rect = ability_text_surf.get_frect(bottomleft=ability_rect.topleft)
        self.screen.blit(ability_text_surf, ability_text_rect)

        for index, ability in enumerate(monster.get_abilities()):
            element = ATTACK_DATA[ability]["element"]
            text_surf = self.fonts["regular"].render(ability, False, COLORS["black"])
            x = ability_rect.left + index % 2 * ability_rect.width / 2
            y = (20 + ability_rect.top) + index // 2 * (text_surf.height + 20)
            text_rect = text_surf.get_frect(topleft=(x, y))
            pygame.draw.rect(
                self.screen, COLORS[element], text_rect.inflate(15, 10), 0, 4
            )
            self.screen.blit(text_surf, text_rect)

    def update(self, dt):
        self.input()
        self.screen.blit(self.tint_surf, (0, 0))
        self.display_list()
        self.display_main(dt)
