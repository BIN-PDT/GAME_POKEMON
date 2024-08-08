from settings import *
from game_data import *
from os.path import join

from sprites import (
    Sprite,
    AnimatedSprite,
    BorderSprite,
    ColliableSprite,
    MonsterPatchSprite,
    TransitionSprite,
)
from entities import Character, Player
from groups import AllSprites
from dialog import DialogTree
from support import *
from monster import Monster
from monster_index import MonsterIndex
from battle import Battle


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Pokemon Hunter")
        self.clock = pygame.time.Clock()
        # PLAYER MONSTERS.
        self.player_monsters = {
            0: Monster("Charmadillo", 30),
            1: Monster("Friolera", 29),
            2: Monster("Larvea", 3),
            3: Monster("Atrox", 24),
            4: Monster("Sparchu", 24),
            5: Monster("Gulfin", 24),
            6: Monster("Jacana", 2),
            7: Monster("Pouch", 3),
        }
        self.dummy_monsters = {
            0: Monster("Atrox", 24),
            1: Monster("Gulfin", 13),
            2: Monster("Jacana", 2),
            3: Monster("Pouch", 3),
        }
        self.index_show = False
        # GROUPS.
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.character_sprites = pygame.sprite.Group()
        self.transition_sprites = pygame.sprite.Group()
        # ASSETS.
        self.import_assets()
        self.setup(self.tmx_map["world"], "house")
        # DIALOG.
        self.dialog_tree = None
        self.monster_index = MonsterIndex(
            self.player_monsters, self.fonts, self.monster_frames
        )
        # TRASITION.
        self.transition_target = None
        self.tint_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.tint_mode = "untint"
        self.tint_speed = 600
        self.tint_progress = 0
        # BATTLE.
        self.battle = Battle(
            self.player_monsters,
            self.dummy_monsters,
            self.monster_frames,
            self.bg_frames["forest"],
            self.fonts,
        )

    def import_assets(self):
        self.tmx_map = import_maps("data", "maps")

        self.overworld_frames = {
            "water": import_folder_list("meta", "tilesets", "water"),
            "coast": import_coast(24, 12, "meta", "tilesets", "coast"),
            "characters": import_characters("meta", "characters"),
        }

        self.monster_frames = {
            "icons": import_folder_dict("meta", "icons"),
            "monsters": import_monsters(4, 2, "meta", "monsters"),
            "ui": import_folder_dict("meta", "ui"),
        }

        self.fonts = {
            "dialog": pygame.font.Font(join("meta", "fonts", "PixeloidSans.ttf"), 30),
            "regular": pygame.font.Font(join("meta", "fonts", "PixeloidSans.ttf"), 18),
            "small": pygame.font.Font(join("meta", "fonts", "PixeloidSans.ttf"), 14),
            "bold": pygame.font.Font(join("meta", "fonts", "dogicapixelbold.otf"), 20),
        }

        self.bg_frames = import_folder_dict("meta", "backgrounds")

    def setup(self, tmx_map, player_start_pos):
        # CLEAR THE MAP.
        for group in (
            self.all_sprites,
            self.collision_sprites,
            self.character_sprites,
            self.transition_sprites,
        ):
            group.empty()
        # TERRAINS.
        for layer in ["Terrain", "Terrain Top"]:
            for x, y, surf in tmx_map.get_layer_by_name(layer).tiles():
                Sprite(
                    pos=(x * TILE_SIZE, y * TILE_SIZE),
                    surf=surf,
                    groups=self.all_sprites,
                    z=WORLD_LAYERS["bg"],
                )
        # WATER.
        for obj in tmx_map.get_layer_by_name("Water"):
            for x in range(int(obj.x), int(obj.x + obj.width), TILE_SIZE):
                for y in range(int(obj.y), int(obj.y + obj.height), TILE_SIZE):
                    AnimatedSprite(
                        pos=(x, y),
                        frames=self.overworld_frames["water"],
                        groups=self.all_sprites,
                        z=WORLD_LAYERS["water"],
                    )
        # COAST.
        for obj in tmx_map.get_layer_by_name("Coast"):
            terrain, side = obj.properties["terrain"], obj.properties["side"]
            AnimatedSprite(
                pos=(obj.x, obj.y),
                frames=self.overworld_frames["coast"][terrain][side],
                groups=self.all_sprites,
                z=WORLD_LAYERS["bg"],
            )
        # OBJECTS.
        for obj in tmx_map.get_layer_by_name("Objects"):
            if obj.name == "top":
                Sprite(
                    pos=(obj.x, obj.y),
                    surf=obj.image,
                    groups=self.all_sprites,
                    z=WORLD_LAYERS["top"],
                )
            else:
                ColliableSprite(
                    pos=(obj.x, obj.y),
                    surf=obj.image,
                    groups=(self.all_sprites, self.collision_sprites),
                )
        # TRASISTION OBJECTS.
        for obj in tmx_map.get_layer_by_name("Transition"):
            TransitionSprite(
                pos=(obj.x, obj.y),
                size=(obj.width, obj.height),
                target=(obj.properties["target"], obj.properties["pos"]),
                groups=self.transition_sprites,
            )
        # COLLISION OBJECTS.
        for obj in tmx_map.get_layer_by_name("Collisions"):
            BorderSprite(
                pos=(obj.x, obj.y),
                surf=pygame.Surface((obj.width, obj.height)),
                groups=self.collision_sprites,
            )
        # GRASS PATCHES.
        for obj in tmx_map.get_layer_by_name("Monsters"):
            MonsterPatchSprite(
                pos=(obj.x, obj.y),
                surf=obj.image,
                groups=self.all_sprites,
                biome=obj.properties["biome"],
            )
        # ENTITIES.
        for obj in tmx_map.get_layer_by_name("Entities"):
            frames = self.overworld_frames["characters"]

            if obj.name == "Player":
                if obj.properties["pos"] == player_start_pos:
                    self.player = Player(
                        pos=(obj.x, obj.y),
                        facing_direction=obj.direction,
                        frames=frames["player"],
                        groups=self.all_sprites,
                        collision_sprites=self.collision_sprites,
                    )
            else:
                Character(
                    pos=(obj.x, obj.y),
                    facing_direction=obj.direction,
                    frames=frames[obj.properties["graphic"]],
                    groups=(
                        self.all_sprites,
                        self.collision_sprites,
                        self.character_sprites,
                    ),
                    character_data=TRAINER_DATA[obj.properties["character_id"]],
                    player=self.player,
                    create_dialog=self.create_dialog,
                    collision_sprites=self.collision_sprites,
                    radius=obj.properties["radius"],
                )

    def input(self):
        keys = pygame.key.get_just_pressed()
        if not self.dialog_tree and not self.battle:
            # CHARACTER DIALOG INPUT.
            if keys[pygame.K_SPACE]:
                for character in self.character_sprites:
                    if check_connections(200, self.player, character):
                        # BLOCK THE PLAYER.
                        self.player.block()
                        # FACING TOGETHER.
                        character.change_facing_direction(self.player.rect.center)
                        # START DIALOG.
                        self.create_dialog(character)
                        # BLOCK THE CHARACTER ROTATION.
                        character.can_rotate = False
            # MONSTER INDEX INPUT.
            if keys[pygame.K_RETURN]:
                self.index_show = not self.index_show
                self.player.blocked = not self.player.blocked

    # DIALOG SYSTEM.
    def create_dialog(self, character):
        if not self.dialog_tree:
            self.dialog_tree = DialogTree(
                character=character,
                player=self.player,
                all_sprites=self.all_sprites,
                font=self.fonts["dialog"],
                end_dialog=self.end_dialog,
            )

    def end_dialog(self, character):
        self.dialog_tree = None
        self.player.unblock()

    # TRANSITION SYSTEM.
    def transition_check(self):
        sprites = [
            sprite
            for sprite in self.transition_sprites
            if sprite.rect.colliderect(self.player.hitbox)
        ]
        if sprites:
            self.player.block()
            self.transition_target = sprites[0].target
            self.tint_mode = "tint"

    def tint_screen(self, dt):
        if self.tint_mode == "tint":
            self.tint_progress += self.tint_speed * dt
            if self.tint_progress >= 255:
                self.setup(
                    tmx_map=self.tmx_map[self.transition_target[0]],
                    player_start_pos=self.transition_target[1],
                )
                self.tint_mode = "untint"
                self.transition_target = None
        else:
            self.tint_progress -= self.tint_speed * dt

        self.tint_progress = max(0, min(255, self.tint_progress))
        self.tint_surf.set_alpha(self.tint_progress)
        self.screen.blit(self.tint_surf, (0, 0))

    def run(self):
        while True:
            dt = self.clock.tick() / 1000
            # EVENT LOOP.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
            # GAME LOGIC.
            self.input()
            self.transition_check()
            self.screen.fill("black")
            self.all_sprites.update(dt)
            self.all_sprites.draw(self.player)
            # OVERLAYS.
            if self.dialog_tree:
                self.dialog_tree.update()
            if self.index_show:
                self.monster_index.update(dt)
            if self.battle:
                self.battle.update(dt)
            self.tint_screen(dt)
            pygame.display.update()


if __name__ == "__main__":
    Game().run()
