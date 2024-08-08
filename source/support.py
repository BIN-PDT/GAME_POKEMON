from settings import *
from os import walk
from os.path import join
from pytmx.util_pygame import load_pygame


def import_image(*path, alpha=True, format="png"):
    full_path = f"{join(*path)}.{format}"
    surf = pygame.image.load(full_path)
    return surf.convert_alpha() if alpha else surf.convert()


def import_tiles(cols, rows, *path):
    frames = {}
    surf = import_image(*path)
    TILE_WIDTH, TILE_HEIGHT = surf.get_width() / cols, surf.get_height() / rows
    for col in range(cols):
        for row in range(rows):
            left, top = col * TILE_WIDTH, row * TILE_HEIGHT
            cutout_rect = pygame.Rect(left, top, TILE_WIDTH, TILE_HEIGHT)
            cutout_surf = pygame.Surface((TILE_WIDTH, TILE_HEIGHT))
            cutout_surf.fill("green")
            cutout_surf.set_colorkey("green")
            cutout_surf.blit(surf, (0, 0), cutout_rect)

            frames[(col, row)] = cutout_surf
    return frames


def import_coast(cols, rows, *path):
    tiles = import_tiles(cols, rows, *path)
    frames = {}
    terrains = ["grass", "grass_i", "sand_i", "sand", "rock", "rock_i", "ice", "ice_i"]
    sides = {
        "topleft": (0, 0),
        "top": (1, 0),
        "topright": (2, 0),
        "left": (0, 1),
        "right": (2, 1),
        "bottomleft": (0, 2),
        "bottom": (1, 2),
        "bottomright": (2, 2),
    }

    for index, terrain in enumerate(terrains):
        frames[terrain] = {}
        for key, pos in sides.items():
            frames[terrain][key] = [
                tiles[(pos[0] + index * 3, pos[1] + row)] for row in range(0, rows, 3)
            ]
    return frames


def import_folder_list(*path):
    frames = []
    for folder_path, _, file_names in walk(join(*path)):
        for file_name in sorted(file_names, key=lambda name: int(name.split(".")[0])):
            full_path = join(folder_path, file_name)
            surf = pygame.image.load(full_path).convert_alpha()
            frames.append(surf)
    return frames


def import_folder_dict(*path, subordinate=False):
    frames = {}
    for folder_path, sub_folders, file_names in walk(join(*path)):
        if subordinate:
            for sub_folder in sub_folders:
                frames[sub_folder] = import_folder_list()
        else:
            for file_name in file_names:
                full_path = join(folder_path, file_name)
                surf = pygame.image.load(full_path).convert_alpha()
                frames[file_name.split(".")[0]] = surf
    return frames


def import_character(cols, rows, *path):
    tiles = import_tiles(cols, rows, *path)
    frames = {}
    directions = ["down", "left", "right", "up"]

    for index, direction in enumerate(directions):
        frames[direction] = [tiles[(col, index)] for col in range(cols)]
        frames[f"{direction}_idle"] = [tiles[0, index]]
    return frames


def import_characters(*path):
    frames = {}
    for _, _, file_names in walk(join(*path)):
        for file_name in file_names:
            name = file_name.split(".")[0]
            frames[name] = import_character(4, 4, *path, name)
    return frames


def import_maps(*path):
    tmx_maps = {}
    for folder_path, _, file_names in walk(join(*path)):
        for file_name in file_names:
            tmx_maps[file_name.split(".")[0]] = load_pygame(
                join(folder_path, file_name)
            )
    return tmx_maps


def import_monsters(cols, rows, *path):
    frames = {}
    for _, _, file_names in walk(join(*path)):
        for file_name in file_names:
            name = file_name.split(".")[0]
            frames[name] = {}

            tiles = import_tiles(cols, rows, *path, name)
            for index, key in enumerate(("idle", "attack")):
                frames[name][key] = [tiles[(col, index)] for col in range(cols)]
    return frames


def outline_frames(frames, outline_width):
    outlined_frames = {}
    for name, monster_frames in frames.items():
        outlined_frames[name] = {}
        for state, frames in monster_frames.items():
            outlined_frames[name][state] = []
            for frame in frames:
                new_size = Vector(frame.get_size()) + Vector(outline_width * 2)
                new_surf = pygame.Surface(new_size, pygame.SRCALPHA)
                new_surf.fill((0, 0, 0, 0))
                mask_surf = pygame.mask.from_surface(frame).to_surface()
                mask_surf.set_colorkey("black")

                new_surf.blit(mask_surf, (0, 0))  # TL.
                new_surf.blit(mask_surf, (outline_width, 0))  # T.
                new_surf.blit(mask_surf, (outline_width * 2, 0))  # TR.
                new_surf.blit(mask_surf, (outline_width * 2, outline_width))  # R.
                new_surf.blit(mask_surf, (outline_width * 2, outline_width * 2))  # BR.
                new_surf.blit(mask_surf, (outline_width, outline_width * 2))  # B.
                new_surf.blit(mask_surf, (0, outline_width * 2))  # BL.
                new_surf.blit(mask_surf, (0, outline_width))  # L.

                outlined_frames[name][state].append(new_surf)
    return outlined_frames


def check_connections(radius, entity, target, tolerance=30):
    relation = Vector(target.rect.center) - Vector(entity.rect.center)
    if relation.length() < radius:
        if (
            abs(relation.y) < tolerance
            and (
                entity.facing_direction == "left"
                and relation.x < 0
                or entity.facing_direction == "right"
                and relation.x > 0
            )
        ) or (
            abs(relation.x) < tolerance
            and (
                entity.facing_direction == "up"
                and relation.y < 0
                or entity.facing_direction == "down"
                and relation.y > 0
            )
        ):
            return True


def draw_bar(surface, frame, current, maximum, fg_color, bg_color, radius=1):
    # CALCULATE RATIO.
    ratio = frame.width / maximum
    progress = max(0, min(frame.width, current * ratio))
    # BACKGROUND (TOTAL) & FOREGROUD (CURRENT).
    bg_rect = frame.copy()
    fg_rect = pygame.FRect(frame.topleft, (progress, frame.height))
    # DISPLAY.
    pygame.draw.rect(surface, bg_color, bg_rect, 0, radius)
    pygame.draw.rect(surface, fg_color, fg_rect, 0, radius)
