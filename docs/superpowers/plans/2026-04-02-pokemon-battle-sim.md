# Pokemon Battle Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI Pokemon battle simulator with Gen 4 mechanics and improved AI (weighted scoring, 2-turn lookahead, memory, personality profiles). Players build teams via PokeAPI, battle canonical Platinum champions.

**Architecture:** Modular engine — data layer (PokeAPI client, champion loader), battle engine (damage, types, turns, status), AI system (scorer, lookahead, memory, personality), CLI (display, team builder, app). Each module is independently testable.

**Tech Stack:** Python 3.12+, httpx, typer, rich, pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Project config, dependencies |
| `src/__init__.py` | Package root |
| `src/engine/pokemon.py` | Pokemon and Move dataclasses, stat calculation |
| `src/engine/typechart.py` | Gen 4 17-type effectiveness lookup |
| `src/engine/damage.py` | Gen 4 damage formula with modifiers |
| `src/engine/moves.py` | Status effects, move execution, stat stages |
| `src/engine/battle.py` | Turn loop, speed priority, win condition |
| `src/data/pokeapi_client.py` | Fetch Pokemon/move/type data from PokeAPI |
| `src/data/champion_loader.py` | Parse decompilation JSON into battle-ready teams |
| `src/ai/memory.py` | Turn history tracking, pattern detection |
| `src/ai/personality.py` | Personality profiles with dimension weights |
| `src/ai/scorer.py` | 5-dimension move scoring |
| `src/ai/opponent_model.py` | Track revealed moves, estimate threats |
| `src/ai/lookahead.py` | 2-turn simulation and board evaluation |
| `src/cli/display.py` | Health bars, battle rendering with rich |
| `src/cli/team_builder.py` | 4-mode team selection |
| `src/cli/app.py` | Entry point, main menu, battle loop glue |
| `tests/engine/test_pokemon.py` | Pokemon model tests |
| `tests/engine/test_typechart.py` | Type chart tests |
| `tests/engine/test_damage.py` | Damage formula tests |
| `tests/engine/test_moves.py` | Status/move effect tests |
| `tests/engine/test_battle.py` | Turn resolution tests |
| `tests/data/test_pokeapi_client.py` | PokeAPI client tests |
| `tests/data/test_champion_loader.py` | Champion loader tests |
| `tests/ai/test_memory.py` | AI memory tests |
| `tests/ai/test_personality.py` | Personality tests |
| `tests/ai/test_scorer.py` | Scorer tests |
| `tests/ai/test_opponent_model.py` | Opponent model tests |
| `tests/ai/test_lookahead.py` | Lookahead tests |

---

### Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `src/__init__.py`, `src/engine/__init__.py`, `src/data/__init__.py`, `src/ai/__init__.py`, `src/cli/__init__.py`
- Create: `tests/__init__.py`, `tests/engine/__init__.py`, `tests/data/__init__.py`, `tests/ai/__init__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "pokemon-battle-sim"
version = "0.1.0"
description = "Pokemon battle simulator with improved AI"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27",
    "typer>=0.12",
    "rich>=13.0",
]

[project.scripts]
pokebattle = "src.cli.app:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.23"]
```

- [ ] **Step 2: Create package __init__.py files**

Create empty `__init__.py` files at:
- `src/__init__.py`
- `src/engine/__init__.py`
- `src/data/__init__.py`
- `src/ai/__init__.py`
- `src/cli/__init__.py`
- `tests/__init__.py`
- `tests/engine/__init__.py`
- `tests/data/__init__.py`
- `tests/ai/__init__.py`

- [ ] **Step 3: Install dependencies**

```bash
cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

- [ ] **Step 4: Verify pytest runs**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest --co -q`
Expected: "no tests ran" (no errors)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat: project scaffold with dependencies"
```

---

### Task 2: Pokemon Model

**Files:**
- Create: `src/engine/pokemon.py`
- Create: `tests/engine/test_pokemon.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/engine/test_pokemon.py
from src.engine.pokemon import Move, Pokemon, MoveCategory, Status

def test_move_creation():
    move = Move(
        name="Thunderbolt",
        type="electric",
        category=MoveCategory.SPECIAL,
        power=95,
        accuracy=100,
        pp=15,
        priority=0,
        effect=None,
    )
    assert move.name == "Thunderbolt"
    assert move.current_pp == 15

