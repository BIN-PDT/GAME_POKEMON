from game_data import MONSTER_DATA, ATTACK_DATA
from random import randint


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
        # EXPERIENCE.
        self.xp = randint(0, 1000)
        self.level_up = self.level * 150

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
            (self.energy, self.get_stat("max_health")),
            (self.initiative, 100),
        )

    def update(self, dt):
        if not self.is_paused:
            self.initiative += self.get_stat("speed") * dt
