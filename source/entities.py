from random import choice

from settings import *
from support import check_connections
from timers import Timer
from monster import Monster


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
        # DIALOG.
        self.blocked = False

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

    def block(self):
        self.blocked = True
        self.direction = Vector()

    def unblock(self):
        self.blocked = False

    def change_facing_direction(self, target_pos):
        relation = Vector(target_pos) - Vector(self.rect.center)
        if abs(relation.y) < 30:
            self.facing_direction = "right" if relation.x > 0 else "left"
        else:
            self.facing_direction = "down" if relation.y > 0 else "up"


class Character(Entity):
    def __init__(
        self,
        pos,
        facing_direction,
        frames,
        groups,
        character_data,
        player,
        create_dialog,
        collision_sprites,
        radius,
        is_nurse,
        notice_sound,
    ):
        super().__init__(pos, facing_direction, frames, groups)
        # CHARACTER DATA.
        self.character_data = character_data
        self.player = player
        self.is_nurse = is_nurse
        self.monsters = (
            {
                i: Monster(name, level)
                for i, (name, level) in self.character_data["monsters"].items()
            }
            if self.character_data.get("monsters")
            else None
        )
        # DIALOG.
        self.create_dialog = create_dialog
        self.collision_rects = [
            sprite.rect for sprite in collision_sprites if sprite is not self
        ]
        # MOVEMENT.
        self.has_moved = False
        self.can_rotate = True
        self.has_noticed = False
        self.radius = int(radius)
        # LOOK AROUND.
        self.view_directions = self.character_data["directions"]

        self.timers = {
            "look around": Timer(1500, True, True, self.random_view_direction),
            "notice": Timer(500, command=self.start_move),
        }
        # SOUND.
        self.notice_sound = notice_sound

    def get_dialog(self):
        return self.character_data["dialog"][
            "defeated" if self.character_data["defeated"] else "default"
        ]

    def raycast(self):
        if not self.has_moved and not self.has_noticed:
            if check_connections(self.radius, self, self.player) and self.has_los():
                # BLOCK THE PLAYER.
                self.player.block()
                # CHANGE PLAYER'S FACING DIRECTION.
                self.player.change_facing_direction(self.rect.center)
                # MOVE TO THE PLAYER.
                self.timers["notice"].activate()
                # CHARACTER DON'T ROTATE ITSELF & NOTICE THE PLAYER.
                self.can_rotate = False
                self.has_noticed = True
                # PLAYER WAS NOTICED.
                self.player.is_noticed = True
                self.notice_sound.play()

    def has_los(self):
        src_pos, des_pos = self.rect.center, self.player.rect.center
        if Vector(src_pos).distance_to(Vector(des_pos)) < self.radius:
            collisions = [
                bool(rect.clipline(src_pos, des_pos)) for rect in self.collision_rects
            ]
        return not any(collisions)

    def start_move(self):
        relation = (
            Vector(self.player.rect.center) - Vector(self.rect.center)
        ).normalize()
        self.direction = Vector(round(relation.x), round(relation.y))

    def move(self, dt):
        if not self.has_moved and self.direction:
            if not self.hitbox.inflate(10, 10).colliderect(self.player.hitbox):
                self.rect.center += self.direction * self.speed * dt
                self.hitbox.center = self.rect.center
            else:
                # STOP MOVING.
                self.has_moved = True
                self.direction = Vector()
                # START DIALOG.
                self.create_dialog(self)
                # STOP NOTICING.
                self.player.is_noticed = False

    def random_view_direction(self):
        if self.can_rotate:
            self.facing_direction = choice(self.view_directions)

    def update(self, dt):
        for timer in self.timers.values():
            timer.update()
        self.animate(dt)
        if self.character_data["look_around"]:
            self.raycast()
            self.move(dt)


class Player(Entity):
    def __init__(self, pos, facing_direction, frames, groups, collision_sprites):
        super().__init__(pos, facing_direction, frames, groups)
        # COLLISION.
        self.collision_sprites = collision_sprites
        # DIALOG.
        self.is_noticed = False

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
        if not self.blocked:
            self.input()
            self.move(dt)
        self.animate(dt)