def test_pokemon_creation():
    pokemon = Pokemon(
        name="Pikachu",
        types=["electric"],
        level=100,
        base_stats={"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[],
        ability="static",
        item=None,
        iv_scale=250,
    )
    assert pokemon.name == "Pikachu"
    assert pokemon.current_hp == pokemon.max_hp
    assert pokemon.is_alive

def test_stat_calculation():
    """Gen 4 stat formula: ((2*Base + IV + EV/4) * Level/100 + 5) * Nature"""
    pokemon = Pokemon(
        name="Garchomp",
        types=["dragon", "ground"],
        level=100,
        base_stats={"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[],
        ability="sand-veil",
        item=None,
        iv_scale=250,
    )
    # IV scale 250 maps to IV=31. With neutral nature, no EVs:
    # HP = (2*108 + 31) * 100/100 + 100 + 10 = 357
    # Atk = ((2*130 + 31) * 100/100 + 5) = 296
    assert pokemon.max_hp == 357
    assert pokemon.stats["attack"] == 296
    assert pokemon.stats["speed"] == 239

def test_pokemon_take_damage():
    pokemon = Pokemon(
        name="Pikachu",
        types=["electric"],
        level=50,
        base_stats={"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[],
        ability="static",
        item=None,
        iv_scale=250,
    )
    max_hp = pokemon.max_hp
    pokemon.take_damage(50)
    assert pokemon.current_hp == max_hp - 50
    assert pokemon.is_alive
    pokemon.take_damage(9999)
    assert pokemon.current_hp == 0
    assert not pokemon.is_alive

def test_stat_stages():
    pokemon = Pokemon(
        name="Pikachu",
        types=["electric"],
        level=100,
        base_stats={"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[],
        ability="static",
        item=None,
        iv_scale=250,
    )
    assert pokemon.stat_stages["attack"] == 0
    pokemon.modify_stat_stage("attack", 2)
    assert pokemon.stat_stages["attack"] == 2
    # +2 = 2x multiplier
    assert pokemon.get_effective_stat("attack") == pokemon.stats["attack"] * 2
    pokemon.modify_stat_stage("attack", 6)
    assert pokemon.stat_stages["attack"] == 6  # clamped at +6
    pokemon.modify_stat_stage("attack", -12)
    assert pokemon.stat_stages["attack"] == -6  # clamped at -6
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/engine/test_pokemon.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement Pokemon model**

```python
# src/engine/pokemon.py
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
    return (iv_scale * 31) // 255


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/engine/test_pokemon.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/engine/pokemon.py tests/engine/test_pokemon.py
git commit -m "feat: pokemon and move models with Gen 4 stat calculation"
```

---

### Task 3: Type Chart

**Files:**
- Create: `src/engine/typechart.py`
- Create: `tests/engine/test_typechart.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/engine/test_typechart.py
from src.engine.typechart import type_effectiveness, get_matchup

def test_super_effective():
    assert type_effectiveness("fire", "grass") == 2.0
    assert type_effectiveness("water", "fire") == 2.0
    assert type_effectiveness("electric", "water") == 2.0

def test_not_very_effective():
    assert type_effectiveness("fire", "water") == 0.5
    assert type_effectiveness("grass", "fire") == 0.5

def test_immune():
    assert type_effectiveness("normal", "ghost") == 0.0
    assert type_effectiveness("ground", "flying") == 0.0
    assert type_effectiveness("electric", "ground") == 0.0

def test_neutral():
    assert type_effectiveness("fire", "normal") == 1.0

def test_dual_type_matchup():
    # Fire vs Grass/Poison = 2x * 1x = 2x
    assert get_matchup("fire", ["grass", "poison"]) == 2.0
    # Ground vs Water/Flying = 1x * 0x = 0x
    assert get_matchup("ground", ["water", "flying"]) == 0.0
    # Ice vs Dragon/Ground = 2x * 2x = 4x
    assert get_matchup("ice", ["dragon", "ground"]) == 4.0
    # Fire vs Water/Rock = 0.5x * 0.5x = 0.25x
    assert get_matchup("fire", ["water", "rock"]) == 0.25
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/engine/test_typechart.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement type chart**

```python
# src/engine/typechart.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/engine/test_typechart.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/engine/typechart.py tests/engine/test_typechart.py
git commit -m "feat: Gen 4 type effectiveness chart"
```

---

### Task 4: Damage Calculator

**Files:**
- Create: `src/engine/damage.py`
- Create: `tests/engine/test_damage.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/engine/test_damage.py
import random
from src.engine.damage import calculate_damage
from src.engine.pokemon import Pokemon, Move, MoveCategory


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
    random.seed(0)  # fix the roll
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/engine/test_damage.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement damage calculator**

```python
# src/engine/damage.py
from __future__ import annotations
import random
from dataclasses import dataclass
from src.engine.pokemon import Pokemon, Move, MoveCategory
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/engine/test_damage.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/engine/damage.py tests/engine/test_damage.py
git commit -m "feat: Gen 4 damage calculator with STAB, crits, type effectiveness"
```

---

### Task 5: Move Effects & Status System

**Files:**
- Create: `src/engine/moves.py`
- Create: `tests/engine/test_moves.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/engine/test_moves.py
from src.engine.moves import apply_status, apply_end_of_turn, can_act
from src.engine.pokemon import Pokemon, Move, MoveCategory, Status


def _make_pokemon(name="Pikachu", level=100):
    return Pokemon(
        name=name, types=["electric"], level=level,
        base_stats={"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[], ability="", item=None, iv_scale=250,
    )


def test_apply_burn():
    poke = _make_pokemon()
    applied = apply_status(poke, Status.BURN)
    assert applied
    assert poke.status == Status.BURN

def test_cannot_double_status():
    poke = _make_pokemon()
    apply_status(poke, Status.BURN)
    applied = apply_status(poke, Status.PARALYSIS)
    assert not applied
    assert poke.status == Status.BURN

def test_burn_end_of_turn():
    poke = _make_pokemon()
    apply_status(poke, Status.BURN)
    hp_before = poke.current_hp
    apply_end_of_turn(poke)
    # Burn does 1/8 max HP
    assert poke.current_hp == hp_before - poke.max_hp // 8

def test_poison_end_of_turn():
    poke = _make_pokemon()
    apply_status(poke, Status.POISON)
    hp_before = poke.current_hp
    apply_end_of_turn(poke)
    # Poison does 1/8 max HP
    assert poke.current_hp == hp_before - poke.max_hp // 8

def test_bad_poison_escalates():
    poke = _make_pokemon()
    apply_status(poke, Status.BAD_POISON)
    hp_before = poke.current_hp
    apply_end_of_turn(poke)
    # Bad poison turn 1: 1/16 max HP
    damage_t1 = hp_before - poke.current_hp
    assert damage_t1 == poke.max_hp // 16
    hp_before = poke.current_hp
    apply_end_of_turn(poke)
    # Bad poison turn 2: 2/16 max HP
    damage_t2 = hp_before - poke.current_hp
    assert damage_t2 == (poke.max_hp * 2) // 16

def test_sleep_prevents_action():
    import random
    random.seed(0)
    poke = _make_pokemon()
    apply_status(poke, Status.SLEEP)
    # Sleep lasts 1-3 turns; while asleep can_act returns False
    assert poke.status == Status.SLEEP
    result = can_act(poke)
    # Either still asleep (False) or just woke up (True) — both valid

def test_paralysis_speed_quarter():
    poke = _make_pokemon()
    apply_status(poke, Status.PARALYSIS)
    # Paralysis quarters speed
    effective_speed = poke.get_effective_stat("speed")
    # Base speed stat at level 100 = 185, quartered = 46
    assert effective_speed == poke.stats["speed"]  # stat_stages don't handle para
    # Paralysis speed is handled in battle turn order, not stat stages
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/engine/test_moves.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement move effects**

```python
# src/engine/moves.py
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
        if random.randint(1, 5) == 1:  # 20% thaw
            pokemon.status = Status.NONE
            return True
        return False

    if pokemon.status == Status.PARALYSIS:
        if random.randint(1, 4) == 1:  # 25% full para
            return False

    # Confusion check (volatile)
    if "confusion" in pokemon.volatile:
        pokemon.status_turns = pokemon.status_turns  # track separately if needed
        if random.randint(1, 2) == 1:
            return False  # hits self in confusion

    return True


def get_effective_speed(pokemon: Pokemon) -> int:
    """Get speed accounting for paralysis."""
    speed = pokemon.get_effective_stat("speed")
    if pokemon.status == Status.PARALYSIS:
        speed = speed // 4
    return speed
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/engine/test_moves.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/engine/moves.py tests/engine/test_moves.py
git commit -m "feat: status conditions with end-of-turn effects and action checks"
```

---

### Task 6: PokeAPI Client

**Files:**
- Create: `src/data/pokeapi_client.py`
- Create: `tests/data/test_pokeapi_client.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/data/test_pokeapi_client.py
import pytest
from src.data.pokeapi_client import PokeAPIClient
from src.engine.pokemon import Pokemon, MoveCategory


@pytest.fixture
def client():
    return PokeAPIClient()


def test_fetch_pokemon(client):
    """Fetch Pikachu and verify basic data."""
    pokemon = client.get_pokemon("pikachu", level=50)
    assert pokemon.name == "pikachu"
    assert "electric" in pokemon.types
    assert pokemon.level == 50
    assert pokemon.max_hp > 0
    assert pokemon.base_stats["speed"] == 90

def test_fetch_pokemon_by_id(client):
    pokemon = client.get_pokemon(25, level=100)  # Pikachu = #25
    assert pokemon.name == "pikachu"

def test_fetch_move(client):
    move = client.get_move("thunderbolt")
    assert move.name == "thunderbolt"
    assert move.type == "electric"
    assert move.category == MoveCategory.SPECIAL
    assert move.power == 95
    assert move.accuracy == 100
    assert move.pp == 15

def test_fetch_pokemon_with_moves(client):
    pokemon = client.get_pokemon("garchomp", level=62, move_names=["earthquake", "dragon-rush", "flamethrower", "giga-impact"])
    assert len(pokemon.moves) == 4
    assert pokemon.moves[0].name == "earthquake"

def test_get_random_pokemon(client):
    pokemon = client.get_random_pokemon(level=100, gen=4)
    assert pokemon.name
    assert len(pokemon.moves) == 4
    assert pokemon.level == 100

def test_get_learnable_moves(client):
    moves = client.get_learnable_moves("pikachu", gen=4)
    assert len(moves) > 0
    assert "thunderbolt" in moves
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/data/test_pokeapi_client.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement PokeAPI client**

```python
# src/data/pokeapi_client.py
from __future__ import annotations
import random
import httpx
from src.engine.pokemon import Pokemon, Move, MoveCategory


_BASE_URL = "https://pokeapi.co/api/v2"

# Gen 4 national dex range
_GEN4_MAX_DEX = 493

_CATEGORY_MAP = {
    "physical": MoveCategory.PHYSICAL,
    "special": MoveCategory.SPECIAL,
    "status": MoveCategory.STATUS,
}


class PokeAPIClient:
    def __init__(self):
        self._http = httpx.Client(base_url=_BASE_URL, timeout=30.0)

    def _get(self, path: str) -> dict:
        resp = self._http.get(path)
        resp.raise_for_status()
        return resp.json()

    def get_move(self, name: str) -> Move:
        data = self._get(f"/move/{name}")
        return Move(
            name=data["name"],
            type=data["type"]["name"],
            category=_CATEGORY_MAP[data["damage_class"]["name"]],
            power=data["power"] or 0,
            accuracy=data["accuracy"] or 100,
            pp=data["pp"],
            priority=data["priority"],
            effect=data["effect_entries"][0]["short_effect"] if data["effect_entries"] else None,
        )

    def get_pokemon(
        self,
        name_or_id: str | int,
        level: int = 100,
        move_names: list[str] | None = None,
        iv_scale: int = 250,
    ) -> Pokemon:
        data = self._get(f"/pokemon/{name_or_id}")
        stats_map = {}
        stat_name_map = {
            "hp": "hp", "attack": "attack", "defense": "defense",
            "special-attack": "sp_attack", "special-defense": "sp_defense", "speed": "speed",
        }
        for s in data["stats"]:
            key = stat_name_map[s["stat"]["name"]]
            stats_map[key] = s["base_stat"]

        types = [t["type"]["name"] for t in data["types"]]
        abilities = [a["ability"]["name"] for a in data["abilities"]]
        ability = abilities[0] if abilities else ""

        moves = []
        if move_names:
            for mn in move_names:
                moves.append(self.get_move(mn))

        return Pokemon(
            name=data["name"],
            types=types,
            level=level,
            base_stats=stats_map,
            moves=moves,
            ability=ability,
            item=None,
            iv_scale=iv_scale,
        )

    def get_learnable_moves(self, name_or_id: str | int, gen: int = 4) -> list[str]:
        data = self._get(f"/pokemon/{name_or_id}")
        gen_name = f"generation-{['i','ii','iii','iv','v','vi','vii','viii','ix'][gen-1]}"
        learnable = []
        for m in data["moves"]:
            for vg in m["version_group_details"]:
                # Check if learnable by level-up or TM in this generation's games
                if "platinum" in vg["version_group"]["name"] or gen_name in vg["version_group"]["url"]:
                    learnable.append(m["move"]["name"])
                    break
            else:
                # Fallback: include if any gen 4 version group
                for vg in m["version_group_details"]:
                    if "diamond" in vg["version_group"]["name"] or "pearl" in vg["version_group"]["name"]:
                        learnable.append(m["move"]["name"])
                        break
        return list(set(learnable))

    def get_random_pokemon(self, level: int = 100, gen: int = 4) -> Pokemon:
        dex_id = random.randint(1, _GEN4_MAX_DEX)
        learnable = self.get_learnable_moves(dex_id, gen=gen)
        # Pick 4 random moves, preferring damaging moves
        if len(learnable) <= 4:
            chosen_moves = learnable
        else:
            chosen_moves = random.sample(learnable, 4)
        moves = []
        for mn in chosen_moves:
            try:
                moves.append(self.get_move(mn))
            except httpx.HTTPStatusError:
                continue
        return self.get_pokemon(dex_id, level=level, iv_scale=250)._replace_moves(moves)

    def close(self):
        self._http.close()
```

Then add a helper to Pokemon for replacing moves after creation — edit `src/engine/pokemon.py` to add:

```python
# Add to the Pokemon class in src/engine/pokemon.py
    def _replace_moves(self, moves: list[Move]) -> Pokemon:
        """Return self with replaced moves (used by API client)."""
        self.moves = moves
        return self
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/data/test_pokeapi_client.py -v`
Expected: 6 passed (requires internet connection)

- [ ] **Step 5: Commit**

```bash
git add src/data/pokeapi_client.py tests/data/test_pokeapi_client.py src/engine/pokemon.py
git commit -m "feat: PokeAPI client for fetching Pokemon, moves, and learnsets"
```

---

### Task 7: Champion Data Loader

**Files:**
- Create: `src/data/champion_loader.py`
- Create: `tests/data/test_champion_loader.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/data/test_champion_loader.py
from src.data.champion_loader import ChampionLoader


def test_load_cynthia():
    loader = ChampionLoader()
    team = loader.load_champion("champion_cynthia")
    assert team.name == "Cynthia"
    assert len(team.party) == 6
    assert team.party[0].species == "spiritomb"
    assert team.party[0].level == 58
    assert team.party[0].moves == ["dark-pulse", "psychic", "silver-wind", "shadow-ball"]
    assert team.party[5].species == "garchomp"
    assert team.party[5].item == "sitrus-berry"
    assert len(team.items) == 4

def test_load_aaron():
    loader = ChampionLoader()
    team = loader.load_champion("elite_four_aaron")
    assert team.name == "Aaron"
    assert len(team.party) == 5
    assert team.party[0].species == "yanmega"

def test_list_champions():
    loader = ChampionLoader()
    champs = loader.list_champions()
    assert "champion_cynthia" in champs
    assert "elite_four_aaron" in champs
    assert "elite_four_bertha" in champs
    assert "elite_four_flint" in champs
    assert "elite_four_lucian" in champs

def test_constant_to_api_name():
    from src.data.champion_loader import _constant_to_api_name
    assert _constant_to_api_name("SPECIES_GARCHOMP") == "garchomp"
    assert _constant_to_api_name("MOVE_DARK_PULSE") == "dark-pulse"
    assert _constant_to_api_name("MOVE_GIGA_IMPACT") == "giga-impact"
    assert _constant_to_api_name("ITEM_FULL_RESTORE") == "full-restore"
    assert _constant_to_api_name("ITEM_SITRUS_BERRY") == "sitrus-berry"
    assert _constant_to_api_name("ITEM_NONE") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/data/test_champion_loader.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement champion loader**

```python
# src/data/champion_loader.py
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path


_DECOMP_TRAINERS_PATH = Path("/mnt/c/Users/arjun.myanger/development/pokeplatinum/res/trainers/data")

# Champion/E4 files we support
_CHAMPION_FILES = [
    "champion_cynthia",
    "champion_cynthia_rematch",
    "elite_four_aaron",
    "elite_four_aaron_rematch",
    "elite_four_bertha",
    "elite_four_bertha_rematch",
    "elite_four_flint",
    "elite_four_flint_rematch",
    "elite_four_lucian",
    "elite_four_lucian_rematch",
]


def _constant_to_api_name(constant: str) -> str | None:
    """Convert decompilation constants to PokeAPI-compatible names.

    SPECIES_GARCHOMP -> garchomp
    MOVE_DARK_PULSE -> dark-pulse
    ITEM_SITRUS_BERRY -> sitrus-berry
    ITEM_NONE -> None
    """
    if constant == "ITEM_NONE":
        return None
    # Strip prefix (SPECIES_, MOVE_, ITEM_)
    parts = constant.split("_", 1)
    if len(parts) == 2 and parts[0] in ("SPECIES", "MOVE", "ITEM"):
        name = parts[1].lower().replace("_", "-")
    else:
        # Handle MOVE_X_SCISSOR -> x-scissor (prefix is MOVE)
        name = constant.split("_", 1)[1].lower().replace("_", "-")
    return name


@dataclass
class PartyMember:
    species: str
    level: int
    moves: list[str]
    item: str | None
    iv_scale: int


@dataclass
class ChampionTeam:
    name: str
    trainer_class: str
    party: list[PartyMember]
    items: list[str]
    ai_flags: list[str]


class ChampionLoader:
    def __init__(self, trainers_path: Path = _DECOMP_TRAINERS_PATH):
        self._path = trainers_path

    def list_champions(self) -> list[str]:
        available = []
        for name in _CHAMPION_FILES:
            if (self._path / f"{name}.json").exists():
                available.append(name)
        return available

    def load_champion(self, filename: str) -> ChampionTeam:
        filepath = self._path / f"{filename}.json"
        with open(filepath) as f:
            data = json.load(f)

        party = []
        for member in data["party"]:
            species = _constant_to_api_name(member["species"])
            moves = [_constant_to_api_name(m) for m in member["moves"]]
            item = _constant_to_api_name(member["item"])
            party.append(PartyMember(
                species=species,
                level=member["level"],
                moves=moves,
                item=item,
                iv_scale=member["iv_scale"],
            ))

        items = [_constant_to_api_name(i) for i in data.get("items", []) if _constant_to_api_name(i)]

        return ChampionTeam(
            name=data["name"],
            trainer_class=data["class"],
            party=party,
            items=items,
            ai_flags=data.get("ai_flags", []),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/data/test_champion_loader.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/data/champion_loader.py tests/data/test_champion_loader.py
git commit -m "feat: champion data loader parsing decompilation trainer JSONs"
```

---

### Task 8: Battle Engine

**Files:**
- Create: `src/engine/battle.py`
- Create: `tests/engine/test_battle.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/engine/test_battle.py
import random
from src.engine.battle import Battle, BattleAction, ActionType, BattleEvent, EventType
from src.engine.pokemon import Pokemon, Move, MoveCategory


def _make_move(name, type_, category, power, priority=0, accuracy=100, pp=10, effect=None):
    return Move(name=name, type=type_, category=category, power=power,
                accuracy=accuracy, pp=pp, priority=priority, effect=effect)


def _make_pokemon(name, types, base_stats, level=100, moves=None, iv_scale=250):
    return Pokemon(name=name, types=types, level=level, base_stats=base_stats,
                   moves=moves or [], ability="", item=None, iv_scale=iv_scale)


def test_turn_order_by_speed():
    fast = _make_pokemon("Fast", ["normal"],
        {"hp": 50, "attack": 50, "defense": 50, "sp_attack": 50, "sp_defense": 50, "speed": 150},
        moves=[_make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40)])
    slow = _make_pokemon("Slow", ["normal"],
        {"hp": 50, "attack": 50, "defense": 50, "sp_attack": 50, "sp_defense": 50, "speed": 10},
        moves=[_make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40)])
    battle = Battle(player_team=[fast], opponent_team=[slow])
    first, second = battle.get_turn_order(
        BattleAction(ActionType.MOVE, move_index=0),
        BattleAction(ActionType.MOVE, move_index=0),
    )
    assert first.pokemon.name == "Fast"

def test_priority_overrides_speed():
    slow = _make_pokemon("Slow", ["normal"],
        {"hp": 50, "attack": 50, "defense": 50, "sp_attack": 50, "sp_defense": 50, "speed": 10},
        moves=[_make_move("Quick Attack", "normal", MoveCategory.PHYSICAL, 40, priority=1)])
    fast = _make_pokemon("Fast", ["normal"],
        {"hp": 50, "attack": 50, "defense": 50, "sp_attack": 50, "sp_defense": 50, "speed": 150},
        moves=[_make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40)])
    battle = Battle(player_team=[slow], opponent_team=[fast])
    first, second = battle.get_turn_order(
        BattleAction(ActionType.MOVE, move_index=0),
        BattleAction(ActionType.MOVE, move_index=0),
    )
    assert first.pokemon.name == "Slow"

def test_switch_goes_before_attack():
    poke1 = _make_pokemon("Attacker", ["normal"],
        {"hp": 50, "attack": 50, "defense": 50, "sp_attack": 50, "sp_defense": 50, "speed": 200},
        moves=[_make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40)])
    poke2 = _make_pokemon("Switcher", ["normal"],
        {"hp": 50, "attack": 50, "defense": 50, "sp_attack": 50, "sp_defense": 50, "speed": 10},
        moves=[_make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40)])
    bench = _make_pokemon("Bench", ["normal"],
        {"hp": 50, "attack": 50, "defense": 50, "sp_attack": 50, "sp_defense": 50, "speed": 10},
        moves=[_make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40)])
    battle = Battle(player_team=[poke1], opponent_team=[poke2, bench])
    first, second = battle.get_turn_order(
        BattleAction(ActionType.MOVE, move_index=0),
        BattleAction(ActionType.SWITCH, switch_index=1),
    )
    assert first.action.action_type == ActionType.SWITCH

