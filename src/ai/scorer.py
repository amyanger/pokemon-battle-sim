from __future__ import annotations
from dataclasses import dataclass
from src.engine.pokemon import Pokemon, Move, MoveCategory, Status
from src.engine.damage import calculate_damage
from src.engine.typechart import get_matchup
from src.ai.personality import Personality
from src.ai.memory import BattleMemory
from src.ai.opponent_model import OpponentModel

_SETUP_MOVES = {
    "swords-dance", "nasty-plot", "calm-mind", "dragon-dance", "bulk-up",
    "quiver-dance", "shell-smash", "agility", "rock-polish", "iron-defense",
    "amnesia", "barrier", "cosmic-power", "cotton-guard",
}

_DISRUPTION_MOVES = {
    "thunder-wave", "toxic", "will-o-wisp", "stun-spore", "sleep-powder",
    "spore", "dark-void", "hypnosis", "yawn", "confuse-ray", "swagger",
    "stealth-rock", "spikes", "toxic-spikes", "leech-seed",
}

_RECOVERY_MOVES = {
    "recover", "soft-boiled", "milk-drink", "roost", "slack-off",
    "moonlight", "morning-sun", "synthesis", "wish", "aqua-ring",
}


@dataclass
class GameState:
    my_team_alive: int
    opp_team_alive: int
    turn: int


class MoveScorer:
    def __init__(self, personality: Personality, memory: BattleMemory, opponent_model: OpponentModel):
        self.personality = personality
        self.memory = memory
        self.opponent_model = opponent_model

    def score_moves(self, attacker: Pokemon, defender: Pokemon, state: GameState) -> list[float]:
        scores = []
        for move in attacker.moves:
            raw = self._score_single_move(attacker, defender, move, state)
            scores.append(raw)
        return scores

    def _score_single_move(self, attacker: Pokemon, defender: Pokemon, move: Move, state: GameState) -> float:
        effectiveness = get_matchup(move.type, defender.types)
        if effectiveness == 0.0 and move.category != MoveCategory.STATUS:
            return 0.0
        if move.current_pp <= 0:
            return 0.0

        dimensions = {
            "damage_value": self._calc_damage_value(attacker, defender, move),
            "kill_potential": self._calc_kill_potential(attacker, defender, move),
            "risk": self._calc_risk(move),
            "setup_value": self._calc_setup_value(attacker, defender, move, state),
            "disruption": self._calc_disruption(defender, move, state),
        }

        weighted = self.personality.apply_weights(dimensions)
        return sum(weighted.values())

    def _calc_damage_value(self, attacker: Pokemon, defender: Pokemon, move: Move) -> float:
        if move.category == MoveCategory.STATUS:
            return 0.0
        result = calculate_damage(attacker, defender, move, critical=False, roll=100)
        return (result.damage / max(defender.max_hp, 1)) * 10

    def _calc_kill_potential(self, attacker: Pokemon, defender: Pokemon, move: Move) -> float:
        if move.category == MoveCategory.STATUS:
            return 0.0
        result = calculate_damage(attacker, defender, move, critical=False, roll=85)
        if result.damage >= defender.current_hp:
            return 10.0
        max_result = calculate_damage(attacker, defender, move, critical=False, roll=100)
        if max_result.damage >= defender.current_hp:
            return 5.0
        return 0.0

    def _calc_risk(self, move: Move) -> float:
        risk = 0.0
        if move.accuracy < 100:
            risk += (100 - move.accuracy) * 0.1
        if move.name in ("explosion", "self-destruct", "memento"):
            risk += 8.0
        elif move.name in ("close-combat", "superpower"):
            risk += 2.0
        elif move.name in ("giga-impact", "hyper-beam"):
            risk += 3.0
        return -risk

    def _calc_setup_value(self, attacker: Pokemon, defender: Pokemon, move: Move, state: GameState) -> float:
        if move.name not in _SETUP_MOVES:
            return 0.0
        if state.opp_team_alive <= 1:
            return 1.0
        hp_ratio = attacker.current_hp / attacker.max_hp
        value = 5.0 * hp_ratio
        stat_sum = sum(attacker.stat_stages.values())
        if stat_sum >= 4:
            value *= 0.3
        return value

    def _calc_disruption(self, defender: Pokemon, move: Move, state: GameState) -> float:
        if move.name not in _DISRUPTION_MOVES:
            return 0.0
        if defender.status != Status.NONE and move.name in (
            "thunder-wave", "toxic", "will-o-wisp", "stun-spore",
            "sleep-powder", "spore", "dark-void", "hypnosis",
        ):
            return -5.0
        if state.turn <= 3:
            return 6.0
        return 3.0
