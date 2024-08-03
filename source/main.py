from settings import *
from game_data import *
from os.path import join
from pytmx.util_pygame import load_pygame

from sprites import (
    Sprite,
    AnimatedSprite,
    BorderSprite,
    ColliableSprite,
    MonsterPatchSprite,
)
from entities import Character, Player
from groups import AllSprites
from dialog import DialogTree
from support import *


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Pokemon Hunter")
        self.clock = pygame.time.Clock()
        # GROUPS.
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.character_sprites = pygame.sprite.Group()

        self.import_assets()
        self.setup(self.tmx_map["world"], "house")

        self.dialog_tree = None

    def import_assets(self):
        self.tmx_map = {
            "world": load_pygame(join("data", "maps", "world.tmx")),
            "hospital": load_pygame(join("data", "maps", "hospital.tmx")),
        }

        self.overworld_frames = {
            "water": import_folder_list("meta", "tilesets", "water"),
            "coast": import_coast(24, 12, "meta", "tilesets", "coast"),
            "characters": import_characters("meta", "characters"),
        }

        self.fonts = {
            "dialog": pygame.font.Font(join("meta", "fonts", "PixeloidSans.ttf"), 30)
        }

    def setup(self, tmx_map, player_start_pos):
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
        if not self.dialog_tree:
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
            self.screen.fill("black")
            self.all_sprites.update(dt)
            self.all_sprites.draw(self.player)
            # OVERLAYS.
            if self.dialog_tree:
                self.dialog_tree.update()
            pygame.display.update()


if __name__ == "__main__":
    Game().run()