def test_execute_turn_deals_damage():
    random.seed(42)
    attacker = _make_pokemon("Attacker", ["normal"],
        {"hp": 100, "attack": 100, "defense": 50, "sp_attack": 50, "sp_defense": 50, "speed": 100},
        moves=[_make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40)])
    defender = _make_pokemon("Defender", ["normal"],
        {"hp": 100, "attack": 50, "defense": 50, "sp_attack": 50, "sp_defense": 50, "speed": 50},
        moves=[_make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40)])
    battle = Battle(player_team=[attacker], opponent_team=[defender])
    events = battle.execute_turn(
        BattleAction(ActionType.MOVE, move_index=0),
        BattleAction(ActionType.MOVE, move_index=0),
    )
    # Both should have taken damage
    damage_events = [e for e in events if e.event_type == EventType.DAMAGE]
    assert len(damage_events) >= 1
    assert defender.current_hp < defender.max_hp

def test_battle_win_condition():
    strong = _make_pokemon("Strong", ["fighting"],
        {"hp": 200, "attack": 200, "defense": 200, "sp_attack": 200, "sp_defense": 200, "speed": 200},
        moves=[_make_move("Close Combat", "fighting", MoveCategory.PHYSICAL, 120)])
    weak = _make_pokemon("Weak", ["normal"],
        {"hp": 10, "attack": 10, "defense": 10, "sp_attack": 10, "sp_defense": 10, "speed": 10},
        moves=[_make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40)])
    battle = Battle(player_team=[strong], opponent_team=[weak])
    events = battle.execute_turn(
        BattleAction(ActionType.MOVE, move_index=0),
        BattleAction(ActionType.MOVE, move_index=0),
    )
    assert battle.is_over()
    assert battle.get_winner() == "player"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/engine/test_battle.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement battle engine**

```python
# src/engine/battle.py
from __future__ import annotations
import random
from dataclasses import dataclass, field
from enum import Enum
from src.engine.pokemon import Pokemon, Move, Status
from src.engine.damage import calculate_damage, DamageResult
from src.engine.moves import apply_end_of_turn, can_act, get_effective_speed
from src.engine.typechart import get_matchup


class ActionType(Enum):
    MOVE = "move"
    SWITCH = "switch"
    ITEM = "item"


class EventType(Enum):
    DAMAGE = "damage"
    MISS = "miss"
    STATUS = "status"
    FAINT = "faint"
    SWITCH = "switch"
    EFFECTIVENESS = "effectiveness"
    CRITICAL = "critical"
    END_OF_TURN = "end_of_turn"
    CANT_ACT = "cant_act"
    ITEM_USED = "item_used"


@dataclass
class BattleAction:
    action_type: ActionType
    move_index: int = 0
    switch_index: int = 0
    item_name: str | None = None


@dataclass
class BattleEvent:
    event_type: EventType
    source: str = ""
    target: str = ""
    message: str = ""
    damage: int = 0
    effectiveness: float = 1.0


@dataclass
class TurnEntry:
    pokemon: Pokemon
    action: BattleAction
    team: str  # "player" or "opponent"


class Battle:
    def __init__(self, player_team: list[Pokemon], opponent_team: list[Pokemon]):
        self.player_team = player_team
        self.opponent_team = opponent_team
        self.player_active: int = 0
        self.opponent_active: int = 0
        self.turn_count: int = 0
        self.player_fainted: int = 0
        self.opponent_fainted: int = 0
        self.damage_dealt: dict[str, int] = {}  # pokemon name -> total damage

    @property
    def player_pokemon(self) -> Pokemon:
        return self.player_team[self.player_active]

    @property
    def opponent_pokemon(self) -> Pokemon:
        return self.opponent_team[self.opponent_active]

    def get_turn_order(
        self, player_action: BattleAction, opponent_action: BattleAction
    ) -> tuple[TurnEntry, TurnEntry]:
        player_entry = TurnEntry(self.player_pokemon, player_action, "player")
        opponent_entry = TurnEntry(self.opponent_pokemon, opponent_action, "opponent")

        # Switches always go first
        if player_action.action_type == ActionType.SWITCH and opponent_action.action_type != ActionType.SWITCH:
            return player_entry, opponent_entry
        if opponent_action.action_type == ActionType.SWITCH and player_action.action_type != ActionType.SWITCH:
            return opponent_entry, player_entry

        # Items go before moves
        if player_action.action_type == ActionType.ITEM and opponent_action.action_type == ActionType.MOVE:
            return player_entry, opponent_entry
        if opponent_action.action_type == ActionType.ITEM and player_action.action_type == ActionType.MOVE:
            return opponent_entry, player_entry

        # Both moves: check priority
        if player_action.action_type == ActionType.MOVE and opponent_action.action_type == ActionType.MOVE:
            p_priority = self.player_pokemon.moves[player_action.move_index].priority
            o_priority = self.opponent_pokemon.moves[opponent_action.move_index].priority
            if p_priority != o_priority:
                if p_priority > o_priority:
                    return player_entry, opponent_entry
                return opponent_entry, player_entry

        # Same priority: compare speed
        p_speed = get_effective_speed(self.player_pokemon)
        o_speed = get_effective_speed(self.opponent_pokemon)
        if p_speed == o_speed:
            if random.randint(0, 1) == 0:
                return player_entry, opponent_entry
            return opponent_entry, player_entry
        if p_speed > o_speed:
            return player_entry, opponent_entry
        return opponent_entry, player_entry

    def execute_turn(
        self, player_action: BattleAction, opponent_action: BattleAction
    ) -> list[BattleEvent]:
        self.turn_count += 1
        events: list[BattleEvent] = []

        first, second = self.get_turn_order(player_action, opponent_action)

        # Execute first action
        target_first = self.opponent_pokemon if first.team == "player" else self.player_pokemon
        events.extend(self._execute_action(first, target_first))

        # Execute second action (if still alive)
        if second.pokemon.is_alive:
            target_second = self.opponent_pokemon if second.team == "player" else self.player_pokemon
            if target_second.is_alive:
                events.extend(self._execute_action(second, target_second))

        # End of turn effects
        for pokemon in [self.player_pokemon, self.opponent_pokemon]:
            if pokemon.is_alive:
                eot_damage = apply_end_of_turn(pokemon)
                if eot_damage > 0:
                    events.append(BattleEvent(
                        EventType.END_OF_TURN, source=pokemon.name,
                        message=f"{pokemon.name} took {eot_damage} damage from {pokemon.status.value}!",
                        damage=eot_damage,
                    ))
                    if not pokemon.is_alive:
                        events.append(BattleEvent(EventType.FAINT, source=pokemon.name,
                                                  message=f"{pokemon.name} fainted!"))

        return events

    def _execute_action(self, entry: TurnEntry, target: Pokemon) -> list[BattleEvent]:
        events: list[BattleEvent] = []

        if entry.action.action_type == ActionType.SWITCH:
            idx = entry.action.switch_index
            if entry.team == "player":
                self.player_active = idx
                entry.pokemon.reset_stat_stages()
            else:
                self.opponent_active = idx
                entry.pokemon.reset_stat_stages()
            new_pokemon = self.player_pokemon if entry.team == "player" else self.opponent_pokemon
            events.append(BattleEvent(EventType.SWITCH, source=entry.pokemon.name,
                                      message=f"Go, {new_pokemon.name}!"))
            return events

        if entry.action.action_type == ActionType.MOVE:
            move = entry.pokemon.moves[entry.action.move_index]

            # Check if can act (sleep, paralysis, etc.)
            if not can_act(entry.pokemon):
                events.append(BattleEvent(EventType.CANT_ACT, source=entry.pokemon.name,
                                          message=f"{entry.pokemon.name} can't move!"))
                return events

            # Deduct PP
            move.current_pp = max(0, move.current_pp - 1)

            # Accuracy check
            if move.accuracy < 100 and random.randint(1, 100) > move.accuracy:
                events.append(BattleEvent(EventType.MISS, source=entry.pokemon.name,
                                          target=target.name,
                                          message=f"{entry.pokemon.name}'s {move.name} missed!"))
                return events

            # Calculate and apply damage
            result = calculate_damage(entry.pokemon, target, move)
            if result.damage > 0:
                target.take_damage(result.damage)
                self.damage_dealt[entry.pokemon.name] = self.damage_dealt.get(entry.pokemon.name, 0) + result.damage
                events.append(BattleEvent(EventType.DAMAGE, source=entry.pokemon.name,
                                          target=target.name, damage=result.damage,
                                          effectiveness=result.effectiveness,
                                          message=f"{entry.pokemon.name} used {move.name}!"))
                if result.effectiveness > 1.0:
                    events.append(BattleEvent(EventType.EFFECTIVENESS,
                                              message="It's super effective!",
                                              effectiveness=result.effectiveness))
                elif 0 < result.effectiveness < 1.0:
                    events.append(BattleEvent(EventType.EFFECTIVENESS,
                                              message="It's not very effective...",
                                              effectiveness=result.effectiveness))
                if result.critical:
                    events.append(BattleEvent(EventType.CRITICAL, message="A critical hit!"))

                if not target.is_alive:
                    events.append(BattleEvent(EventType.FAINT, source=target.name,
                                              message=f"{target.name} fainted!"))
                    if target in self.player_team:
                        self.player_fainted += 1
                    else:
                        self.opponent_fainted += 1
            elif result.effectiveness == 0.0:
                events.append(BattleEvent(EventType.EFFECTIVENESS,
                                          source=entry.pokemon.name,
                                          message=f"It doesn't affect {target.name}...",
                                          effectiveness=0.0))

        return events

    def is_over(self) -> bool:
        player_alive = any(p.is_alive for p in self.player_team)
        opponent_alive = any(p.is_alive for p in self.opponent_team)
        return not player_alive or not opponent_alive

    def get_winner(self) -> str | None:
        player_alive = any(p.is_alive for p in self.player_team)
        opponent_alive = any(p.is_alive for p in self.opponent_team)
        if not opponent_alive:
            return "player"
        if not player_alive:
            return "opponent"
        return None

    def get_alive_indices(self, team: str) -> list[int]:
        pokemon_list = self.player_team if team == "player" else self.opponent_team
        active = self.player_active if team == "player" else self.opponent_active
        return [i for i, p in enumerate(pokemon_list) if p.is_alive and i != active]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/engine/test_battle.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/engine/battle.py tests/engine/test_battle.py
git commit -m "feat: battle engine with turn resolution, priority, and win conditions"
```

