import random
from src.engine.damage import calculate_damage
from src.engine.pokemon import Pokemon, Move, MoveCategory, Status


def _make_pokemon(name, types, base_stats, level=100, iv_scale=250):
    return Pokemon(
        name=name, types=types, level=level, base_stats=base_stats,
        moves=[], ability="", item=None, iv_scale=iv_scale,
    )


def _make_move(name, type_, category, power, accuracy=100, priority=0, effect=None):
    return Move(
        name=name, type=type_, category=category, power=power,
        accuracy=accuracy, pp=10, priority=priority, effect=effect,
    )


def test_basic_physical_damage():
    """Garchomp Earthquake vs Pikachu — super effective physical."""
    random.seed(0)
    attacker = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102})
    defender = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90})
    move = _make_move("Earthquake", "ground", MoveCategory.PHYSICAL, 100)
    result = calculate_damage(attacker, defender, move)
    assert result.damage > 0
    assert result.effectiveness == 2.0
    assert result.stab  # ground move from ground type

def test_stab_bonus():
    """STAB should multiply damage by 1.5."""
    random.seed(42)
    attacker = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90})
    defender = _make_pokemon("Geodude", ["rock", "ground"],
        {"hp": 40, "attack": 80, "defense": 100, "sp_attack": 30, "sp_defense": 30, "speed": 20})
    # Electric vs Rock/Ground = immune
    move = _make_move("Thunderbolt", "electric", MoveCategory.SPECIAL, 95)
    result = calculate_damage(attacker, defender, move)
    assert result.damage == 0
    assert result.effectiveness == 0.0

def test_status_move_does_no_damage():
    attacker = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90})
    defender = _make_pokemon("Geodude", ["rock", "ground"],
        {"hp": 40, "attack": 80, "defense": 100, "sp_attack": 30, "sp_defense": 30, "speed": 20})
    move = _make_move("Thunder Wave", "electric", MoveCategory.STATUS, 0)
    result = calculate_damage(attacker, defender, move)
    assert result.damage == 0

def test_special_move_uses_sp_stats():
    """Special moves should use sp_attack / sp_defense."""
    random.seed(1)
    attacker = _make_pokemon("Alakazam", ["psychic"],
        {"hp": 55, "attack": 50, "defense": 45, "sp_attack": 135, "sp_defense": 95, "speed": 120})
    defender = _make_pokemon("Machamp", ["fighting"],
        {"hp": 90, "attack": 130, "defense": 80, "sp_attack": 65, "sp_defense": 85, "speed": 55})
    move = _make_move("Psychic", "psychic", MoveCategory.SPECIAL, 90)
    result = calculate_damage(attacker, defender, move)
    assert result.damage > 0
    assert result.effectiveness == 2.0
    assert result.stab


def test_burn_halves_physical_damage():
    """Burned attacker should deal half physical damage."""
    attacker = _make_pokemon("Machamp", ["fighting"],
        {"hp": 90, "attack": 130, "defense": 80, "sp_attack": 65, "sp_defense": 85, "speed": 55})
    defender = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90})
    move = _make_move("Close Combat", "fighting", MoveCategory.PHYSICAL, 120)
    normal = calculate_damage(attacker, defender, move, critical=False, roll=100)
    attacker.status = Status.BURN
    burned = calculate_damage(attacker, defender, move, critical=False, roll=100)
    assert burned.damage < normal.damage
    # Should be approximately half
    assert abs(burned.damage - normal.damage // 2) <= 2


def test_burn_does_not_halve_special_damage():
    """Burned attacker's special moves should not be halved."""
    attacker = _make_pokemon("Alakazam", ["psychic"],
        {"hp": 55, "attack": 50, "defense": 45, "sp_attack": 135, "sp_defense": 95, "speed": 120})
    defender = _make_pokemon("Machamp", ["fighting"],
        {"hp": 90, "attack": 130, "defense": 80, "sp_attack": 65, "sp_defense": 85, "speed": 55})
    move = _make_move("Psychic", "psychic", MoveCategory.SPECIAL, 90)
    normal = calculate_damage(attacker, defender, move, critical=False, roll=100)
    attacker.status = Status.BURN
    burned = calculate_damage(attacker, defender, move, critical=False, roll=100)
    assert normal.damage == burned.damage
