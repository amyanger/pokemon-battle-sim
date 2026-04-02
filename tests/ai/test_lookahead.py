from src.ai.lookahead import Lookahead, BoardState
from src.engine.pokemon import Pokemon, Move, MoveCategory


def _make_move(name, type_, category, power, accuracy=100, priority=0):
    return Move(name=name, type=type_, category=category, power=power,
                accuracy=accuracy, pp=10, priority=priority, effect=None)


def _make_pokemon(name, types, base_stats, moves, level=100):
    return Pokemon(name=name, types=types, level=level, base_stats=base_stats,
                   moves=moves, ability="", item=None, iv_scale=250)


def test_evaluate_board_state():
    state_good = BoardState(my_hp_pct=1.0, opp_hp_pct=0.2, my_alive=6, opp_alive=2,
                            my_status=False, opp_status=True, my_boosts=0, opp_boosts=0)
    state_bad = BoardState(my_hp_pct=0.2, opp_hp_pct=1.0, my_alive=2, opp_alive=6,
                           my_status=True, opp_status=False, my_boosts=0, opp_boosts=0)
    assert state_good.evaluate() > state_bad.evaluate()

def test_lookahead_prefers_kill():
    lookahead = Lookahead(depth=1)
    attacker = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[
            _make_move("Earthquake", "ground", MoveCategory.PHYSICAL, 100),
            _make_move("Tackle", "normal", MoveCategory.PHYSICAL, 40),
        ])
    defender = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[_make_move("Thunderbolt", "electric", MoveCategory.SPECIAL, 95)])
    defender.current_hp = 50
    scores = lookahead.evaluate_moves(attacker, defender, my_team_alive=6, opp_team_alive=1)
    assert scores[0] > scores[1]

def test_lookahead_considers_opponent_response():
    lookahead = Lookahead(depth=2)
    attacker = _make_pokemon("Pikachu", ["electric"],
        {"hp": 35, "attack": 55, "defense": 40, "sp_attack": 50, "sp_defense": 50, "speed": 90},
        moves=[
            _make_move("Thunderbolt", "electric", MoveCategory.SPECIAL, 95),
            _make_move("Iron Tail", "steel", MoveCategory.PHYSICAL, 100, accuracy=75),
        ])
    defender = _make_pokemon("Garchomp", ["dragon", "ground"],
        {"hp": 108, "attack": 130, "defense": 95, "sp_attack": 80, "sp_defense": 85, "speed": 102},
        moves=[_make_move("Earthquake", "ground", MoveCategory.PHYSICAL, 100)])
    scores = lookahead.evaluate_moves(attacker, defender, my_team_alive=6, opp_team_alive=6)
    assert scores[1] > scores[0]  # Iron Tail > Thunderbolt (immune)
