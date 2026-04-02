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
