from __future__ import annotations
import random
import typer
from rich.console import Console
from src.data.pokeapi_client import PokeAPIClient
from src.engine.battle import Battle, BattleAction, ActionType
from src.engine.pokemon import Status
from src.ai.scorer import MoveScorer, GameState
from src.ai.lookahead import Lookahead
from src.ai.memory import BattleMemory, TurnRecord
from src.ai.opponent_model import OpponentModel
from src.ai.personality import get_champion_personality, PROFILES
from src.cli.display import (
    show_battle_state, show_move_menu, show_switch_menu,
    show_events, show_battle_result,
)
from src.cli.team_builder import build_player_team, build_opponent_team

app = typer.Typer()
console = Console()


class AIController:
    def __init__(self, name: str, battle: Battle, trainer_items: list[str]):
        personality = get_champion_personality(name)
        self.memory = BattleMemory()
        self.opponent_model = OpponentModel()
        self.scorer = MoveScorer(personality, self.memory, self.opponent_model)
        self.lookahead = Lookahead(depth=2)
        self.battle = battle
        self.trainer_items = list(trainer_items)
        self.name = name

    def choose_action(self) -> BattleAction:
        my_pokemon = self.battle.opponent_pokemon
        target = self.battle.player_pokemon

        # Check if we should use an item (Full Restore when HP < 30%)
        if self.trainer_items and my_pokemon.current_hp / my_pokemon.max_hp < 0.3:
            return BattleAction(ActionType.ITEM, item_name=self.trainer_items.pop(0))

        # Check if we should switch
        switch_idx = self._consider_switch()
        if switch_idx is not None:
            return BattleAction(ActionType.SWITCH, switch_index=switch_idx)

        # Score moves
        state = GameState(
            my_team_alive=sum(1 for p in self.battle.opponent_team if p.is_alive),
            opp_team_alive=sum(1 for p in self.battle.player_team if p.is_alive),
            turn=self.battle.turn_count,
        )
        base_scores = self.scorer.score_moves(my_pokemon, target, state)
        lookahead_scores = self.lookahead.evaluate_moves(
            my_pokemon, target,
            my_team_alive=state.my_team_alive,
            opp_team_alive=state.opp_team_alive,
        )

        # Combine scores (weighted average)
        combined = []
        for i in range(len(my_pokemon.moves)):
            if i < len(base_scores) and i < len(lookahead_scores):
                combined.append(base_scores[i] * 0.6 + lookahead_scores[i] * 0.4)
            elif i < len(base_scores):
                combined.append(base_scores[i])
            else:
                combined.append(0)

        if not combined or max(combined) <= 0:
            alive = self.battle.get_alive_indices("opponent")
            if alive:
                return BattleAction(ActionType.SWITCH, switch_index=alive[0])
            return BattleAction(ActionType.MOVE, move_index=0)

        best_idx = combined.index(max(combined))
        return BattleAction(ActionType.MOVE, move_index=best_idx)

    def _consider_switch(self) -> int | None:
        my_pokemon = self.battle.opponent_pokemon
        target = self.battle.player_pokemon
        alive_indices = self.battle.get_alive_indices("opponent")
        if not alive_indices:
            return None

        from src.engine.typechart import get_matchup
        best_eff = max(
            (get_matchup(m.type, target.types) for m in my_pokemon.moves if m.current_pp > 0),
            default=0,
        )
        if best_eff == 0.0:
            best_idx = None
            best_threat = -1
            for idx in alive_indices:
                candidate = self.battle.opponent_team[idx]
                threat = self.opponent_model.assess_threat(candidate, target)
                if threat > best_threat:
                    best_threat = threat
                    best_idx = idx
            return best_idx
        return None

    def record_turn(self, user_move: str, opp_move: str, damage_dealt: int, damage_taken: int):
        self.memory.record_turn(TurnRecord(
            turn=self.battle.turn_count,
            user_move=opp_move,
            user_pokemon=self.battle.opponent_pokemon.name,
            opponent_move=user_move,
            opponent_pokemon=self.battle.player_pokemon.name,
            damage_dealt=damage_dealt,
            damage_taken=damage_taken,
        ))
        self.opponent_model.reveal_move(self.battle.player_pokemon.name, user_move)


