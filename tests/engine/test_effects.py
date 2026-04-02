import random
from src.engine.pokemon import Pokemon, Move, MoveCategory, Status
from src.engine.moves import apply_move_effects


def _make_pokemon(name="Pikachu", types=None, level=100, hp=200):
    return Pokemon(
        name=name, types=types or ["normal"], level=level,
        base_stats={"hp": hp, "attack": 100, "defense": 100, "sp_attack": 100, "sp_defense": 100, "speed": 100},
        moves=[], ability="", item=None, iv_scale=250,
    )


def _make_move(name="test-move", type_="normal", category=MoveCategory.PHYSICAL,
               power=80, accuracy=100, pp=10, priority=0, effect=None, **kwargs):
    return Move(name=name, type=type_, category=category, power=power,
                accuracy=accuracy, pp=pp, priority=priority, effect=effect, **kwargs)


# --- Status ailment tests ---

def test_status_move_inflicts_paralysis():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("thunder-wave", category=MoveCategory.STATUS, power=0,
                      ailment="paralysis", ailment_chance=0)  # 0 = guaranteed
    events = apply_move_effects(attacker, target, move, 0)
    assert target.status == Status.PARALYSIS
    assert any("paralysis" in msg for _, msg in events)


def test_status_move_inflicts_burn():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("will-o-wisp", category=MoveCategory.STATUS, power=0,
                      ailment="burn", ailment_chance=0)
    events = apply_move_effects(attacker, target, move, 0)
    assert target.status == Status.BURN


def test_status_move_inflicts_sleep():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("spore", category=MoveCategory.STATUS, power=0,
                      ailment="sleep", ailment_chance=0)
    events = apply_move_effects(attacker, target, move, 0)
    assert target.status == Status.SLEEP
    assert any("fell asleep" in msg for _, msg in events)


def test_toxic_inflicts_bad_poison():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("toxic", category=MoveCategory.STATUS, power=0,
                      ailment="poison", ailment_chance=0)
    events = apply_move_effects(attacker, target, move, 0)
    assert target.status == Status.BAD_POISON
    assert any("badly poisoned" in msg for _, msg in events)


def test_status_blocked_if_already_statused():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    target.status = Status.BURN
    move = _make_move("thunder-wave", category=MoveCategory.STATUS, power=0,
                      ailment="paralysis", ailment_chance=0)
    events = apply_move_effects(attacker, target, move, 0)
    assert target.status == Status.BURN  # unchanged
    assert len(events) == 0


def test_secondary_status_chance_roll():
    random.seed(42)
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("flamethrower", power=90, ailment="burn", ailment_chance=10)
    # Run many times to verify it's probabilistic
    burn_count = 0
    for _ in range(100):
        target.status = Status.NONE
        apply_move_effects(attacker, target, move, 50)
        if target.status == Status.BURN:
            burn_count += 1
    assert 0 < burn_count < 100  # should hit sometimes but not always


# --- Confusion test ---

def test_confusion_added_to_volatile():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("confuse-ray", category=MoveCategory.STATUS, power=0,
                      ailment="confusion", ailment_chance=0)
    apply_move_effects(attacker, target, move, 0)
    assert "confusion" in target.volatile


# --- Stat change tests ---

def test_swords_dance_raises_user_attack():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("swords-dance", category=MoveCategory.STATUS, power=0,
                      stat_changes=[("attack", 2)], stat_change_target="auto")
    events = apply_move_effects(attacker, target, move, 0)
    assert attacker.stat_stages["attack"] == 2
    assert any("Attack rose" in msg for _, msg in events)


def test_growl_lowers_target_attack():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("growl", category=MoveCategory.STATUS, power=0,
                      stat_changes=[("attack", -1)], stat_change_target="auto")
    events = apply_move_effects(attacker, target, move, 0)
    assert target.stat_stages["attack"] == -1
    assert any("Attack fell" in msg for _, msg in events)


def test_close_combat_self_debuff():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("close-combat", power=120,
                      stat_changes=[("defense", -1), ("sp_defense", -1)],
                      stat_change_target="user", stat_chance=0)
    events = apply_move_effects(attacker, target, move, 80)
    assert attacker.stat_stages["defense"] == -1
    assert attacker.stat_stages["sp_defense"] == -1


def test_energy_ball_lowers_target_spdef():
    random.seed(0)  # ensure the 10% triggers
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("energy-ball", power=90,
                      stat_changes=[("sp_defense", -1)],
                      stat_change_target="target", stat_chance=10)
    # Run until we get at least one proc
    proc_count = 0
    for _ in range(200):
        target.stat_stages["sp_defense"] = 0
        apply_move_effects(attacker, target, move, 50)
        if target.stat_stages["sp_defense"] == -1:
            proc_count += 1
    assert proc_count > 0  # should proc at least once in 200 tries


