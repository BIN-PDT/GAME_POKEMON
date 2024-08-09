from settings import *
from timers import Timer


class Evolution:
    def __init__(
        self,
        monster_frames,
        start_monster,
        end_monster,
        font,
        end_evolution,
        star_frames,
    ):
        self.screen = pygame.display.get_surface()
        # IMAGE.
        self.start_monster_surf = pygame.transform.scale2x(
            monster_frames[start_monster]["idle"][0]
        )
        self.start_monster_rect = self.start_monster_surf.get_frect(
            center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        )
        self.end_monster_surf = pygame.transform.scale2x(
            monster_frames[end_monster]["idle"][0]
        )
        self.end_monster_rect = self.end_monster_surf.get_frect(
            center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        )
        # TEXT.
        self.start_text_surf = font.render(
            f"{start_monster} is evolving!", False, COLORS["black"]
        )
        self.start_text_rect = self.start_text_surf.get_frect(
            midtop=self.start_monster_rect.midbottom + Vector(0, 20)
        )
        self.end_text_surf = font.render(
            f"{start_monster} evolved into {end_monster}!", False, COLORS["black"]
        )
        self.end_text_rect = self.end_text_surf.get_frect(
            midtop=self.end_monster_rect.midbottom + Vector(0, 20)
        )
        # STAR ANIMATION.
        self.star_frames = [pygame.transform.scale2x(frame) for frame in star_frames]
        self.frame_index = 0
        # TIMERS.
        self.timers = {
            "start": Timer(1000, autostart=True),
            "end": Timer(2000, command=end_evolution),
        }
        # TRASITION.
        self.tint_surf = pygame.Surface(self.screen.get_size())
        self.tint_surf.set_alpha(200)
        self.progress, self.tint_speed = 0, 80

        self.start_monster_mask = pygame.mask.from_surface(
            self.start_monster_surf
        ).to_surface()
        self.start_monster_mask.set_colorkey("black")
        self.start_monster_mask.set_alpha(self.progress)

    def display_star_animation(self, dt):
        self.frame_index += 20 * dt
        if self.frame_index <= len(self.star_frames):
            surf = self.star_frames[int(self.frame_index)]
            rect = surf.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
            self.screen.blit(surf, rect)

    def update(self, dt):
        for timer in self.timers.values():
            timer.update()
        if not self.timers["start"].is_active:
            self.screen.blit(self.tint_surf, (0, 0))
            self.progress += self.tint_speed * dt
            if self.progress < 255:
                self.screen.blit(self.start_monster_surf, self.start_monster_rect)
                self.start_monster_mask.set_alpha(self.progress)
                self.screen.blit(self.start_monster_mask, self.start_monster_rect)

                pygame.draw.rect(
                    surface=self.screen,
                    color=COLORS["white"],
                    rect=self.start_text_rect.inflate(20, 20),
                    width=0,
                    border_radius=5,
                )
                self.screen.blit(self.start_text_surf, self.start_text_rect)
            else:
                self.screen.blit(self.end_monster_surf, self.end_monster_rect)
                if not self.timers["end"].is_active:
                    self.timers["end"].activate()

                pygame.draw.rect(
                    surface=self.screen,
                    color=COLORS["white"],
                    rect=self.end_text_rect.inflate(20, 20),
                    width=0,
                    border_radius=5,
                )
                self.screen.blit(self.end_text_surf, self.end_text_rect)
                self.display_star_animation(dt)
