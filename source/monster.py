from game_data import MONSTER_DATA, ATTACK_DATA


class Monster:
    def __init__(self, name, level):
        self.name, self.level = name, level
        # STATS.
        self.element = MONSTER_DATA[self.name]["stats"]["element"]
        self.abilities = MONSTER_DATA[self.name]["abilities"]
        self.base_stats = MONSTER_DATA[self.name]["stats"]
        self.health = self.base_stats["max_health"] * self.level
        self.energy = self.base_stats["max_energy"] * self.level
        self.initiative = 0
        self.is_paused = False
        self.is_defending = False
        # EXPERIENCE.
        self.xp = 0
        self.level_up = self.level * 150
        self.evolution = MONSTER_DATA[self.name]["evolve"]

    def get_stat(self, stat):
        return self.base_stats[stat] * self.level

    def get_stats(self):
        return {
            "health": self.get_stat("max_health"),
            "energy": self.get_stat("max_energy"),
            "attack": self.get_stat("attack"),
            "defense": self.get_stat("defense"),
            "speed": self.get_stat("speed"),
            "recovery": self.get_stat("recovery"),
        }

    def get_abilities(self, all=True):
        if all:
            return [
                ability
                for level, ability in self.abilities.items()
                if self.level >= level
            ]
        else:
            return [
                ability
                for level, ability in self.abilities.items()
                if self.level >= level and self.energy >= ATTACK_DATA[ability]["cost"]
            ]

    def get_info(self):
        return (
            (self.health, self.get_stat("max_health")),
            (self.energy, self.get_stat("max_energy")),
            (self.initiative, 100),
        )

    def reduce_energy(self, attack):
        self.energy -= ATTACK_DATA[attack]["cost"]

    def get_base_damage(self, attack):
        return self.get_stat("attack") * ATTACK_DATA[attack]["amount"]

    def update_xp(self, amount):
        self.xp += amount
        if self.xp >= self.level_up:
            self.level += 1
            self.xp -= self.level_up
            self.level_up = self.level * 150

    def limit_stats(self):
        self.health = max(0, min(self.health, self.get_stat("max_health")))
        self.energy = max(0, min(self.energy, self.get_stat("max_energy")))

    def get_recovery(self):
        recovery_amount = self.get_stat("recovery")
        self.health += recovery_amount * 0.25
        self.energy += recovery_amount * 0.75

    def is_energetic(self):
        return (
            self.health >= self.get_stat("max_health") * 0.5
            and self.energy >= self.get_stat("max_energy") * 0.8
        )

    def update(self, dt):
        self.limit_stats()
        if not self.is_paused:
            self.initiative += self.get_stat("speed") * dt
