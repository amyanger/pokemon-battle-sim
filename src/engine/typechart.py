"""Gen 4 type effectiveness chart (17 types, no Fairy)."""

TYPES = [
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic",
    "bug", "rock", "ghost", "dragon", "dark", "steel",
]

# Chart[attacker][defender] -> effectiveness
# Only non-1.0 entries stored for brevity
_SUPER = 2.0
_WEAK = 0.5
_IMMUNE = 0.0

_CHART: dict[str, dict[str, float]] = {
    "normal":   {"rock": _WEAK, "ghost": _IMMUNE, "steel": _WEAK},
    "fire":     {"fire": _WEAK, "water": _WEAK, "grass": _SUPER, "ice": _SUPER, "bug": _SUPER, "rock": _WEAK, "dragon": _WEAK, "steel": _SUPER},
    "water":    {"fire": _SUPER, "water": _WEAK, "grass": _WEAK, "ground": _SUPER, "rock": _SUPER, "dragon": _WEAK},
    "electric": {"water": _SUPER, "electric": _WEAK, "grass": _WEAK, "ground": _IMMUNE, "flying": _SUPER, "dragon": _WEAK},
    "grass":    {"fire": _WEAK, "water": _SUPER, "grass": _WEAK, "poison": _WEAK, "ground": _SUPER, "flying": _WEAK, "bug": _WEAK, "rock": _SUPER, "dragon": _WEAK, "steel": _WEAK},
    "ice":      {"fire": _WEAK, "water": _WEAK, "grass": _SUPER, "ice": _WEAK, "ground": _SUPER, "flying": _SUPER, "dragon": _SUPER, "steel": _WEAK},
    "fighting": {"normal": _SUPER, "ice": _SUPER, "poison": _WEAK, "flying": _WEAK, "psychic": _WEAK, "bug": _WEAK, "rock": _SUPER, "ghost": _IMMUNE, "dark": _SUPER, "steel": _SUPER},
    "poison":   {"grass": _SUPER, "poison": _WEAK, "ground": _WEAK, "rock": _WEAK, "ghost": _WEAK, "steel": _IMMUNE},
    "ground":   {"fire": _SUPER, "electric": _SUPER, "grass": _WEAK, "poison": _SUPER, "flying": _IMMUNE, "bug": _WEAK, "rock": _SUPER, "steel": _SUPER},
    "flying":   {"electric": _WEAK, "grass": _SUPER, "fighting": _SUPER, "bug": _SUPER, "rock": _WEAK, "steel": _WEAK},
    "psychic":  {"fighting": _SUPER, "poison": _SUPER, "psychic": _WEAK, "dark": _IMMUNE, "steel": _WEAK},
    "bug":      {"fire": _WEAK, "grass": _SUPER, "fighting": _WEAK, "poison": _WEAK, "flying": _WEAK, "psychic": _SUPER, "ghost": _WEAK, "dark": _SUPER, "steel": _WEAK},
    "rock":     {"fire": _SUPER, "ice": _SUPER, "fighting": _WEAK, "ground": _WEAK, "flying": _SUPER, "bug": _SUPER, "steel": _WEAK},
    "ghost":    {"normal": _IMMUNE, "psychic": _SUPER, "ghost": _SUPER, "dark": _WEAK, "steel": _WEAK},
    "dragon":   {"dragon": _SUPER, "steel": _WEAK},
    "dark":     {"fighting": _WEAK, "psychic": _SUPER, "ghost": _SUPER, "dark": _WEAK, "steel": _WEAK},
    "steel":    {"fire": _WEAK, "water": _WEAK, "electric": _WEAK, "ice": _SUPER, "rock": _SUPER, "steel": _WEAK},
}


def type_effectiveness(attack_type: str, defend_type: str) -> float:
    """Single type vs single type effectiveness."""
    return _CHART.get(attack_type, {}).get(defend_type, 1.0)


def get_matchup(attack_type: str, defend_types: list[str]) -> float:
    """Attack type vs defender's type(s). Multiply effectiveness for dual types."""
    result = 1.0
    for dt in defend_types:
        result *= type_effectiveness(attack_type, dt)
    return result