def test_stat_change_capped_at_6():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    attacker.stat_stages["attack"] = 5
    move = _make_move("swords-dance", category=MoveCategory.STATUS, power=0,
                      stat_changes=[("attack", 2)], stat_change_target="auto")
    apply_move_effects(attacker, target, move, 0)
    assert attacker.stat_stages["attack"] == 6  # capped


# --- Drain and recoil tests ---

def test_drain_heals_attacker():
    attacker = _make_pokemon("Attacker")
    attacker.current_hp = attacker.max_hp // 2
    target = _make_pokemon("Target")
    move = _make_move("giga-drain", power=75, drain=50)
    hp_before = attacker.current_hp
    events = apply_move_effects(attacker, target, move, 100)
    assert attacker.current_hp == hp_before + 50  # 50% of 100 damage
    assert any("drained" in msg for _, msg in events)


def test_recoil_damages_attacker():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("double-edge", power=120, drain=-33)
    hp_before = attacker.current_hp
    events = apply_move_effects(attacker, target, move, 100)
    assert attacker.current_hp == hp_before - 33  # 33% of 100 damage
    assert any("recoil" in msg for _, msg in events)


def test_no_drain_on_zero_damage():
    attacker = _make_pokemon("Attacker")
    attacker.current_hp = attacker.max_hp // 2
    target = _make_pokemon("Target")
    move = _make_move("giga-drain", power=75, drain=50)
    hp_before = attacker.current_hp
    apply_move_effects(attacker, target, move, 0)
    assert attacker.current_hp == hp_before  # no heal on 0 damage


# --- Healing tests ---

def test_recover_heals_half_hp():
    attacker = _make_pokemon("Attacker")
    attacker.current_hp = 1
    target = _make_pokemon("Target")
    move = _make_move("recover", category=MoveCategory.STATUS, power=0, healing=50)
    events = apply_move_effects(attacker, target, move, 0)
    assert attacker.current_hp > 1
    assert any("restored" in msg for _, msg in events)


def test_heal_capped_at_max_hp():
    attacker = _make_pokemon("Attacker")
    attacker.current_hp = attacker.max_hp - 1
    target = _make_pokemon("Target")
    move = _make_move("recover", category=MoveCategory.STATUS, power=0, healing=50)
    apply_move_effects(attacker, target, move, 0)
    assert attacker.current_hp == attacker.max_hp


# --- Flinch tests ---

def test_flinch_added_to_volatile():
    random.seed(0)
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("iron-head", power=80, flinch_chance=100)
    apply_move_effects(attacker, target, move, 50)
    assert "flinch" in target.volatile


def test_flinch_prevents_action():
    from src.engine.moves import can_act
    target = _make_pokemon("Target")
    target.volatile.add("flinch")
    assert not can_act(target)
    assert "flinch" not in target.volatile  # consumed


# --- Deterministic mode tests ---

def test_deterministic_skips_low_chance_ailment():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("flamethrower", power=90, ailment="burn", ailment_chance=10)
    apply_move_effects(attacker, target, move, 50, deterministic=True)
    assert target.status == Status.NONE  # 10% chance skipped


def test_deterministic_applies_guaranteed_ailment():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("thunder-wave", category=MoveCategory.STATUS, power=0,
                      ailment="paralysis", ailment_chance=0)
    apply_move_effects(attacker, target, move, 0, deterministic=True)
    assert target.status == Status.PARALYSIS


def test_deterministic_applies_guaranteed_stat_changes():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("close-combat", power=120,
                      stat_changes=[("defense", -1), ("sp_defense", -1)],
                      stat_change_target="user", stat_chance=0)
    apply_move_effects(attacker, target, move, 80, deterministic=True)
    assert attacker.stat_stages["defense"] == -1


def test_no_status_on_fainted_target():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    target.current_hp = 0  # fainted
    move = _make_move("thunder-wave", category=MoveCategory.STATUS, power=0,
                      ailment="paralysis", ailment_chance=0)
    events = apply_move_effects(attacker, target, move, 0)
    assert target.status == Status.NONE
    assert len(events) == 0


def test_deterministic_skips_flinch():
    attacker = _make_pokemon("Attacker")
    target = _make_pokemon("Target")
    move = _make_move("iron-head", power=80, flinch_chance=30)
    apply_move_effects(attacker, target, move, 50, deterministic=True)
    assert "flinch" not in target.volatile
