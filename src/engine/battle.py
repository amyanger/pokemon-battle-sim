from __future__ import annotations
import random
from dataclasses import dataclass, field
from enum import Enum
from src.engine.pokemon import Pokemon, Move, Status
from src.engine.damage import calculate_damage, DamageResult
from src.engine.moves import apply_end_of_turn, can_act, get_effective_speed
from src.engine.typechart import get_matchup


class ActionType(Enum):
    MOVE = "move"
    SWITCH = "switch"
    ITEM = "item"


class EventType(Enum):
    DAMAGE = "damage"
    MISS = "miss"
    STATUS = "status"
    FAINT = "faint"
    SWITCH = "switch"
    EFFECTIVENESS = "effectiveness"
    CRITICAL = "critical"
    END_OF_TURN = "end_of_turn"
    CANT_ACT = "cant_act"
    ITEM_USED = "item_used"


@dataclass
class BattleAction:
    action_type: ActionType
    move_index: int = 0
    switch_index: int = 0
    item_name: str | None = None


@dataclass
class BattleEvent:
    event_type: EventType
    source: str = ""
    target: str = ""
    message: str = ""
    damage: int = 0
    effectiveness: float = 1.0


@dataclass
class TurnEntry:
    pokemon: Pokemon
    action: BattleAction
    team: str  # "player" or "opponent"


