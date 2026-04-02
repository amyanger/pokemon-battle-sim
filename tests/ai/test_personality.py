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
