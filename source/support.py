from settings import *
from os import walk
from os.path import join


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
