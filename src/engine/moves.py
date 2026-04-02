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
    """Check if a pokemon can act this turn (flinch, sleep, paralysis, freeze checks)."""
    if "flinch" in pokemon.volatile:
        pokemon.volatile.discard("flinch")
        return False
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


_AILMENT_TO_STATUS = {
    "burn": Status.BURN,
    "freeze": Status.FREEZE,
    "paralysis": Status.PARALYSIS,
    "poison": Status.POISON,
    "sleep": Status.SLEEP,
}

_STAT_DISPLAY = {
    "attack": "Attack", "defense": "Defense", "speed": "Speed",
    "sp_attack": "Sp. Atk", "sp_defense": "Sp. Def",
}


def _effect_fires(chance: int, deterministic: bool) -> bool:
    """Check if a probabilistic effect triggers. Chance of 0 means guaranteed."""
    resolved = chance if chance > 0 else 100
    if resolved >= 100:
        return True
    if deterministic:
        return False
    return random.randint(1, 100) <= resolved


def apply_move_effects(
    attacker: Pokemon,
    target: Pokemon,
    move,
    damage_dealt: int,
    deterministic: bool = False,
) -> list[tuple[str, str]]:
    """Apply secondary effects after a move hits. Returns (event_type, message) pairs.

    When deterministic=True (for AI lookahead), only guaranteed effects are applied.
    """
    out: list[tuple[str, str]] = []

    # --- Status ailment (only on living targets) ---
    if (target.is_alive and move.ailment != "none"
            and move.ailment in _AILMENT_TO_STATUS
            and _effect_fires(move.ailment_chance, deterministic)):
        # "toxic" specifically inflicts bad poison
        status = Status.BAD_POISON if move.name == "toxic" else _AILMENT_TO_STATUS[move.ailment]
        if apply_status(target, status):
            label = "badly poisoned" if status == Status.BAD_POISON else f"{status.value}ed"
            if status == Status.SLEEP:
                label = "fell asleep"
            elif status == Status.FREEZE:
                label = "was frozen solid"
            out.append(("status", f"{target.name} {label}!"))

    # --- Confusion (volatile, not a primary status) ---
    if (target.is_alive and move.ailment == "confusion"
            and _effect_fires(move.ailment_chance, deterministic)):
        target.volatile.add("confusion")
        out.append(("status", f"{target.name} became confused!"))

    # --- Stat changes ---
    if move.stat_changes and _effect_fires(move.stat_chance, deterministic):
        for stat, stages in move.stat_changes:
            # Determine who the stat change targets
            if move.stat_change_target == "target":
                who = target
            elif move.stat_change_target == "auto":
                who = attacker if stages > 0 else target
            else:
                who = attacker

            if stat not in who.stat_stages:
                continue
            if not who.is_alive:
                continue

            actual = who.modify_stat_stage(stat, stages)
            if actual != 0:
                display = _STAT_DISPLAY.get(stat, stat)
                if actual > 0:
                    out.append(("stat_change", f"{who.name}'s {display} rose!"))
                else:
                    out.append(("stat_change", f"{who.name}'s {display} fell!"))

    # --- Drain (positive = heal attacker, negative = recoil) ---
    if move.drain > 0 and damage_dealt > 0:
        heal_amount = max(1, damage_dealt * move.drain // 100)
        attacker.heal(heal_amount)
        out.append(("drain", f"{attacker.name} had its energy drained!"))
    elif move.drain < 0 and damage_dealt > 0:
        recoil = max(1, damage_dealt * abs(move.drain) // 100)
        attacker.take_damage(recoil)
        out.append(("recoil", f"{attacker.name} was hurt by recoil!"))

    # --- Self-healing (Recover, Roost, etc.) ---
    if move.healing > 0:
        heal_amount = max(1, attacker.max_hp * move.healing // 100)
        healed = attacker.heal(heal_amount)
        if healed > 0:
            out.append(("heal", f"{attacker.name} restored its HP!"))

    # --- Flinch ---
    if move.flinch_chance > 0 and target.is_alive:
        if not deterministic and random.randint(1, 100) <= move.flinch_chance:
            target.volatile.add("flinch")

    return out