class Battle:
    def __init__(self, player_team: list[Pokemon], opponent_team: list[Pokemon]):
        self.player_team = player_team
        self.opponent_team = opponent_team
        self.player_active: int = 0
        self.opponent_active: int = 0
        self.turn_count: int = 0
        self.player_fainted: int = 0
        self.opponent_fainted: int = 0
        self.damage_dealt: dict[str, int] = {}

    @property
    def player_pokemon(self) -> Pokemon:
        return self.player_team[self.player_active]

    @property
    def opponent_pokemon(self) -> Pokemon:
        return self.opponent_team[self.opponent_active]

    def get_turn_order(
        self, player_action: BattleAction, opponent_action: BattleAction
    ) -> tuple[TurnEntry, TurnEntry]:
        player_entry = TurnEntry(self.player_pokemon, player_action, "player")
        opponent_entry = TurnEntry(self.opponent_pokemon, opponent_action, "opponent")

        # Switches always go first
        if player_action.action_type == ActionType.SWITCH and opponent_action.action_type != ActionType.SWITCH:
            return player_entry, opponent_entry
        if opponent_action.action_type == ActionType.SWITCH and player_action.action_type != ActionType.SWITCH:
            return opponent_entry, player_entry

        # Items go before moves
        if player_action.action_type == ActionType.ITEM and opponent_action.action_type == ActionType.MOVE:
            return player_entry, opponent_entry
        if opponent_action.action_type == ActionType.ITEM and player_action.action_type == ActionType.MOVE:
            return opponent_entry, player_entry

        # Both moves: check priority
        if player_action.action_type == ActionType.MOVE and opponent_action.action_type == ActionType.MOVE:
            p_priority = self.player_pokemon.moves[player_action.move_index].priority
            o_priority = self.opponent_pokemon.moves[opponent_action.move_index].priority
            if p_priority != o_priority:
                if p_priority > o_priority:
                    return player_entry, opponent_entry
                return opponent_entry, player_entry

        # Same priority: compare speed
        p_speed = get_effective_speed(self.player_pokemon)
        o_speed = get_effective_speed(self.opponent_pokemon)
        if p_speed == o_speed:
            if random.randint(0, 1) == 0:
                return player_entry, opponent_entry
            return opponent_entry, player_entry
        if p_speed > o_speed:
            return player_entry, opponent_entry
        return opponent_entry, player_entry

    def execute_turn(
        self, player_action: BattleAction, opponent_action: BattleAction
    ) -> list[BattleEvent]:
        self.turn_count += 1
        events: list[BattleEvent] = []

        first, second = self.get_turn_order(player_action, opponent_action)

        # Execute first action
        target_first = self.opponent_pokemon if first.team == "player" else self.player_pokemon
        events.extend(self._execute_action(first, target_first))

        # Execute second action (if still alive)
        if second.pokemon.is_alive:
            target_second = self.opponent_pokemon if second.team == "player" else self.player_pokemon
            if target_second.is_alive:
                events.extend(self._execute_action(second, target_second))

        # End of turn effects
        for pokemon in [self.player_pokemon, self.opponent_pokemon]:
            if pokemon.is_alive:
                eot_damage = apply_end_of_turn(pokemon)
                if eot_damage > 0:
                    events.append(BattleEvent(
                        EventType.END_OF_TURN, source=pokemon.name,
                        message=f"{pokemon.name} took {eot_damage} damage from {pokemon.status.value}!",
                        damage=eot_damage,
                    ))
                    if not pokemon.is_alive:
                        events.append(BattleEvent(EventType.FAINT, source=pokemon.name,
                                                  message=f"{pokemon.name} fainted!"))

        return events

    def _execute_action(self, entry: TurnEntry, target: Pokemon) -> list[BattleEvent]:
        events: list[BattleEvent] = []

        if entry.action.action_type == ActionType.SWITCH:
            idx = entry.action.switch_index
            if entry.team == "player":
                self.player_active = idx
                entry.pokemon.reset_stat_stages()
            else:
                self.opponent_active = idx
                entry.pokemon.reset_stat_stages()
            new_pokemon = self.player_pokemon if entry.team == "player" else self.opponent_pokemon
            events.append(BattleEvent(EventType.SWITCH, source=entry.pokemon.name,
                                      message=f"Go, {new_pokemon.name}!"))
            return events

        if entry.action.action_type == ActionType.MOVE:
            move = entry.pokemon.moves[entry.action.move_index]

            if not can_act(entry.pokemon):
                events.append(BattleEvent(EventType.CANT_ACT, source=entry.pokemon.name,
                                          message=f"{entry.pokemon.name} can't move!"))
                return events

            move.current_pp = max(0, move.current_pp - 1)

            if move.accuracy < 100 and random.randint(1, 100) > move.accuracy:
                events.append(BattleEvent(EventType.MISS, source=entry.pokemon.name,
                                          target=target.name,
                                          message=f"{entry.pokemon.name}'s {move.name} missed!"))
                return events

            result = calculate_damage(entry.pokemon, target, move)
            if result.damage > 0:
                target.take_damage(result.damage)
                self.damage_dealt[entry.pokemon.name] = self.damage_dealt.get(entry.pokemon.name, 0) + result.damage
                events.append(BattleEvent(EventType.DAMAGE, source=entry.pokemon.name,
                                          target=target.name, damage=result.damage,
                                          effectiveness=result.effectiveness,
                                          message=f"{entry.pokemon.name} used {move.name}!"))
                if result.effectiveness > 1.0:
                    events.append(BattleEvent(EventType.EFFECTIVENESS,
                                              message="It's super effective!",
                                              effectiveness=result.effectiveness))
                elif 0 < result.effectiveness < 1.0:
                    events.append(BattleEvent(EventType.EFFECTIVENESS,
                                              message="It's not very effective...",
                                              effectiveness=result.effectiveness))
                if result.critical:
                    events.append(BattleEvent(EventType.CRITICAL, message="A critical hit!"))

                if not target.is_alive:
                    events.append(BattleEvent(EventType.FAINT, source=target.name,
                                              message=f"{target.name} fainted!"))
                    if target in self.player_team:
                        self.player_fainted += 1
                    else:
                        self.opponent_fainted += 1
            elif result.effectiveness == 0.0:
                events.append(BattleEvent(EventType.EFFECTIVENESS,
                                          source=entry.pokemon.name,
                                          message=f"It doesn't affect {target.name}...",
                                          effectiveness=0.0))

        return events

    def is_over(self) -> bool:
        player_alive = any(p.is_alive for p in self.player_team)
        opponent_alive = any(p.is_alive for p in self.opponent_team)
        return not player_alive or not opponent_alive

    def get_winner(self) -> str | None:
        player_alive = any(p.is_alive for p in self.player_team)
        opponent_alive = any(p.is_alive for p in self.opponent_team)
        if not opponent_alive:
            return "player"
        if not player_alive:
            return "opponent"
        return None

    def get_alive_indices(self, team: str) -> list[int]:
        pokemon_list = self.player_team if team == "player" else self.opponent_team
        active = self.player_active if team == "player" else self.opponent_active
        return [i for i, p in enumerate(pokemon_list) if p.is_alive and i != active]