def _get_player_action(battle: Battle) -> BattleAction:
    show_move_menu(battle.player_pokemon, can_switch=bool(battle.get_alive_indices("player")))
    while True:
        try:
            raw = console.input("  > ").strip()
            choice = int(raw)
            if 1 <= choice <= len(battle.player_pokemon.moves):
                move = battle.player_pokemon.moves[choice - 1]
                if move.current_pp <= 0:
                    console.print("  [red]No PP left for that move![/red]")
                    continue
                return BattleAction(ActionType.MOVE, move_index=choice - 1)
            elif choice == len(battle.player_pokemon.moves) + 1:
                show_switch_menu(battle.player_team, battle.player_active)
                while True:
                    raw2 = console.input("  > ").strip()
                    idx = int(raw2)
                    if idx == 0:
                        show_move_menu(battle.player_pokemon)
                        break
                    if 1 <= idx <= len(battle.player_team) and idx - 1 != battle.player_active:
                        poke = battle.player_team[idx - 1]
                        if poke.is_alive:
                            return BattleAction(ActionType.SWITCH, switch_index=idx - 1)
                        console.print("  [red]That Pokemon has fainted![/red]")
                    else:
                        console.print("  [red]Invalid choice.[/red]")
            else:
                console.print("  [red]Invalid choice.[/red]")
        except ValueError:
            console.print("  [red]Enter a number.[/red]")


def _handle_faint_switch(battle: Battle, team: str) -> None:
    """Force a switch when active Pokemon faints."""
    active_pokemon = battle.player_pokemon if team == "player" else battle.opponent_pokemon
    if active_pokemon.is_alive:
        return

    alive = battle.get_alive_indices(team)
    if not alive:
        return

    if team == "player":
        console.print(f"\n  [red]{active_pokemon.name.title()} fainted! Choose next Pokemon:[/red]")
        show_switch_menu(battle.player_team, battle.player_active)
        while True:
            try:
                idx = int(console.input("  > ").strip())
                actual_idx = idx - 1
                if actual_idx in alive:
                    battle.player_active = actual_idx
                    console.print(f"  Go, {battle.player_pokemon.name.title()}!")
                    return
                console.print("  [red]Invalid choice.[/red]")
            except ValueError:
                console.print("  [red]Enter a number.[/red]")
    else:
        # AI picks best switch
        battle.opponent_active = alive[0]
        console.print(f"  [cyan]{battle.opponent_pokemon.name.title()} was sent out![/cyan]")


@app.command()
def battle():
    """Start a Pokemon battle!"""
    console.print("[bold]Pokemon Battle Simulator[/bold]", style="bold blue")
    console.print("Powered by improved AI with lookahead, memory, and personality\n")

    client = PokeAPIClient()

    try:
        player_team = build_player_team(client)
        opponent_name, opponent_team, trainer_items = build_opponent_team(client)

        battle_state = Battle(player_team=player_team, opponent_team=opponent_team)
        ai = AIController(opponent_name, battle_state, trainer_items)

        console.print(f"\n[bold]Battle Start: You vs {opponent_name}![/bold]\n")

        while not battle_state.is_over():
            show_battle_state(
                battle_state.player_pokemon,
                battle_state.opponent_pokemon,
                battle_state.turn_count + 1,
                opponent_name,
            )

            player_action = _get_player_action(battle_state)
            ai_action = ai.choose_action()

            # Handle AI items
            if ai_action.action_type == ActionType.ITEM:
                console.print(f"  [cyan]{opponent_name} used a Full Restore![/cyan]")
                battle_state.opponent_pokemon.current_hp = battle_state.opponent_pokemon.max_hp
                battle_state.opponent_pokemon.status = Status.NONE
                # Player still gets their move — treat AI as doing nothing offensively
                ai_action = BattleAction(ActionType.MOVE, move_index=0)

            events = battle_state.execute_turn(player_action, ai_action)
            show_events(events)

            # Record turn in AI memory
            p_move = (battle_state.player_pokemon.moves[player_action.move_index].name
                     if player_action.action_type == ActionType.MOVE else "switch")
            o_move = "switch" if ai_action.action_type == ActionType.SWITCH else (
                battle_state.opponent_pokemon.moves[ai_action.move_index].name
                if ai_action.action_type == ActionType.MOVE else "item")
            ai.record_turn(p_move, o_move, 0, 0)

            # Handle faints
            _handle_faint_switch(battle_state, "opponent")
            _handle_faint_switch(battle_state, "player")

        winner = battle_state.get_winner()
        show_battle_result(
            winner=winner,
            turn_count=battle_state.turn_count,
            player_fainted=battle_state.player_fainted,
            opponent_fainted=battle_state.opponent_fainted,
            damage_dealt=battle_state.damage_dealt,
        )
    finally:
        client.close()


def main():
    app()


if __name__ == "__main__":
    main()
