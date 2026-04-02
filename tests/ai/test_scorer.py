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
    assert scores[0] > scores[1]

def test_immune_move_scores_zero():
    scorer = MoveScorer(PROFILES["balanced"], BattleMemory(), OpponentModel())
    attacker = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[
            _make_move("Thunderbolt", "electric", MoveCategory.SPECIAL, 95),
            _make_move("Iron Tail", "steel", MoveCategory.PHYSICAL, 100),
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
    agg_ratio = agg_scores[0] / max(agg_scores[1], 0.01)
    bal_ratio = bal_scores[0] / max(bal_scores[1], 0.01)
    assert agg_ratio > bal_ratio
