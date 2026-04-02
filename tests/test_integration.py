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
    assert turns < 50


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