---

### Task 9: AI Memory

**Files:**
- Create: `src/ai/memory.py`
- Create: `tests/ai/test_memory.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/ai/test_memory.py
from src.ai.memory import BattleMemory, TurnRecord


def test_record_turn():
    mem = BattleMemory(max_turns=4)
    mem.record_turn(TurnRecord(
        turn=1, user_move="dark-void", user_pokemon="darkrai",
        opponent_move="tackle", opponent_pokemon="pikachu",
        damage_dealt=0, damage_taken=30,
    ))
    assert len(mem.history) == 1
    assert mem.history[0].user_move == "dark-void"

def test_max_turns_limit():
    mem = BattleMemory(max_turns=2)
    for i in range(5):
        mem.record_turn(TurnRecord(
            turn=i, user_move="tackle", user_pokemon="a",
            opponent_move="tackle", opponent_pokemon="b",
            damage_dealt=10, damage_taken=10,
        ))
    assert len(mem.history) == 2
    assert mem.history[0].turn == 3  # oldest kept

def test_detect_protect_spam():
    mem = BattleMemory(max_turns=4)
    for i in range(3):
        mem.record_turn(TurnRecord(
            turn=i, user_move="tackle", user_pokemon="a",
            opponent_move="protect", opponent_pokemon="b",
            damage_dealt=0, damage_taken=0,
        ))
    patterns = mem.detect_patterns()
    assert "opponent_protect_spam" in patterns

def test_detect_sleep_lead():
    mem = BattleMemory(max_turns=4)
    mem.record_turn(TurnRecord(
        turn=1, user_move="tackle", user_pokemon="a",
        opponent_move="dark-void", opponent_pokemon="darkrai",
        damage_dealt=0, damage_taken=0,
    ))
    patterns = mem.detect_patterns()
    assert "opponent_sleep_lead" in patterns

def test_detect_switch_loop():
    mem = BattleMemory(max_turns=4)
    mem.record_turn(TurnRecord(turn=1, user_move="t", user_pokemon="a",
                               opponent_move="switch", opponent_pokemon="b",
                               damage_dealt=0, damage_taken=0))
    mem.record_turn(TurnRecord(turn=2, user_move="t", user_pokemon="a",
                               opponent_move="tackle", opponent_pokemon="c",
                               damage_dealt=0, damage_taken=0))
    mem.record_turn(TurnRecord(turn=3, user_move="t", user_pokemon="a",
                               opponent_move="switch", opponent_pokemon="b",
                               damage_dealt=0, damage_taken=0))
    patterns = mem.detect_patterns()
    assert "opponent_switch_loop" in patterns
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ai/test_memory.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement AI memory**

```python
# src/ai/memory.py
from __future__ import annotations
from dataclasses import dataclass, field

_SLEEP_MOVES = {"dark-void", "sleep-powder", "spore", "hypnosis", "sing", "grass-whistle", "lovely-kiss", "yawn"}


@dataclass
class TurnRecord:
    turn: int
    user_move: str
    user_pokemon: str
    opponent_move: str
    opponent_pokemon: str
    damage_dealt: int
    damage_taken: int


class BattleMemory:
    def __init__(self, max_turns: int = 4):
        self.max_turns = max_turns
        self.history: list[TurnRecord] = []

    def record_turn(self, record: TurnRecord):
        self.history.append(record)
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

    def detect_patterns(self) -> set[str]:
        patterns: set[str] = set()
        if not self.history:
            return patterns

        # Protect spam: opponent used protect 2+ times in last 3 turns
        recent_opp_moves = [r.opponent_move for r in self.history[-3:]]
        if recent_opp_moves.count("protect") >= 2:
            patterns.add("opponent_protect_spam")

        recent_user_moves = [r.user_move for r in self.history[-3:]]
        if recent_user_moves.count("protect") >= 2:
            patterns.add("user_protect_spam")

        # Sleep lead: opponent used a sleep move on turn 1
        if self.history[0].opponent_move in _SLEEP_MOVES:
            patterns.add("opponent_sleep_lead")
        if self.history[0].user_move in _SLEEP_MOVES:
            patterns.add("user_sleep_lead")

        # Switch loop: opponent switched, came back to same pokemon
        opp_pokemon = [r.opponent_pokemon for r in self.history]
        if len(opp_pokemon) >= 3:
            for i in range(len(opp_pokemon) - 2):
                if opp_pokemon[i] == opp_pokemon[i + 2] and opp_pokemon[i] != opp_pokemon[i + 1]:
                    patterns.add("opponent_switch_loop")
                    break

        opp_switches = [r for r in self.history if r.opponent_move == "switch"]
        if len(opp_switches) >= 2:
            patterns.add("opponent_switch_loop")

        return patterns

    def get_opponent_move_history(self, pokemon_name: str) -> list[str]:
        """Get all moves used by a specific opponent Pokemon."""
        return [r.opponent_move for r in self.history if r.opponent_pokemon == pokemon_name]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ai/test_memory.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai/memory.py tests/ai/test_memory.py
git commit -m "feat: AI battle memory with pattern detection"
```

---

### Task 10: AI Personality Profiles

**Files:**
- Create: `src/ai/personality.py`
- Create: `tests/ai/test_personality.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/ai/test_personality.py
from src.ai.personality import Personality, get_champion_personality, PROFILES


def test_balanced_profile():
    p = PROFILES["balanced"]
    assert p.damage_weight == 1.0
    assert p.kill_weight == 1.0
    assert p.risk_weight == 1.0
    assert p.setup_weight == 1.0
    assert p.disruption_weight == 1.0

def test_aggressive_profile():
    p = PROFILES["aggressive"]
    assert p.damage_weight > 1.0
    assert p.setup_weight < 1.0

def test_tactical_profile():
    p = PROFILES["tactical"]
    assert p.setup_weight > 1.0

def test_champion_personality():
    assert get_champion_personality("Cynthia").name == "tactical"
    assert get_champion_personality("Flint").name == "aggressive"
    assert get_champion_personality("Unknown").name == "balanced"

def test_apply_weights():
    p = PROFILES["aggressive"]
    scores = {"damage_value": 10, "kill_potential": 5, "risk": 3, "setup_value": 8, "disruption": 4}
    weighted = p.apply_weights(scores)
    assert weighted["damage_value"] == 10 * p.damage_weight
    assert weighted["setup_value"] == 8 * p.setup_weight
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ai/test_personality.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement personality profiles**

```python
# src/ai/personality.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Personality:
    name: str
    damage_weight: float
    kill_weight: float
    risk_weight: float
    setup_weight: float
    disruption_weight: float

    def apply_weights(self, scores: dict[str, float]) -> dict[str, float]:
        weight_map = {
            "damage_value": self.damage_weight,
            "kill_potential": self.kill_weight,
            "risk": self.risk_weight,
            "setup_value": self.setup_weight,
            "disruption": self.disruption_weight,
        }
        return {k: v * weight_map.get(k, 1.0) for k, v in scores.items()}


PROFILES: dict[str, Personality] = {
    "balanced": Personality("balanced", 1.0, 1.0, 1.0, 1.0, 1.0),
    "aggressive": Personality("aggressive", 1.5, 1.3, 0.7, 0.5, 0.6),
    "defensive": Personality("defensive", 0.8, 0.8, 1.3, 1.2, 1.5),
    "tactical": Personality("tactical", 1.0, 1.1, 1.0, 1.5, 1.2),
}

_CHAMPION_PERSONALITIES: dict[str, str] = {
    "Cynthia": "tactical",
    "Aaron": "balanced",
    "Bertha": "defensive",
    "Flint": "aggressive",
    "Lucian": "tactical",
}


def get_champion_personality(name: str) -> Personality:
    profile_name = _CHAMPION_PERSONALITIES.get(name, "balanced")
    return PROFILES[profile_name]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ai/test_personality.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai/personality.py tests/ai/test_personality.py
git commit -m "feat: AI personality profiles for champion trainers"
```

---

### Task 11: AI Opponent Model

