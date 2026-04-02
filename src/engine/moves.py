from __future__ import annotations
import random
from src.engine.pokemon import Pokemon, Status


def apply_status(target: Pokemon, status: Status) -> bool:
    """Try to apply a primary status condition. Returns False if already statused."""
    if target.status != Status.NONE:
        return False
    target.status = status
    if status == Status.SLEEP:
        target.status_turns = random.randint(1, 3)
    elif status == Status.BAD_POISON:
        target.status_turns = 0
    return True


def apply_end_of_turn(pokemon: Pokemon) -> int:
    """Apply end-of-turn effects. Returns HP lost."""
    if not pokemon.is_alive:
        return 0
    damage = 0
    if pokemon.status == Status.BURN:
        damage = pokemon.max_hp // 8
    elif pokemon.status == Status.POISON:
        damage = pokemon.max_hp // 8
    elif pokemon.status == Status.BAD_POISON:
        pokemon.status_turns += 1
        damage = (pokemon.max_hp * pokemon.status_turns) // 16
    if damage > 0:
        pokemon.take_damage(damage)
    return damage


def can_act(pokemon: Pokemon) -> bool:
    """Check if a pokemon can act this turn (sleep, paralysis, freeze checks)."""
    if pokemon.status == Status.SLEEP:
        if pokemon.status_turns <= 0:
            pokemon.status = Status.NONE
            return True
        pokemon.status_turns -= 1
        return False
    if pokemon.status == Status.FREEZE:
        if random.randint(1, 5) == 1:
            pokemon.status = Status.NONE
            return True
        return False
    if pokemon.status == Status.PARALYSIS:
        if random.randint(1, 4) == 1:
            return False
    if "confusion" in pokemon.volatile:
        if random.randint(1, 2) == 1:
            return False
    return True


def get_effective_speed(pokemon: Pokemon) -> int:
    """Get speed accounting for paralysis."""
    speed = pokemon.get_effective_stat("speed")
    if pokemon.status == Status.PARALYSIS:
        speed = speed // 4
    return speed
