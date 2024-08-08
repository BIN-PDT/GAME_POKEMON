from settings import *
from sprites import (
    MonsterSprite,
    MonsterNameSprite,
    MonsterLevelSprite,
    MonsterStatsSprite,
)
from groups import BattleSprites


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

        self.setup()

    def setup(self):
        for entity, monsters in self.monster_data.items():
            belligerents = {i: monster for i, monster in monsters.items() if i <= 2}
            for index, monster in belligerents.items():
                self.create_monster(monster, index, index, entity)

    def create_monster(self, monster, index, pos_index, entity):
        frames = self.monster_frames["monsters"][monster.name]
        if entity == "player":
            pos = list(BATTLE_POSITIONS["left"].values())[pos_index]
            groups = self.battle_sprites, self.player_sprites
            # FLIP THE FRAMES.
            frames = {
                state: [pygame.transform.flip(frame, True, False) for frame in frames]
                for state, frames in frames.items()
            }
        else:
            pos = list(BATTLE_POSITIONS["right"].values())[pos_index]
            groups = self.battle_sprites, self.opponent_sprites

        sprite = MonsterSprite(pos, frames, groups, monster, index, pos_index, entity)
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

    def update(self, dt):
        # BACKGROUND.
        self.screen.blit(self.bg_surf, (0, 0))
        # FOREGROUND.
        self.battle_sprites.update(dt)
        self.battle_sprites.draw()
