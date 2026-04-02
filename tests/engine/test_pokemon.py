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
    assert pokemon.stats["speed"] == 240

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
