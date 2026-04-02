from __future__ import annotations
from src.engine.pokemon import Pokemon
from src.engine.typechart import get_matchup, TYPES


class OpponentModel:
    def __init__(self):
        self._known_moves: dict[str, set[str]] = {}

    def reveal_move(self, pokemon_name: str, move_name: str):
        if pokemon_name not in self._known_moves:
            self._known_moves[pokemon_name] = set()
        self._known_moves[pokemon_name].add(move_name)

    def get_known_moves(self, pokemon_name: str) -> set[str]:
        return self._known_moves.get(pokemon_name, set())

    def assess_threat(self, opponent: Pokemon, my_pokemon: Pokemon) -> float:
        """Score how threatening an opponent is to my pokemon.
        >1.0 = threatening, <1.0 = not threatening."""
        best_offense = max(
            get_matchup(opp_type, my_pokemon.types)
            for opp_type in opponent.types
        )
        best_defense = max(
            get_matchup(my_type, opponent.types)
            for my_type in my_pokemon.types
        )
        if best_defense == 0:
            best_defense = 0.25
        if best_offense == 0:
            return 0.1
        return best_offense / best_defense

    def rank_threats(self, opponents: list[Pokemon], my_pokemon: Pokemon) -> list[Pokemon]:
        return sorted(opponents, key=lambda o: self.assess_threat(o, my_pokemon), reverse=True)

    def predict_best_switch_target(self, opponent_team: list[Pokemon], my_pokemon: Pokemon) -> Pokemon | None:
        alive = [p for p in opponent_team if p.is_alive]
        if not alive:
            return None
        return max(alive, key=lambda o: self.assess_threat(o, my_pokemon))
