from settings import *
from timers import Timer


class DialogTree:
    def __init__(self, character, player, all_sprites, font, end_dialog):
        self.character, self.player = character, player
        self.all_sprites, self.font = all_sprites, font
        self.end_dialog = end_dialog

        self.dialog = self.character.get_dialog()
        self.dialog_index, self.dialog_length = 0, len(self.dialog)
        self.current_dialog = DialogSprite(
            message=self.dialog[self.dialog_index],
            character=self.character,
            groups=self.all_sprites,
            font=self.font,
        )
        self.dialog_timer = Timer(500, autostart=True)

    def input(self):
        keys = pygame.key.get_just_pressed()
        if keys[pygame.K_SPACE] and not self.dialog_timer.is_active:
            self.current_dialog.kill()
            self.dialog_index += 1
            if self.dialog_index < self.dialog_length:
                self.current_dialog = DialogSprite(
                    message=self.dialog[self.dialog_index],
                    character=self.character,
                    groups=self.all_sprites,
                    font=self.font,
                )
                self.dialog_timer.activate()
            else:
                self.end_dialog(self.character)

    def update(self):
        self.dialog_timer.update()
        self.input()


class DialogSprite(pygame.sprite.Sprite):
    def __init__(self, message, character, groups, font):
        super().__init__(groups)
        self.z = WORLD_LAYERS["top"]
        # TEXT SURFACE.
        text_surf = font.render(message, False, COLORS["black"])
        padding = 10
        width = max(50, text_surf.get_width() + 2 * padding)
        height = text_surf.get_height() + 2 * padding
        # BACKGROUND SURFACE.
        bg_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 0))
        pygame.draw.rect(
            bg_surf, COLORS["pure white"], bg_surf.get_frect(topleft=(0, 0)), 0, 4
        )
        bg_surf.blit(text_surf, text_surf.get_frect(center=(width / 2, height / 2)))
        # TEXT DISPLAY.
        self.image = bg_surf
        self.rect = self.image.get_frect(
            midbottom=character.rect.midtop + Vector(0, -10)
        )
