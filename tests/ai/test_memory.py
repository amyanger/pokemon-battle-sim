from src.ai.memory import BattleMemory, TurnRecord


def test_record_turn():
    mem = BattleMemory(max_turns=4)
    mem.record_turn(TurnRecord(
        turn=1, user_move="dark-void", user_pokemon="darkrai",
        opponent_move="tackle", opponent_pokemon="pikachu",
        damage_dealt=0, damage_taken=30,
    ))
    assert len(mem.history) == 1
    assert mem.history[0].user_move == "dark-void"

def test_max_turns_limit():
    mem = BattleMemory(max_turns=2)
    for i in range(5):
        mem.record_turn(TurnRecord(
            turn=i, user_move="tackle", user_pokemon="a",
            opponent_move="tackle", opponent_pokemon="b",
            damage_dealt=10, damage_taken=10,
        ))
    assert len(mem.history) == 2
    assert mem.history[0].turn == 3

def test_detect_protect_spam():
    mem = BattleMemory(max_turns=4)
    for i in range(3):
        mem.record_turn(TurnRecord(
            turn=i, user_move="tackle", user_pokemon="a",
            opponent_move="protect", opponent_pokemon="b",
            damage_dealt=0, damage_taken=0,
        ))
    patterns = mem.detect_patterns()
    assert "opponent_protect_spam" in patterns

def test_detect_sleep_lead():
    mem = BattleMemory(max_turns=4)
    mem.record_turn(TurnRecord(
        turn=1, user_move="tackle", user_pokemon="a",
        opponent_move="dark-void", opponent_pokemon="darkrai",
        damage_dealt=0, damage_taken=0,
    ))
    patterns = mem.detect_patterns()
    assert "opponent_sleep_lead" in patterns

def test_detect_switch_loop():
    mem = BattleMemory(max_turns=4)
    mem.record_turn(TurnRecord(turn=1, user_move="t", user_pokemon="a",
                               opponent_move="switch", opponent_pokemon="b",
                               damage_dealt=0, damage_taken=0))
    mem.record_turn(TurnRecord(turn=2, user_move="t", user_pokemon="a",
                               opponent_move="tackle", opponent_pokemon="c",
                               damage_dealt=0, damage_taken=0))
    mem.record_turn(TurnRecord(turn=3, user_move="t", user_pokemon="a",
                               opponent_move="switch", opponent_pokemon="b",
                               damage_dealt=0, damage_taken=0))
    patterns = mem.detect_patterns()
    assert "opponent_switch_loop" in patterns
