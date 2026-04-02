from __future__ import annotations
import random
from dataclasses import dataclass
from src.engine.pokemon import Pokemon, Move, MoveCategory, Status
from src.engine.typechart import get_matchup


@dataclass
class DamageResult:
    damage: int
    effectiveness: float
    stab: bool
    critical: bool


def calculate_damage(
    attacker: Pokemon,
    defender: Pokemon,
    move: Move,
    critical: bool | None = None,
    roll: int | None = None,
) -> DamageResult:
    """Gen 4 damage formula. Set critical/roll to override RNG for testing."""
    if move.category == MoveCategory.STATUS or move.power == 0:
        effectiveness = get_matchup(move.type, defender.types)
        return DamageResult(damage=0, effectiveness=effectiveness, stab=False, critical=False)

    effectiveness = get_matchup(move.type, defender.types)
    if effectiveness == 0.0:
        return DamageResult(damage=0, effectiveness=0.0, stab=False, critical=False)

    # Pick attack/defense stats based on category
    if move.category == MoveCategory.PHYSICAL:
        atk = attacker.get_effective_stat("attack")
        dfn = defender.get_effective_stat("defense")
        # Burn halves physical attack
        if attacker.status == Status.BURN:
            atk = atk // 2
    else:
        atk = attacker.get_effective_stat("sp_attack")
        dfn = defender.get_effective_stat("sp_defense")

    # Critical hit: 1/16 chance, 2x damage
    if critical is None:
        critical = random.randint(1, 16) == 1
    crit_mod = 2.0 if critical else 1.0

    # STAB
    stab = move.type in attacker.types
    stab_mod = 1.5 if stab else 1.0

    # Random roll 85-100
    if roll is None:
        roll = random.randint(85, 100)

    # Gen 4 formula
    level_factor = (2 * attacker.level / 5 + 2)
    base_damage = int(level_factor * move.power * atk / dfn) // 50 + 2
    damage = base_damage
    damage = int(damage * crit_mod)
    damage = int(damage * stab_mod)
    damage = int(damage * effectiveness)
    damage = int(damage * roll / 100)
    damage = max(1, damage)  # minimum 1 damage if not immune

    return DamageResult(
        damage=damage,
        effectiveness=effectiveness,
        stab=stab,
        critical=critical,
    )
