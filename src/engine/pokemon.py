from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class MoveCategory(Enum):
    PHYSICAL = "physical"
    SPECIAL = "special"
    STATUS = "status"


class Status(Enum):
    NONE = "none"
    BURN = "burn"
    FREEZE = "freeze"
    PARALYSIS = "paralysis"
    POISON = "poison"
    BAD_POISON = "bad_poison"
    SLEEP = "sleep"


@dataclass
class Move:
    name: str
    type: str
    category: MoveCategory
    power: int
    accuracy: int
    pp: int
    priority: int
    effect: str | None
    current_pp: int = -1

    def __post_init__(self):
        if self.current_pp == -1:
            self.current_pp = self.pp


STAT_STAGE_MULTIPLIERS = {
    -6: 2/8, -5: 2/7, -4: 2/6, -3: 2/5, -2: 2/4, -1: 2/3,
    0: 1.0,
    1: 3/2, 2: 4/2, 3: 5/2, 4: 6/2, 5: 7/2, 6: 8/2,
}


def _iv_from_scale(iv_scale: int) -> int:
    """Map the decompilation's iv_scale (0-255) to IV (0-31)."""
    import math
    return math.ceil(iv_scale * 31 / 255)


def _calc_hp(base: int, iv: int, level: int) -> int:
    """Gen 4 HP stat formula."""
    return (2 * base + iv) * level // 100 + level + 10


def _calc_stat(base: int, iv: int, level: int) -> int:
    """Gen 4 other stat formula (neutral nature, 0 EVs)."""
    return (2 * base + iv) * level // 100 + 5


@dataclass
class Pokemon:
    name: str
    types: list[str]
    level: int
    base_stats: dict[str, int]
    moves: list[Move]
    ability: str
    item: str | None
    iv_scale: int = 250
    current_hp: int = -1
    status: Status = Status.NONE
    status_turns: int = 0
    stat_stages: dict[str, int] = field(default_factory=dict)
    volatile: set[str] = field(default_factory=set)
    stats: dict[str, int] = field(default_factory=dict)
    max_hp: int = 0

    def __post_init__(self):
        iv = _iv_from_scale(self.iv_scale)
        self.max_hp = _calc_hp(self.base_stats["hp"], iv, self.level)
        self.stats = {
            "attack": _calc_stat(self.base_stats["attack"], iv, self.level),
            "defense": _calc_stat(self.base_stats["defense"], iv, self.level),
            "sp_attack": _calc_stat(self.base_stats["sp_attack"], iv, self.level),
            "sp_defense": _calc_stat(self.base_stats["sp_defense"], iv, self.level),
            "speed": _calc_stat(self.base_stats["speed"], iv, self.level),
        }
        if self.current_hp == -1:
            self.current_hp = self.max_hp
        if not self.stat_stages:
            self.stat_stages = {
                "attack": 0, "defense": 0, "sp_attack": 0,
                "sp_defense": 0, "speed": 0,
            }

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

    def take_damage(self, amount: int) -> int:
        actual = min(amount, self.current_hp)
        self.current_hp = max(0, self.current_hp - amount)
        return actual

    def heal(self, amount: int) -> int:
        before = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - before

    def modify_stat_stage(self, stat: str, stages: int) -> int:
        old = self.stat_stages[stat]
        self.stat_stages[stat] = max(-6, min(6, old + stages))
        return self.stat_stages[stat] - old

    def get_effective_stat(self, stat: str) -> int:
        base_val = self.stats[stat]
        multiplier = STAT_STAGE_MULTIPLIERS[self.stat_stages[stat]]
        return int(base_val * multiplier)

    def reset_stat_stages(self):
        for stat in self.stat_stages:
            self.stat_stages[stat] = 0

    def _replace_moves(self, moves: list[Move]) -> Pokemon:
        """Return self with replaced moves (used by API client)."""
        self.moves = moves
        return self