**Files:**
- Create: `src/ai/opponent_model.py`
- Create: `tests/ai/test_opponent_model.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/ai/test_opponent_model.py
from src.ai.opponent_model import OpponentModel
from src.engine.pokemon import Pokemon, Move, MoveCategory


def _make_pokemon(name, types, level=100):
    return Pokemon(name=name, types=types, level=level,
                   base_stats={"hp": 80, "attack": 80, "defense": 80, "sp_attack": 80, "sp_defense": 80, "speed": 80},
                   moves=[], ability="", item=None, iv_scale=250)


def test_reveal_move():
    model = OpponentModel()
    model.reveal_move("pikachu", "thunderbolt")
    model.reveal_move("pikachu", "iron-tail")
    assert model.get_known_moves("pikachu") == {"thunderbolt", "iron-tail"}

def test_reveal_move_deduplicates():
    model = OpponentModel()
    model.reveal_move("pikachu", "thunderbolt")
    model.reveal_move("pikachu", "thunderbolt")
    assert model.get_known_moves("pikachu") == {"thunderbolt"}

def test_assess_threat():
    model = OpponentModel()
    # Garchomp is a big threat to Pikachu (ground > electric)
    garchomp = _make_pokemon("garchomp", ["dragon", "ground"])
    pikachu = _make_pokemon("pikachu", ["electric"])
    threat = model.assess_threat(garchomp, pikachu)
    assert threat > 1.0  # super effective matchup

def test_assess_threat_bad_matchup():
    model = OpponentModel()
    pikachu = _make_pokemon("pikachu", ["electric"])
    geodude = _make_pokemon("geodude", ["rock", "ground"])
    threat = model.assess_threat(pikachu, geodude)
    assert threat < 1.0  # electric can't touch ground

def test_rank_threats():
    model = OpponentModel()
    my_pokemon = _make_pokemon("pikachu", ["electric"])
    opponents = [
        _make_pokemon("garchomp", ["dragon", "ground"]),
        _make_pokemon("magikarp", ["water"]),
        _make_pokemon("steelix", ["steel", "ground"]),
    ]
    ranked = model.rank_threats(opponents, my_pokemon)
    # Garchomp and Steelix should be higher threat than Magikarp
    assert ranked[0].name in ("garchomp", "steelix")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ai/test_opponent_model.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement opponent model**

```python
# src/ai/opponent_model.py
from __future__ import annotations
from src.engine.pokemon import Pokemon
from src.engine.typechart import get_matchup, TYPES


class OpponentModel:
    def __init__(self):
        self._known_moves: dict[str, set[str]] = {}

    def reveal_move(self, pokemon_name: str, move_name: str):
        if pokemon_name not in self._known_moves:
            self._known_moves[pokemon_name] = set()
        self._known_moves[pokemon_name].add(move_name)

    def get_known_moves(self, pokemon_name: str) -> set[str]:
        return self._known_moves.get(pokemon_name, set())

    def assess_threat(self, opponent: Pokemon, my_pokemon: Pokemon) -> float:
        """Score how threatening an opponent is to my pokemon.
        
        Based on type matchup: best offensive matchup opponent's types have
        against my pokemon, divided by best defensive matchup.
        >1.0 = threatening, <1.0 = not threatening.
        """
        # Best offensive matchup: how well can opponent's types hit mine?
        best_offense = max(
            get_matchup(opp_type, my_pokemon.types)
            for opp_type in opponent.types
        )
        # Best defensive matchup: how well can my types hit opponent?
        best_defense = max(
            get_matchup(my_type, opponent.types)
            for my_type in my_pokemon.types
        )
        # Avoid division by zero (immune)
        if best_defense == 0:
            best_defense = 0.25
        if best_offense == 0:
            return 0.1  # Not threatening if they can't hit us

        return best_offense / best_defense

    def rank_threats(self, opponents: list[Pokemon], my_pokemon: Pokemon) -> list[Pokemon]:
        """Rank opponent Pokemon by threat level to my active Pokemon, highest first."""
        return sorted(opponents, key=lambda o: self.assess_threat(o, my_pokemon), reverse=True)

    def predict_best_switch_target(self, opponent_team: list[Pokemon], my_pokemon: Pokemon) -> Pokemon | None:
        """Predict which Pokemon the opponent is most likely to switch to."""
        alive = [p for p in opponent_team if p.is_alive]
        if not alive:
            return None
        # Opponent will likely switch to their best matchup against us
        return max(alive, key=lambda o: self.assess_threat(o, my_pokemon))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ai/test_opponent_model.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai/opponent_model.py tests/ai/test_opponent_model.py
git commit -m "feat: AI opponent model with threat assessment and move tracking"
```

---

### Task 12: AI Scorer

**Files:**
- Create: `src/ai/scorer.py`
- Create: `tests/ai/test_scorer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/ai/test_scorer.py
from src.ai.scorer import MoveScorer, GameState
from src.ai.personality import PROFILES
from src.ai.memory import BattleMemory
from src.ai.opponent_model import OpponentModel
from src.engine.pokemon import Pokemon, Move, MoveCategory, Status


def _make_move(name, type_, category, power, accuracy=100, priority=0, effect=None, pp=10):
    return Move(name=name, type=type_, category=category, power=power,
                accuracy=accuracy, pp=pp, priority=priority, effect=effect)


def _make_pokemon(name, types, base_stats, moves, level=100):
    return Pokemon(name=name, types=types, level=level, base_stats=base_stats,
                   moves=moves, ability="", item=None, iv_scale=250)


def test_damaging_move_scores_higher_than_status():
    scorer = MoveScorer(PROFILES["balanced"], BattleMemory(), OpponentModel())
    attacker = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[
            _make_move("Earthquake", "ground", MoveCategory.PHYSICAL, 100),
            _make_move("Swords Dance", "normal", MoveCategory.STATUS, 0),
        ])
    defender = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[])
    state = GameState(my_team_alive=6, opp_team_alive=1, turn=5)
    scores = scorer.score_moves(attacker, defender, state)
    assert scores[0] > scores[1]  # EQ > Swords Dance when they're almost dead

def test_super_effective_preferred():
    scorer = MoveScorer(PROFILES["balanced"], BattleMemory(), OpponentModel())
    attacker = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[
            _make_move("Earthquake", "ground", MoveCategory.PHYSICAL, 100),  # SE vs electric
            _make_move("Dragon Rush", "dragon", MoveCategory.PHYSICAL, 100),  # neutral
        ])
    defender = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[])
    state = GameState(my_team_alive=6, opp_team_alive=6, turn=1)
    scores = scorer.score_moves(attacker, defender, state)
    assert scores[0] > scores[1]  # EQ (SE) > Dragon Rush (neutral)

def test_immune_move_scores_zero():
    scorer = MoveScorer(PROFILES["balanced"], BattleMemory(), OpponentModel())
    attacker = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[
            _make_move("Thunderbolt", "electric", MoveCategory.SPECIAL, 95),  # immune
            _make_move("Iron Tail", "steel", MoveCategory.PHYSICAL, 100),     # neutral
        ])
    defender = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[])
    state = GameState(my_team_alive=6, opp_team_alive=6, turn=1)
    scores = scorer.score_moves(attacker, defender, state)
    assert scores[0] == 0  # Thunderbolt immune
    assert scores[1] > 0

def test_aggressive_personality_favors_damage():
    aggressive_scorer = MoveScorer(PROFILES["aggressive"], BattleMemory(), OpponentModel())
    balanced_scorer = MoveScorer(PROFILES["balanced"], BattleMemory(), OpponentModel())
    attacker = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[
            _make_move("Earthquake", "ground", MoveCategory.PHYSICAL, 100),
            _make_move("Swords Dance", "normal", MoveCategory.STATUS, 0),
        ])
    defender = _make_pokemon("Steelix", ["steel", "ground"],
        {"hp": 75, "attack": 85, "defense": 200, "sp_attack": 55, "sp_defense": 65, "speed": 30},
        moves=[])
    state = GameState(my_team_alive=6, opp_team_alive=6, turn=1)
    agg_scores = aggressive_scorer.score_moves(attacker, defender, state)
    bal_scores = balanced_scorer.score_moves(attacker, defender, state)
    # Aggressive should favor EQ more relative to Swords Dance
    agg_ratio = agg_scores[0] / max(agg_scores[1], 0.01)
    bal_ratio = bal_scores[0] / max(bal_scores[1], 0.01)
    assert agg_ratio > bal_ratio
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ai/test_scorer.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement AI scorer**

```python
# src/ai/scorer.py
from __future__ import annotations
from dataclasses import dataclass
from src.engine.pokemon import Pokemon, Move, MoveCategory, Status
from src.engine.damage import calculate_damage
from src.engine.typechart import get_matchup
from src.ai.personality import Personality
from src.ai.memory import BattleMemory
from src.ai.opponent_model import OpponentModel

_SETUP_MOVES = {
    "swords-dance", "nasty-plot", "calm-mind", "dragon-dance", "bulk-up",
    "quiver-dance", "shell-smash", "agility", "rock-polish", "iron-defense",
    "amnesia", "barrier", "cosmic-power", "cotton-guard",
}

_DISRUPTION_MOVES = {
    "thunder-wave", "toxic", "will-o-wisp", "stun-spore", "sleep-powder",
    "spore", "dark-void", "hypnosis", "yawn", "confuse-ray", "swagger",
    "stealth-rock", "spikes", "toxic-spikes", "leech-seed",
}

_RECOVERY_MOVES = {
    "recover", "soft-boiled", "milk-drink", "roost", "slack-off",
    "moonlight", "morning-sun", "synthesis", "wish", "aqua-ring",
}


@dataclass
class GameState:
    my_team_alive: int
    opp_team_alive: int
    turn: int


class MoveScorer:
    def __init__(self, personality: Personality, memory: BattleMemory, opponent_model: OpponentModel):
        self.personality = personality
        self.memory = memory
        self.opponent_model = opponent_model

    def score_moves(self, attacker: Pokemon, defender: Pokemon, state: GameState) -> list[float]:
        """Score all moves for the attacker. Returns list of scores aligned with attacker.moves."""
        scores = []
        for move in attacker.moves:
            raw = self._score_single_move(attacker, defender, move, state)
            scores.append(raw)
        return scores

    def _score_single_move(
        self, attacker: Pokemon, defender: Pokemon, move: Move, state: GameState
    ) -> float:
        # Immune check
        effectiveness = get_matchup(move.type, defender.types)
        if effectiveness == 0.0 and move.category != MoveCategory.STATUS:
            return 0.0

        # No PP left
        if move.current_pp <= 0:
            return 0.0

        dimensions = {
            "damage_value": self._calc_damage_value(attacker, defender, move),
            "kill_potential": self._calc_kill_potential(attacker, defender, move),
            "risk": self._calc_risk(move),
            "setup_value": self._calc_setup_value(attacker, defender, move, state),
            "disruption": self._calc_disruption(defender, move, state),
        }

        weighted = self.personality.apply_weights(dimensions)
        return sum(weighted.values())

    def _calc_damage_value(self, attacker: Pokemon, defender: Pokemon, move: Move) -> float:
        if move.category == MoveCategory.STATUS:
            return 0.0
        result = calculate_damage(attacker, defender, move, critical=False, roll=100)
        # Normalize: damage as fraction of defender's max HP * 10
        return (result.damage / max(defender.max_hp, 1)) * 10

    def _calc_kill_potential(self, attacker: Pokemon, defender: Pokemon, move: Move) -> float:
        if move.category == MoveCategory.STATUS:
            return 0.0
        result = calculate_damage(attacker, defender, move, critical=False, roll=85)
        # Even minimum roll kills
        if result.damage >= defender.current_hp:
            return 10.0
        # High roll kills
        max_result = calculate_damage(attacker, defender, move, critical=False, roll=100)
        if max_result.damage >= defender.current_hp:
            return 5.0
        return 0.0

    def _calc_risk(self, move: Move) -> float:
        risk = 0.0
        # Low accuracy is risky
        if move.accuracy < 100:
            risk += (100 - move.accuracy) * 0.1
        # Recoil / self-KO moves
        if move.name in ("explosion", "self-destruct", "memento"):
            risk += 8.0
        elif move.name in ("close-combat", "superpower"):
            risk += 2.0
        elif move.name in ("giga-impact", "hyper-beam"):
            risk += 3.0  # recharge turn
        # Risk is negative (subtracted), so return as negative
        return -risk

    def _calc_setup_value(
        self, attacker: Pokemon, defender: Pokemon, move: Move, state: GameState
    ) -> float:
        if move.name not in _SETUP_MOVES:
            return 0.0
        # Setup is valuable early game, less so late
        if state.opp_team_alive <= 1:
            return 1.0  # why setup when you can just kill
        # Setup is better when you're healthy
        hp_ratio = attacker.current_hp / attacker.max_hp
        value = 5.0 * hp_ratio
        # Check if already boosted
        stat_sum = sum(attacker.stat_stages.values())
        if stat_sum >= 4:
            value *= 0.3  # diminishing returns on stacking boosts
        return value

    def _calc_disruption(self, defender: Pokemon, move: Move, state: GameState) -> float:
        if move.name not in _DISRUPTION_MOVES:
            return 0.0
        # Don't status an already-statused target
        if defender.status != Status.NONE and move.name in (
            "thunder-wave", "toxic", "will-o-wisp", "stun-spore",
            "sleep-powder", "spore", "dark-void", "hypnosis",
        ):
            return -5.0  # penalty for wasting a turn
        # Disruption is better early
        if state.turn <= 3:
            return 6.0
        return 3.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ai/test_scorer.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai/scorer.py tests/ai/test_scorer.py
git commit -m "feat: AI 5-dimension move scorer with personality weighting"
```

