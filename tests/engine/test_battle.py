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
