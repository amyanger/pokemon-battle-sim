from __future__ import annotations
from dataclasses import dataclass, field

_SLEEP_MOVES = {"dark-void", "sleep-powder", "spore", "hypnosis", "sing", "grass-whistle", "lovely-kiss", "yawn"}


@dataclass
class TurnRecord:
    turn: int
    user_move: str
    user_pokemon: str
    opponent_move: str
    opponent_pokemon: str
    damage_dealt: int
    damage_taken: int


class BattleMemory:
    def __init__(self, max_turns: int = 4):
        self.max_turns = max_turns
        self.history: list[TurnRecord] = []

    def record_turn(self, record: TurnRecord):
        self.history.append(record)
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

    def detect_patterns(self) -> set[str]:
        patterns: set[str] = set()
        if not self.history:
            return patterns

        recent_opp_moves = [r.opponent_move for r in self.history[-3:]]
        if recent_opp_moves.count("protect") >= 2:
            patterns.add("opponent_protect_spam")

        recent_user_moves = [r.user_move for r in self.history[-3:]]
        if recent_user_moves.count("protect") >= 2:
            patterns.add("user_protect_spam")

        if self.history[0].opponent_move in _SLEEP_MOVES:
            patterns.add("opponent_sleep_lead")
        if self.history[0].user_move in _SLEEP_MOVES:
            patterns.add("user_sleep_lead")

        opp_pokemon = [r.opponent_pokemon for r in self.history]
        if len(opp_pokemon) >= 3:
            for i in range(len(opp_pokemon) - 2):
                if opp_pokemon[i] == opp_pokemon[i + 2] and opp_pokemon[i] != opp_pokemon[i + 1]:
                    patterns.add("opponent_switch_loop")
                    break

        opp_switches = [r for r in self.history if r.opponent_move == "switch"]
        if len(opp_switches) >= 2:
            patterns.add("opponent_switch_loop")

        return patterns

    def get_opponent_move_history(self, pokemon_name: str) -> list[str]:
        return [r.opponent_move for r in self.history if r.opponent_pokemon == pokemon_name]
