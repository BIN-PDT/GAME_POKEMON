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
        self.z = WORLD_LAYERS["main"]
        self.y_sort = self.rect.centery
        # COLLISION.
        self.hitbox = self.rect.inflate(-self.rect.width / 2, -60)

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
    def __init__(self, pos, facing_direction, frames, groups, collision_sprites):
        super().__init__(pos, facing_direction, frames, groups)
        # COLLISION.
        self.collision_sprites = collision_sprites

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
        self.direction = input_vector.normalize() if input_vector else input_vector

    def move(self, dt):
        self.rect.centerx += self.direction.x * self.speed * dt
        self.hitbox.centerx = self.rect.centerx
        self.collide("horizontal")
        self.rect.centery += self.direction.y * self.speed * dt
        self.hitbox.centery = self.rect.centery
        self.collide("vertical")

    def collide(self, axis):
        for sprite in self.collision_sprites:
            if sprite.hitbox.colliderect(self.hitbox):
                if axis == "horizontal":
                    if self.direction.x > 0:
                        self.hitbox.right = sprite.hitbox.left
                    else:
                        self.hitbox.left = sprite.hitbox.right
                    self.rect.centerx = self.hitbox.centerx
                else:
                    if self.direction.y > 0:
                        self.hitbox.bottom = sprite.hitbox.top
                    else:
                        self.hitbox.top = sprite.hitbox.bottom
                    self.rect.centery = self.hitbox.centery

    def update(self, dt):
        self.y_sort = self.rect.centery
        self.input()
        self.move(dt)
        self.animate(dt)