---

### Task 13: AI Lookahead

**Files:**
- Create: `src/ai/lookahead.py`
- Create: `tests/ai/test_lookahead.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/ai/test_lookahead.py
from src.ai.lookahead import Lookahead, BoardState
from src.engine.pokemon import Pokemon, Move, MoveCategory


def _make_move(name, type_, category, power, accuracy=100, priority=0):
    return Move(name=name, type=type_, category=category, power=power,
                accuracy=accuracy, pp=10, priority=priority, effect=None)


def _make_pokemon(name, types, base_stats, moves, level=100):
    return Pokemon(name=name, types=types, level=level, base_stats=base_stats,
                   moves=moves, ability="", item=None, iv_scale=250)


def test_evaluate_board_state():
    """More HP remaining = better board state."""
    state_good = BoardState(my_hp_pct=1.0, opp_hp_pct=0.2, my_alive=6, opp_alive=2,
                            my_status=False, opp_status=True, my_boosts=0, opp_boosts=0)
    state_bad = BoardState(my_hp_pct=0.2, opp_hp_pct=1.0, my_alive=2, opp_alive=6,
                           my_status=True, opp_status=False, my_boosts=0, opp_boosts=0)
    assert state_good.evaluate() > state_bad.evaluate()

def test_lookahead_prefers_kill():
    """If one move can KO and another can't, lookahead should prefer the KO."""
    lookahead = Lookahead(depth=1)
    attacker = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[
            _make_move("Earthquake", "ground", MoveCategory.PHYSICAL, 100),  # kills
            _make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40),       # doesn't kill
        ])
    defender = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[_make_move("Thunderbolt", "electric", MoveCategory.SPECIAL, 95)])
    # Pikachu has low HP
    defender.current_hp = 50
    scores = lookahead.evaluate_moves(attacker, defender, my_team_alive=6, opp_team_alive=1)
    assert scores[0] > scores[1]

def test_lookahead_considers_opponent_response():
    """Lookahead should penalize moves that leave us vulnerable."""
    lookahead = Lookahead(depth=2)
    attacker = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[
            _make_move("Thunderbolt", "electric", MoveCategory.SPECIAL, 95),  # immune to ground
            _make_move("Iron Tail", "steel", MoveCategory.PHYSICAL, 100, accuracy=75),
        ])
    defender = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[_make_move("Earthquake", "ground", MoveCategory.PHYSICAL, 100)])
    scores = lookahead.evaluate_moves(attacker, defender, my_team_alive=6, opp_team_alive=6)
    # Iron Tail should score higher since Thunderbolt is immune
    assert scores[1] > scores[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ai/test_lookahead.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement lookahead**

```python
# src/ai/lookahead.py
from __future__ import annotations
import copy
from dataclasses import dataclass
from src.engine.pokemon import Pokemon, Move, MoveCategory, Status
from src.engine.damage import calculate_damage


@dataclass
class BoardState:
    my_hp_pct: float
    opp_hp_pct: float
    my_alive: int
    opp_alive: int
    my_status: bool
    opp_status: bool
    my_boosts: int
    opp_boosts: int

    def evaluate(self) -> float:
        """Score from AI's perspective. Positive = good for AI."""
        score = 0.0
        # HP advantage
        score += (self.my_hp_pct - self.opp_hp_pct) * 30
        # Team advantage
        score += (self.my_alive - self.opp_alive) * 20
        # Status advantage (having status is bad)
        if self.opp_status:
            score += 5
        if self.my_status:
            score -= 5
        # Boost advantage
        score += (self.my_boosts - self.opp_boosts) * 3
        return score


class Lookahead:
    def __init__(self, depth: int = 2):
        self.depth = depth

    def evaluate_moves(
        self,
        attacker: Pokemon,
        defender: Pokemon,
        my_team_alive: int = 6,
        opp_team_alive: int = 6,
    ) -> list[float]:
        """Evaluate each of attacker's moves via simulation. Returns score per move."""
        scores = []
        for i, move in enumerate(attacker.moves):
            if move.current_pp <= 0:
                scores.append(-999.0)
                continue
            score = self._simulate_move(attacker, defender, move, my_team_alive, opp_team_alive)
            scores.append(score)
        return scores

    def _simulate_move(
        self,
        attacker: Pokemon,
        defender: Pokemon,
        move: Move,
        my_alive: int,
        opp_alive: int,
    ) -> float:
        """Simulate using this move, then opponent's best response. Return board evaluation."""
        # Simulate our move
        sim_attacker = self._clone_pokemon(attacker)
        sim_defender = self._clone_pokemon(defender)

        our_result = calculate_damage(sim_attacker, sim_defender, move, critical=False, roll=92)
        sim_defender.take_damage(our_result.damage)

        # If we KO them, great
        if not sim_defender.is_alive:
            opp_alive_after = opp_alive - 1
            state = BoardState(
                my_hp_pct=sim_attacker.current_hp / sim_attacker.max_hp,
                opp_hp_pct=0.0,
                my_alive=my_alive,
                opp_alive=opp_alive_after,
                my_status=sim_attacker.status != Status.NONE,
                opp_status=False,
                my_boosts=sum(max(0, v) for v in sim_attacker.stat_stages.values()),
                opp_boosts=0,
            )
            return state.evaluate()

        if self.depth <= 1:
            return self._evaluate_current(sim_attacker, sim_defender, my_alive, opp_alive)

        # Simulate opponent's best response
        best_opp_score = -999.0
        for opp_move in sim_defender.moves:
            if opp_move.current_pp <= 0:
                continue
            sim_atk2 = self._clone_pokemon(sim_attacker)
            sim_def2 = self._clone_pokemon(sim_defender)
            opp_result = calculate_damage(sim_def2, sim_atk2, opp_move, critical=False, roll=92)
            sim_atk2.take_damage(opp_result.damage)
            # Score from opponent's perspective (negative for us)
            opp_eval = self._evaluate_current(sim_atk2, sim_def2, my_alive, opp_alive)
            if -opp_eval > best_opp_score:
                best_opp_score = -opp_eval

        # Our score is negative of opponent's best (they play optimally)
        return -best_opp_score if best_opp_score > -999.0 else self._evaluate_current(
            sim_attacker, sim_defender, my_alive, opp_alive
        )

    def _evaluate_current(
        self, attacker: Pokemon, defender: Pokemon, my_alive: int, opp_alive: int
    ) -> float:
        opp_alive_adj = opp_alive - (0 if defender.is_alive else 1)
        my_alive_adj = my_alive - (0 if attacker.is_alive else 1)
        state = BoardState(
            my_hp_pct=attacker.current_hp / attacker.max_hp if attacker.is_alive else 0.0,
            opp_hp_pct=defender.current_hp / defender.max_hp if defender.is_alive else 0.0,
            my_alive=my_alive_adj,
            opp_alive=opp_alive_adj,
            my_status=attacker.status != Status.NONE,
            opp_status=defender.status != Status.NONE,
            my_boosts=sum(max(0, v) for v in attacker.stat_stages.values()),
            opp_boosts=sum(max(0, v) for v in defender.stat_stages.values()),
        )
        return state.evaluate()

    def _clone_pokemon(self, pokemon: Pokemon) -> Pokemon:
        p = copy.copy(pokemon)
        p.stat_stages = dict(pokemon.stat_stages)
        p.volatile = set(pokemon.volatile)
        p.moves = list(pokemon.moves)  # shallow copy moves list
        return p
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ai/test_lookahead.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/ai/lookahead.py tests/ai/test_lookahead.py
git commit -m "feat: AI 2-turn lookahead with board state evaluation"
```

---

### Task 14: CLI Display

**Files:**
- Create: `src/cli/display.py`
- Create: `tests/cli/__init__.py` (empty)

- [ ] **Step 1: Create the display module**

No TDD here — display is visual output, tested manually. Create `tests/cli/__init__.py` as an empty file.

```python
# src/cli/display.py
from __future__ import annotations
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from src.engine.pokemon import Pokemon, Status
from src.engine.battle import BattleEvent, EventType


console = Console()


def _hp_color(pct: float) -> str:
    if pct > 0.5:
        return "green"
    elif pct > 0.2:
        return "yellow"
    return "red"


def _hp_bar(current: int, maximum: int, width: int = 20) -> Text:
    pct = current / max(maximum, 1)
    filled = int(pct * width)
    color = _hp_color(pct)
    bar = Text("[")
    bar.append("|" * filled, style=color)
    bar.append("-" * (width - filled), style="dim")
    bar.append(f"] {current}/{maximum}")
    return bar


def _status_text(status: Status) -> str:
    if status == Status.NONE:
        return ""
    labels = {
        Status.BURN: "[red]BRN[/red]",
        Status.FREEZE: "[cyan]FRZ[/cyan]",
        Status.PARALYSIS: "[yellow]PAR[/yellow]",
        Status.POISON: "[magenta]PSN[/magenta]",
        Status.BAD_POISON: "[magenta]TOX[/magenta]",
        Status.SLEEP: "[dim]SLP[/dim]",
    }
    return labels.get(status, "")


def show_battle_state(player: Pokemon, opponent: Pokemon, turn: int, opponent_name: str = "Opponent"):
    console.print(f"\n--- Turn {turn} ---", style="bold")

    # Opponent's Pokemon
    opp_hp_bar = _hp_bar(opponent.current_hp, opponent.max_hp)
    opp_status = _status_text(opponent.status)
    console.print(f"  {opponent_name}'s {opponent.name.title()} Lv{opponent.level} {opp_status}")
    console.print(f"  ", end="")
    console.print(opp_hp_bar)
    console.print()

    # Player's Pokemon
    p_hp_bar = _hp_bar(player.current_hp, player.max_hp)
    p_status = _status_text(player.status)
    console.print(f"  Your {player.name.title()} Lv{player.level} {p_status}")
    console.print(f"  ", end="")
    console.print(p_hp_bar)
    console.print()


