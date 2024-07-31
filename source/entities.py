from settings import *


class Entity(pygame.sprite.Sprite):
    def __init__(self, pos, facing_direction, frames, groups):
        super().__init__(groups)
        # MOVEMENT.
        self.direction, self.speed = Vector(), 250
        self.facing_direction = facing_direction
        # GRAPHIC.
        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.get_state()][self.frame_index]
        self.rect = self.image.get_frect(center=pos)

    def animate(self, dt):
        frames = self.frames[self.get_state()]
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index > len(frames):
            self.frame_index = 0

        self.image = frames[int(self.frame_index)]

    def get_state(self):
        is_moving = bool(self.direction)
        if is_moving:
            if self.direction.x != 0:
                self.facing_direction = "left" if self.direction.x < 0 else "right"
            if self.direction.y != 0:
                self.facing_direction = "up" if self.direction.y < 0 else "down"
        return f"{self.facing_direction}{'' if is_moving else '_idle'}"


class Character(Entity):
    def __init__(self, pos, facing_direction, frames, groups):
        super().__init__(pos, facing_direction, frames, groups)


class Player(Entity):
    def __init__(self, pos, facing_direction, frames, groups):
        super().__init__(pos, facing_direction, frames, groups)

    def input(self):
        keys = pygame.key.get_pressed()
        input_vector = Vector()
        if keys[pygame.K_UP]:
            input_vector.y -= 1
        if keys[pygame.K_DOWN]:
            input_vector.y += 1
        if keys[pygame.K_LEFT]:
            input_vector.x -= 1
        if keys[pygame.K_RIGHT]:
            input_vector.x += 1
        self.direction = input_vector

    def move(self, dt):
        self.rect.center += self.direction * self.speed * dt

    def update(self, dt):
        self.input()
        self.move(dt)
        self.animate(dt)
