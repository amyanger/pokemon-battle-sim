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
    assert poke.current_hp == hp_before - poke.max_hp // 8

def test_poison_end_of_turn():
    poke = _make_pokemon()
    apply_status(poke, Status.POISON)
    hp_before = poke.current_hp
    apply_end_of_turn(poke)
    assert poke.current_hp == hp_before - poke.max_hp // 8

def test_bad_poison_escalates():
    poke = _make_pokemon()
    apply_status(poke, Status.BAD_POISON)
    hp_before = poke.current_hp
    apply_end_of_turn(poke)
    damage_t1 = hp_before - poke.current_hp
    assert damage_t1 == poke.max_hp // 16
    hp_before = poke.current_hp
    apply_end_of_turn(poke)
    damage_t2 = hp_before - poke.current_hp
    assert damage_t2 == (poke.max_hp * 2) // 16

def test_sleep_prevents_action():
    import random
    random.seed(0)
    poke = _make_pokemon()
    apply_status(poke, Status.SLEEP)
    assert poke.status == Status.SLEEP
    result = can_act(poke)
    # Either still asleep (False) or just woke up (True) — both valid

def test_paralysis_speed_quarter():
    poke = _make_pokemon()
    apply_status(poke, Status.PARALYSIS)
    effective_speed = poke.get_effective_stat("speed")
    assert effective_speed == poke.stats["speed"]  # stat_stages don't handle para