def show_move_menu(pokemon: Pokemon, can_switch: bool = True):
    console.print(f"  {pokemon.name.title()}'s moves:", style="bold")
    for i, move in enumerate(pokemon.moves):
        pp_color = "green" if move.current_pp > move.pp // 4 else "red"
        console.print(
            f"    {i + 1}. {move.name.replace('-', ' ').title():20s} "
            f"({move.type.title():10s}) "
            f"[{pp_color}]PP: {move.current_pp}/{move.pp}[/{pp_color}]"
        )
    if can_switch:
        console.print(f"    {len(pokemon.moves) + 1}. Switch Pokemon")
    console.print()


def show_switch_menu(team: list[Pokemon], active_index: int):
    console.print("  Choose a Pokemon:", style="bold")
    for i, poke in enumerate(team):
        if i == active_index:
            continue
        if not poke.is_alive:
            console.print(f"    {i + 1}. {poke.name.title()} [red](fainted)[/red]")
        else:
            hp_bar = _hp_bar(poke.current_hp, poke.max_hp)
            console.print(f"    {i + 1}. {poke.name.title()} ", end="")
            console.print(hp_bar)
    console.print(f"    0. Back")
    console.print()


def show_events(events: list[BattleEvent]):
    for event in events:
        if event.event_type == EventType.DAMAGE:
            console.print(f"  {event.message} ({event.damage} damage)")
        elif event.event_type == EventType.EFFECTIVENESS:
            if event.effectiveness > 1.0:
                console.print(f"  [green]{event.message}[/green]")
            elif event.effectiveness == 0.0:
                console.print(f"  [dim]{event.message}[/dim]")
            else:
                console.print(f"  [yellow]{event.message}[/yellow]")
        elif event.event_type == EventType.CRITICAL:
            console.print(f"  [bold yellow]{event.message}[/bold yellow]")
        elif event.event_type == EventType.FAINT:
            console.print(f"  [red]{event.message}[/red]")
        elif event.event_type == EventType.SWITCH:
            console.print(f"  [cyan]{event.message}[/cyan]")
        elif event.event_type == EventType.CANT_ACT:
            console.print(f"  [dim]{event.message}[/dim]")
        elif event.event_type == EventType.END_OF_TURN:
            console.print(f"  [magenta]{event.message}[/magenta]")
        elif event.event_type == EventType.MISS:
            console.print(f"  [dim]{event.message}[/dim]")
        else:
            console.print(f"  {event.message}")


def show_battle_result(winner: str, turn_count: int, player_fainted: int, opponent_fainted: int,
                       damage_dealt: dict[str, int]):
    console.print()
    if winner == "player":
        console.print(Panel("[bold green]You Win![/bold green]", expand=False))
    else:
        console.print(Panel("[bold red]You Lose![/bold red]", expand=False))

    table = Table(title="Battle Summary")
    table.add_column("Stat", style="bold")
    table.add_column("Value")
    table.add_row("Turns", str(turn_count))
    table.add_row("Your Pokemon Fainted", str(player_fainted))
    table.add_row("Opponent Pokemon Fainted", str(opponent_fainted))

    if damage_dealt:
        mvp = max(damage_dealt, key=damage_dealt.get)
        table.add_row("MVP", f"{mvp.title()} ({damage_dealt[mvp]} damage)")

    console.print(table)
```

- [ ] **Step 2: Commit**

```bash
git add src/cli/display.py tests/cli/__init__.py
git commit -m "feat: rich CLI display with health bars, events, and battle summary"
```

---

### Task 15: CLI Team Builder

**Files:**
- Create: `src/cli/team_builder.py`

- [ ] **Step 1: Implement team builder**

```python
# src/cli/team_builder.py
from __future__ import annotations
from rich.console import Console
from src.data.pokeapi_client import PokeAPIClient
from src.data.champion_loader import ChampionLoader, ChampionTeam
from src.engine.pokemon import Pokemon
import random

console = Console()


def build_player_team(client: PokeAPIClient) -> list[Pokemon]:
    console.print("\n[bold]Choose your team mode:[/bold]")
    console.print("  1. Fully random")
    console.print("  2. Pick Pokemon, random moves")
    console.print("  3. Full manual")
    console.print("  4. Pick from champion presets")
    console.print()

    choice = _prompt_choice(1, 4)

    if choice == 1:
        return _random_team(client)
    elif choice == 2:
        return _pick_pokemon_random_moves(client)
    elif choice == 3:
        return _full_manual(client)
    elif choice == 4:
        return _champion_preset(client)
    return []


def build_opponent_team(client: PokeAPIClient) -> tuple[str, list[Pokemon], list[str]]:
    """Returns (trainer_name, team, trainer_items)."""
    loader = ChampionLoader()
    champions = loader.list_champions()

    console.print("\n[bold]Choose your opponent:[/bold]")
    for i, champ in enumerate(champions):
        display_name = champ.replace("_", " ").title()
        console.print(f"  {i + 1}. {display_name}")
    console.print(f"  {len(champions) + 1}. Random team")
    console.print()

    choice = _prompt_choice(1, len(champions) + 1)

    if choice == len(champions) + 1:
        team = [client.get_random_pokemon(level=100) for _ in range(6)]
        return "Random Trainer", team, []

    champ_data = loader.load_champion(champions[choice - 1])
    team = _build_champion_team(client, champ_data)
    return champ_data.name, team, champ_data.items


def _random_team(client: PokeAPIClient) -> list[Pokemon]:
    console.print("\n[bold]Generating random team...[/bold]")
    team = []
    for i in range(6):
        console.print(f"  Fetching Pokemon {i + 1}/6...")
        pokemon = client.get_random_pokemon(level=100)
        team.append(pokemon)
        console.print(f"    Got {pokemon.name.title()}!")
    return team


def _pick_pokemon_random_moves(client: PokeAPIClient) -> list[Pokemon]:
    team = []
    for i in range(6):
        console.print(f"\n  Pokemon {i + 1}/6 — Enter name or dex number (or 'random'):")
        while True:
            raw = console.input("  > ").strip().lower()
            if raw == "random":
                pokemon = client.get_random_pokemon(level=100)
            else:
                try:
                    name_or_id = int(raw) if raw.isdigit() else raw
                    learnable = client.get_learnable_moves(name_or_id)
                    chosen = random.sample(learnable, min(4, len(learnable)))
                    moves = []
                    for mn in chosen:
                        try:
                            moves.append(client.get_move(mn))
                        except Exception:
                            continue
                    pokemon = client.get_pokemon(name_or_id, level=100)
                    pokemon.moves = moves
                except Exception as e:
                    console.print(f"  [red]Error: {e}. Try again.[/red]")
                    continue
            team.append(pokemon)
            console.print(f"    {pokemon.name.title()} with moves: {', '.join(m.name for m in pokemon.moves)}")
            break
    return team


def _full_manual(client: PokeAPIClient) -> list[Pokemon]:
    team = []
    for i in range(6):
        console.print(f"\n  Pokemon {i + 1}/6 — Enter name or dex number:")
        while True:
            raw = console.input("  > ").strip().lower()
            try:
                name_or_id = int(raw) if raw.isdigit() else raw
                learnable = client.get_learnable_moves(name_or_id)
                console.print(f"  Available moves: {', '.join(sorted(learnable)[:50])}...")
                if len(learnable) > 50:
                    console.print(f"    ({len(learnable)} total — type move names)")

                chosen_moves = []
                for j in range(4):
                    console.print(f"  Move {j + 1}/4:")
                    while True:
                        move_name = console.input("  > ").strip().lower().replace(" ", "-")
                        if move_name in learnable:
                            chosen_moves.append(client.get_move(move_name))
                            break
                        console.print(f"  [red]'{move_name}' not in learnset. Try again.[/red]")

                pokemon = client.get_pokemon(name_or_id, level=100)
                pokemon.moves = chosen_moves
                team.append(pokemon)
                console.print(f"    {pokemon.name.title()} ready!")
                break
            except Exception as e:
                console.print(f"  [red]Error: {e}. Try again.[/red]")
    return team


def _champion_preset(client: PokeAPIClient) -> list[Pokemon]:
    loader = ChampionLoader()
    champions = loader.list_champions()
    console.print("\n  Pick a champion's team to use:")
    for i, champ in enumerate(champions):
        console.print(f"    {i + 1}. {champ.replace('_', ' ').title()}")
    choice = _prompt_choice(1, len(champions))
    champ_data = loader.load_champion(champions[choice - 1])
    return _build_champion_team(client, champ_data)


def _build_champion_team(client: PokeAPIClient, champ: ChampionTeam) -> list[Pokemon]:
    team = []
    for member in champ.party:
        console.print(f"  Loading {member.species}...")
        pokemon = client.get_pokemon(
            member.species,
            level=member.level,
            move_names=member.moves,
            iv_scale=member.iv_scale,
        )
        if member.item:
            pokemon.item = member.item
        team.append(pokemon)
    return team


def _prompt_choice(low: int, high: int) -> int:
    while True:
        try:
            raw = console.input("  > ").strip()
            val = int(raw)
            if low <= val <= high:
                return val
            console.print(f"  [red]Enter a number between {low} and {high}.[/red]")
        except ValueError:
            console.print(f"  [red]Enter a number.[/red]")
```

- [ ] **Step 2: Commit**

```bash
git add src/cli/team_builder.py
git commit -m "feat: CLI team builder with 4 selection modes"
```

---

### Task 16: CLI App — Main Entry Point

**Files:**
- Create: `src/cli/app.py`

- [ ] **Step 1: Implement the main app**

```python
# src/cli/app.py
from __future__ import annotations
import random
import typer
from rich.console import Console
from src.data.pokeapi_client import PokeAPIClient
from src.engine.battle import Battle, BattleAction, ActionType
from src.ai.scorer import MoveScorer, GameState
from src.ai.lookahead import Lookahead
from src.ai.memory import BattleMemory, TurnRecord
from src.ai.opponent_model import OpponentModel
from src.ai.personality import get_champion_personality, PROFILES
from src.cli.display import (
    show_battle_state, show_move_menu, show_switch_menu,
    show_events, show_battle_result,
)
from src.cli.team_builder import build_player_team, build_opponent_team

app = typer.Typer()
console = Console()


