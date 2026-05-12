from __future__ import annotations
from rich.console import Console
from src.data.pokeapi_client import PokeAPIClient
from src.data.champion_loader import ChampionLoader, ChampionTeam, TrainerEntry
from src.engine.pokemon import Pokemon
import random

console = Console()


def build_player_team(client: PokeAPIClient) -> list[Pokemon]:
    console.print("\n[bold]Choose your team mode:[/bold]")
    console.print("  1. Fully random")
    console.print("  2. Pick Pokemon, random moves")
    console.print("  3. Full manual")
    console.print("  4. Pick from champion presets")
    console.print()

    choice = _prompt_choice(1, 4)

    if choice == 1:
        return _random_team(client)
    elif choice == 2:
        return _pick_pokemon_random_moves(client)
    elif choice == 3:
        return _full_manual(client)
    elif choice == 4:
        return _champion_preset(client)
    return []


def build_opponent_team(client: PokeAPIClient) -> tuple[str, list[Pokemon], list[str]]:
    """Returns (trainer_name, team, trainer_items)."""
    loader = ChampionLoader()
    trainers = loader.list_trainers()

    console.print("\n[bold]Choose your opponent:[/bold]")
    for i, t in enumerate(trainers):
        console.print(f"  {i + 1}. {t.display_name} ({t.role})")
    console.print(f"  {len(trainers) + 1}. Random team")
    console.print()

    trainer_choice = _prompt_choice(1, len(trainers) + 1)

    if trainer_choice == len(trainers) + 1:
        team = [client.get_random_pokemon(level=100) for _ in range(6)]
        return "Random Trainer", team, []

    variant_choice = _prompt_variant(trainers[trainer_choice - 1])
    filename = _resolve_trainer_selection(trainers, trainer_choice, variant_choice)

    champ_data = loader.load_champion(filename)
    team = _build_champion_team(client, champ_data)
    return champ_data.name, team, champ_data.items


def _random_team(client: PokeAPIClient) -> list[Pokemon]:
    console.print("\n[bold]Generating random team...[/bold]")
    team = []
    for i in range(6):
        console.print(f"  Fetching Pokemon {i + 1}/6...")
        pokemon = client.get_random_pokemon(level=100)
        team.append(pokemon)
        console.print(f"    Got {pokemon.name.title()}!")
    return team


def _pick_pokemon_random_moves(client: PokeAPIClient) -> list[Pokemon]:
    team = []
    for i in range(6):
        console.print(f"\n  Pokemon {i + 1}/6 — Enter name or dex number (or 'random'):")
        while True:
            raw = console.input("  > ").strip().lower()
            if raw == "random":
                pokemon = client.get_random_pokemon(level=100)
            else:
                try:
                    name_or_id = int(raw) if raw.isdigit() else raw
                    learnable = client.get_learnable_moves(name_or_id)
                    chosen = random.sample(learnable, min(4, len(learnable)))
                    moves = []
                    for mn in chosen:
                        try:
                            moves.append(client.get_move(mn))
                        except Exception:
                            continue
                    pokemon = client.get_pokemon(name_or_id, level=100)
                    pokemon.moves = moves
                except Exception as e:
                    console.print(f"  [red]Error: {e}. Try again.[/red]")
                    continue
            team.append(pokemon)
            console.print(f"    {pokemon.name.title()} with moves: {', '.join(m.name for m in pokemon.moves)}")
            break
    return team


def _full_manual(client: PokeAPIClient) -> list[Pokemon]:
    team = []
    for i in range(6):
        console.print(f"\n  Pokemon {i + 1}/6 — Enter name or dex number:")
        while True:
            raw = console.input("  > ").strip().lower()
            try:
                name_or_id = int(raw) if raw.isdigit() else raw
                learnable = client.get_learnable_moves(name_or_id)
                console.print(f"  Available moves: {', '.join(sorted(learnable)[:50])}...")
                if len(learnable) > 50:
                    console.print(f"    ({len(learnable)} total — type move names)")

                chosen_moves = []
                for j in range(4):
                    console.print(f"  Move {j + 1}/4:")
                    while True:
                        move_name = console.input("  > ").strip().lower().replace(" ", "-")
                        if move_name in learnable:
                            chosen_moves.append(client.get_move(move_name))
                            break
                        console.print(f"  [red]'{move_name}' not in learnset. Try again.[/red]")

                pokemon = client.get_pokemon(name_or_id, level=100)
                pokemon.moves = chosen_moves
                team.append(pokemon)
                console.print(f"    {pokemon.name.title()} ready!")
                break
            except Exception as e:
                console.print(f"  [red]Error: {e}. Try again.[/red]")
    return team


def _champion_preset(client: PokeAPIClient) -> list[Pokemon]:
    loader = ChampionLoader()
    trainers = loader.list_trainers()

    console.print("\n  Pick a champion's team to use:")
    for i, t in enumerate(trainers):
        console.print(f"    {i + 1}. {t.display_name} ({t.role})")
    console.print()

    trainer_choice = _prompt_choice(1, len(trainers))
    variant_choice = _prompt_variant(trainers[trainer_choice - 1])
    filename = _resolve_trainer_selection(trainers, trainer_choice, variant_choice)

    champ_data = loader.load_champion(filename)
    return _build_champion_team(client, champ_data)


def _build_champion_team(client: PokeAPIClient, champ: ChampionTeam) -> list[Pokemon]:
    team = []
    for member in champ.party:
        console.print(f"  Loading {member.species}...")
        pokemon = client.get_pokemon(
            member.species,
            level=member.level,
            move_names=member.moves,
            iv_scale=member.iv_scale,
        )
        if member.item:
            pokemon.item = member.item
        team.append(pokemon)
    return team


def _resolve_trainer_selection(
    trainers: list[TrainerEntry],
    trainer_choice: int,
    variant_choice: int | None,
) -> str:
    """Pure selection logic — given user choices, return the chosen JSON filename.

    trainer_choice is 1-indexed into `trainers`.
    variant_choice is 1-indexed into the trainer's variants, or None when the trainer
    has only one variant (in which case it's auto-selected).
    """
    trainer = trainers[trainer_choice - 1]
    if len(trainer.variants) == 1:
        return trainer.variants[0][1]
    return trainer.variants[variant_choice - 1][1]


def _prompt_variant(trainer: TrainerEntry) -> int | None:
    """Prompt for base vs rematch when a trainer has multiple variants. Returns None for single-variant trainers."""
    if len(trainer.variants) == 1:
        return None
    console.print(f"\n[bold]{trainer.display_name}: which version?[/bold]")
    for i, (label, _filename) in enumerate(trainer.variants):
        console.print(f"  {i + 1}. {label}")
    console.print()
    return _prompt_choice(1, len(trainer.variants))


def _prompt_choice(low: int, high: int) -> int:
    while True:
        try:
            raw = console.input("  > ").strip()
            val = int(raw)
            if low <= val <= high:
                return val
            console.print(f"  [red]Enter a number between {low} and {high}.[/red]")
        except ValueError:
            console.print(f"  [red]Enter a number.[/red]")
