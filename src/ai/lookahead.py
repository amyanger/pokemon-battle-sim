from __future__ import annotations
import copy
from dataclasses import dataclass
from src.engine.pokemon import Pokemon, Move, MoveCategory, Status
from src.engine.damage import calculate_damage


@dataclass
class BoardState:
    my_hp_pct: float
    opp_hp_pct: float
    my_alive: int
    opp_alive: int
    my_status: bool
    opp_status: bool
    my_boosts: int
    opp_boosts: int

    def evaluate(self) -> float:
        score = 0.0
        score += (self.my_hp_pct - self.opp_hp_pct) * 30
        score += (self.my_alive - self.opp_alive) * 20
        if self.opp_status:
            score += 5
        if self.my_status:
            score -= 5
        score += (self.my_boosts - self.opp_boosts) * 3
        return score


class Lookahead:
    def __init__(self, depth: int = 2):
        self.depth = depth

    def evaluate_moves(self, attacker: Pokemon, defender: Pokemon,
                       my_team_alive: int = 6, opp_team_alive: int = 6) -> list[float]:
        scores = []
        for i, move in enumerate(attacker.moves):
            if move.current_pp <= 0:
                scores.append(-999.0)
                continue
            score = self._simulate_move(attacker, defender, move, my_team_alive, opp_team_alive)
            scores.append(score)
        return scores

    def _simulate_move(self, attacker: Pokemon, defender: Pokemon, move: Move,
                       my_alive: int, opp_alive: int) -> float:
        sim_attacker = self._clone_pokemon(attacker)
        sim_defender = self._clone_pokemon(defender)

        our_result = calculate_damage(sim_attacker, sim_defender, move, critical=False, roll=92)
        sim_defender.take_damage(our_result.damage)

        if not sim_defender.is_alive:
            opp_alive_after = opp_alive - 1
            # Use damage ratio as a tiebreaker: more damage = lower opp_hp_pct equivalent
            damage_ratio = min(1.0, our_result.damage / sim_defender.max_hp)
            state = BoardState(
                my_hp_pct=sim_attacker.current_hp / sim_attacker.max_hp,
                opp_hp_pct=max(0.0, 1.0 - damage_ratio), my_alive=my_alive, opp_alive=opp_alive_after,
                my_status=sim_attacker.status != Status.NONE, opp_status=False,
                my_boosts=sum(max(0, v) for v in sim_attacker.stat_stages.values()),
                opp_boosts=0,
            )
            return state.evaluate()

        if self.depth <= 1:
            return self._evaluate_current(sim_attacker, sim_defender, my_alive, opp_alive)

        best_opp_score = -999.0
        for opp_move in sim_defender.moves:
            if opp_move.current_pp <= 0:
                continue
            sim_atk2 = self._clone_pokemon(sim_attacker)
            sim_def2 = self._clone_pokemon(sim_defender)
            opp_result = calculate_damage(sim_def2, sim_atk2, opp_move, critical=False, roll=92)
            sim_atk2.take_damage(opp_result.damage)
            opp_eval = self._evaluate_current(sim_atk2, sim_def2, my_alive, opp_alive)
            if -opp_eval > best_opp_score:
                best_opp_score = -opp_eval

        return -best_opp_score if best_opp_score > -999.0 else self._evaluate_current(
            sim_attacker, sim_defender, my_alive, opp_alive)

    def _evaluate_current(self, attacker: Pokemon, defender: Pokemon,
                          my_alive: int, opp_alive: int) -> float:
        opp_alive_adj = opp_alive - (0 if defender.is_alive else 1)
        my_alive_adj = my_alive - (0 if attacker.is_alive else 1)
        state = BoardState(
            my_hp_pct=attacker.current_hp / attacker.max_hp if attacker.is_alive else 0.0,
            opp_hp_pct=defender.current_hp / defender.max_hp if defender.is_alive else 0.0,
            my_alive=my_alive_adj, opp_alive=opp_alive_adj,
            my_status=attacker.status != Status.NONE,
            opp_status=defender.status != Status.NONE,
            my_boosts=sum(max(0, v) for v in attacker.stat_stages.values()),
            opp_boosts=sum(max(0, v) for v in defender.stat_stages.values()),
        )
        return state.evaluate()

    def _clone_pokemon(self, pokemon: Pokemon) -> Pokemon:
        p = copy.copy(pokemon)
        p.stat_stages = dict(pokemon.stat_stages)
        p.volatile = set(pokemon.volatile)
        p.moves = list(pokemon.moves)
        return p
