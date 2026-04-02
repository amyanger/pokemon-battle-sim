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
    garchomp = _make_pokemon("garchomp", ["dragon", "ground"])
    pikachu = _make_pokemon("pikachu", ["electric"])
    threat = model.assess_threat(garchomp, pikachu)
    assert threat > 1.0

def test_assess_threat_bad_matchup():
    model = OpponentModel()
    pikachu = _make_pokemon("pikachu", ["electric"])
    geodude = _make_pokemon("geodude", ["rock", "ground"])
    threat = model.assess_threat(pikachu, geodude)
    assert threat < 1.0

def test_rank_threats():
    model = OpponentModel()
    my_pokemon = _make_pokemon("pikachu", ["electric"])
    opponents = [
        _make_pokemon("garchomp", ["dragon", "ground"]),
        _make_pokemon("magikarp", ["water"]),
        _make_pokemon("steelix", ["steel", "ground"]),
    ]
    ranked = model.rank_threats(opponents, my_pokemon)
    assert ranked[0].name in ("garchomp", "steelix")