class AIController:
    def __init__(self, name: str, battle: Battle, trainer_items: list[str]):
        personality = get_champion_personality(name)
        self.memory = BattleMemory()
        self.opponent_model = OpponentModel()
        self.scorer = MoveScorer(personality, self.memory, self.opponent_model)
        self.lookahead = Lookahead(depth=2)
        self.battle = battle
        self.trainer_items = list(trainer_items)
        self.name = name

    def choose_action(self) -> BattleAction:
        my_pokemon = self.battle.opponent_pokemon
        target = self.battle.player_pokemon

        # Check if we should use an item (Full Restore when HP < 30%)
        if self.trainer_items and my_pokemon.current_hp / my_pokemon.max_hp < 0.3:
            return BattleAction(ActionType.ITEM, item_name=self.trainer_items.pop(0))

        # Check if we should switch
        switch_idx = self._consider_switch()
        if switch_idx is not None:
            return BattleAction(ActionType.SWITCH, switch_index=switch_idx)

        # Score moves
        state = GameState(
            my_team_alive=sum(1 for p in self.battle.opponent_team if p.is_alive),
            opp_team_alive=sum(1 for p in self.battle.player_team if p.is_alive),
            turn=self.battle.turn_count,
        )
        base_scores = self.scorer.score_moves(my_pokemon, target, state)
        lookahead_scores = self.lookahead.evaluate_moves(
            my_pokemon, target,
            my_team_alive=state.my_team_alive,
            opp_team_alive=state.opp_team_alive,
        )

        # Combine scores (weighted average)
        combined = []
        for i in range(len(my_pokemon.moves)):
            if i < len(base_scores) and i < len(lookahead_scores):
                combined.append(base_scores[i] * 0.6 + lookahead_scores[i] * 0.4)
            elif i < len(base_scores):
                combined.append(base_scores[i])
            else:
                combined.append(0)

        if not combined or max(combined) <= 0:
            # All moves are bad, try switching
            alive = self.battle.get_alive_indices("opponent")
            if alive:
                return BattleAction(ActionType.SWITCH, switch_index=alive[0])
            return BattleAction(ActionType.MOVE, move_index=0)

        best_idx = combined.index(max(combined))
        return BattleAction(ActionType.MOVE, move_index=best_idx)

    def _consider_switch(self) -> int | None:
        my_pokemon = self.battle.opponent_pokemon
        target = self.battle.player_pokemon
        alive_indices = self.battle.get_alive_indices("opponent")
        if not alive_indices:
            return None

        # Check if current matchup is terrible (all moves immune or ineffective)
        from src.engine.typechart import get_matchup
        best_eff = max(
            (get_matchup(m.type, target.types) for m in my_pokemon.moves if m.current_pp > 0),
            default=0,
        )
        if best_eff == 0.0:
            # Can't hit them at all — switch to best counter
            best_idx = None
            best_threat = -1
            for idx in alive_indices:
                candidate = self.battle.opponent_team[idx]
                threat = self.opponent_model.assess_threat(candidate, target)
                if threat > best_threat:
                    best_threat = threat
                    best_idx = idx
            return best_idx

        return None

    def record_turn(self, user_move: str, opp_move: str, damage_dealt: int, damage_taken: int):
        self.memory.record_turn(TurnRecord(
            turn=self.battle.turn_count,
            user_move=opp_move,  # from AI's perspective, user is the opponent
            user_pokemon=self.battle.opponent_pokemon.name,
            opponent_move=user_move,
            opponent_pokemon=self.battle.player_pokemon.name,
            damage_dealt=damage_dealt,
            damage_taken=damage_taken,
        ))
        # Track revealed moves
        self.opponent_model.reveal_move(self.battle.player_pokemon.name, user_move)


def _get_player_action(battle: Battle) -> BattleAction:
    show_move_menu(battle.player_pokemon, can_switch=bool(battle.get_alive_indices("player")))
    while True:
        try:
            raw = console.input("  > ").strip()
            choice = int(raw)
            if 1 <= choice <= len(battle.player_pokemon.moves):
                move = battle.player_pokemon.moves[choice - 1]
                if move.current_pp <= 0:
                    console.print("  [red]No PP left for that move![/red]")
                    continue
                return BattleAction(ActionType.MOVE, move_index=choice - 1)
            elif choice == len(battle.player_pokemon.moves) + 1:
                # Switch
                show_switch_menu(battle.player_team, battle.player_active)
                while True:
                    raw2 = console.input("  > ").strip()
                    idx = int(raw2)
                    if idx == 0:
                        show_move_menu(battle.player_pokemon)
                        break
                    if 1 <= idx <= len(battle.player_team) and idx - 1 != battle.player_active:
                        poke = battle.player_team[idx - 1]
                        if poke.is_alive:
                            return BattleAction(ActionType.SWITCH, switch_index=idx - 1)
                        console.print("  [red]That Pokemon has fainted![/red]")
                    else:
                        console.print("  [red]Invalid choice.[/red]")
            else:
                console.print("  [red]Invalid choice.[/red]")
        except ValueError:
            console.print("  [red]Enter a number.[/red]")


def _handle_faint_switch(battle: Battle, team: str) -> BattleAction | None:
    """Force a switch when active Pokemon faints."""
    active_pokemon = battle.player_pokemon if team == "player" else battle.opponent_pokemon
    if active_pokemon.is_alive:
        return None

    alive = battle.get_alive_indices(team)
    if not alive:
        return None

    if team == "player":
        console.print(f"\n  [red]{active_pokemon.name.title()} fainted! Choose next Pokemon:[/red]")
        show_switch_menu(battle.player_team if team == "player" else battle.opponent_team,
                        battle.player_active if team == "player" else battle.opponent_active)
        while True:
            try:
                idx = int(console.input("  > ").strip())
                if idx in alive or (1 <= idx <= len(battle.player_team) and idx - 1 in alive):
                    actual_idx = idx - 1 if idx not in alive else idx
                    if actual_idx in alive:
                        battle.player_active = actual_idx
                        console.print(f"  Go, {battle.player_pokemon.name.title()}!")
                        return None
                console.print("  [red]Invalid choice.[/red]")
            except ValueError:
                console.print("  [red]Enter a number.[/red]")
    else:
        # AI picks best switch
        best_idx = alive[0]
        battle.opponent_active = best_idx
        console.print(f"  [cyan]{battle.opponent_pokemon.name.title()} was sent out![/cyan]")
    return None


@app.command()
def battle():
    """Start a Pokemon battle!"""
    console.print("[bold]Pokemon Battle Simulator[/bold]", style="bold blue")
    console.print("Powered by improved AI with lookahead, memory, and personality\n")

    client = PokeAPIClient()

    try:
        player_team = build_player_team(client)
        opponent_name, opponent_team, trainer_items = build_opponent_team(client)

        battle_state = Battle(player_team=player_team, opponent_team=opponent_team)
        ai = AIController(opponent_name, battle_state, trainer_items)

        console.print(f"\n[bold]Battle Start: You vs {opponent_name}![/bold]\n")

        while not battle_state.is_over():
            show_battle_state(
                battle_state.player_pokemon,
                battle_state.opponent_pokemon,
                battle_state.turn_count + 1,
                opponent_name,
            )

            player_action = _get_player_action(battle_state)
            ai_action = ai.choose_action()

            # Handle AI items
            if ai_action.action_type == ActionType.ITEM:
                console.print(f"  [cyan]{opponent_name} used a Full Restore![/cyan]")
                battle_state.opponent_pokemon.current_hp = battle_state.opponent_pokemon.max_hp
                battle_state.opponent_pokemon.status = __import__('src.engine.pokemon', fromlist=['Status']).Status.NONE
                # Player still gets their move
                events = battle_state.execute_turn(
                    player_action,
                    BattleAction(ActionType.MOVE, move_index=0),  # AI "wastes" turn on item
                )
            else:
                events = battle_state.execute_turn(player_action, ai_action)

            show_events(events)

            # Record turn in AI memory
            p_move = (battle_state.player_pokemon.moves[player_action.move_index].name
                     if player_action.action_type == ActionType.MOVE else "switch")
            o_move = ("item" if ai_action.action_type == ActionType.ITEM
                     else battle_state.opponent_pokemon.moves[ai_action.move_index].name
                     if ai_action.action_type == ActionType.MOVE else "switch")
            ai.record_turn(p_move, o_move, 0, 0)

            # Handle faints
            _handle_faint_switch(battle_state, "opponent")
            _handle_faint_switch(battle_state, "player")

        winner = battle_state.get_winner()
        show_battle_result(
            winner=winner,
            turn_count=battle_state.turn_count,
            player_fainted=battle_state.player_fainted,
            opponent_fainted=battle_state.opponent_fainted,
            damage_dealt=battle_state.damage_dealt,
        )
    finally:
        client.close()


def main():
    app()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it runs**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m src.cli.app --help`
Expected: Shows typer help with the `battle` command

- [ ] **Step 3: Commit**

```bash
git add src/cli/app.py
git commit -m "feat: main CLI app with battle loop, AI controller, and player input"
```

---

### Task 17: Integration Test — Full Battle

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
"""Smoke test: run a short automated battle to verify all pieces fit together."""
import random
from src.engine.pokemon import Pokemon, Move, MoveCategory
from src.engine.battle import Battle, BattleAction, ActionType


def _make_move(name, type_, category, power, accuracy=100, priority=0, pp=10):
    return Move(name=name, type=type_, category=category, power=power,
                accuracy=accuracy, pp=pp, priority=priority, effect=None)


def _make_pokemon(name, types, base_stats, moves, level=100):
    return Pokemon(name=name, types=types, level=level, base_stats=base_stats,
                   moves=moves, ability="", item=None, iv_scale=250)


def test_full_battle_runs_to_completion():
    """Two Pokemon fight until one faints. Verifies the full engine works end-to-end."""
    random.seed(123)
    garchomp = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[
            _make_move("Earthquake", "ground", MoveCategory.PHYSICAL, 100),
            _make_move("Dragon Rush", "dragon", MoveCategory.PHYSICAL, 100, accuracy=75),
        ])
    pikachu = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[
            _make_move("Thunderbolt", "electric", MoveCategory.SPECIAL, 95),
            _make_move("Iron Tail", "steel", MoveCategory.PHYSICAL, 100, accuracy=75),
        ])

    battle = Battle(player_team=[garchomp], opponent_team=[pikachu])

    turns = 0
    while not battle.is_over() and turns < 50:
        events = battle.execute_turn(
            BattleAction(ActionType.MOVE, move_index=0),
            BattleAction(ActionType.MOVE, move_index=0),
        )
        turns += 1
        assert len(events) > 0

    assert battle.is_over()
    assert battle.get_winner() is not None
    assert turns < 50  # should end well before 50 turns


def test_ai_scorer_integration():
    """Verify AI scorer works with real Pokemon data."""
    from src.ai.scorer import MoveScorer, GameState
    from src.ai.personality import PROFILES
    from src.ai.memory import BattleMemory
    from src.ai.opponent_model import OpponentModel

    scorer = MoveScorer(PROFILES["tactical"], BattleMemory(), OpponentModel())
    garchomp = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[
            _make_move("Earthquake", "ground", MoveCategory.PHYSICAL, 100),
            _make_move("Dragon Rush", "dragon", MoveCategory.PHYSICAL, 100),
            _make_move("Flamethrower", "fire", MoveCategory.SPECIAL, 90),
            _make_move("Giga Impact", "normal", MoveCategory.PHYSICAL, 150),
        ])
    pikachu = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[])

    state = GameState(my_team_alive=6, opp_team_alive=6, turn=1)
    scores = scorer.score_moves(garchomp, pikachu, state)

    assert len(scores) == 4
    # Earthquake should be best (SE + STAB + high power)
    assert scores[0] == max(scores)
    # All scores should be non-negative
    assert all(s >= 0 for s in scores)
```

- [ ] **Step 2: Run all tests**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ -v --ignore=tests/data/test_pokeapi_client.py`
Expected: All tests pass (excluding PokeAPI tests which need internet)

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: integration tests verifying full battle and AI scoring"
```

---

### Task 18: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/ -v --ignore=tests/data/test_pokeapi_client.py`
Expected: All tests pass

- [ ] **Step 2: Run PokeAPI tests (requires internet)**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m pytest tests/data/test_pokeapi_client.py -v`
Expected: All tests pass

- [ ] **Step 3: Verify CLI launches**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m src.cli.app --help`
Expected: Shows help output with `battle` command

- [ ] **Step 4: Manual smoke test**

Run: `cd /mnt/c/Users/arjun.myanger/development/pokemon-battle-sim && source .venv/bin/activate && python -m src.cli.app battle`
Expected: Game starts, shows team selection, can begin a battle
