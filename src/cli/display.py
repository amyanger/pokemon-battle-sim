from __future__ import annotations
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from src.engine.pokemon import Pokemon, Status
from src.engine.battle import BattleEvent, EventType


console = Console()


TYPE_COLORS: dict[str, str] = {
    "normal": "white",
    "fire": "bright_red",
    "water": "bright_blue",
    "electric": "bright_yellow",
    "grass": "bright_green",
    "ice": "bright_cyan",
    "fighting": "red",
    "poison": "magenta",
    "ground": "yellow",
    "flying": "cyan",
    "psychic": "bright_magenta",
    "bug": "green",
    "rock": "yellow",
    "ghost": "purple",
    "dragon": "blue",
    "dark": "grey50",
    "steel": "grey70",
}


def _type_badge(type_name: str) -> Text:
    color = TYPE_COLORS.get(type_name, "white")
    badge = Text()
    badge.append("[", style="dim")
    badge.append(type_name.upper(), style=f"bold {color}")
    badge.append("]", style="dim")
    return badge


def _hp_color(pct: float) -> str:
    if pct > 0.5:
        return "green"
    elif pct > 0.2:
        return "yellow"
    return "red"


def _hp_bar(current: int, maximum: int, width: int = 24) -> Text:
    pct = current / max(maximum, 1)
    filled = int(round(pct * width))
    filled = max(0, min(width, filled))
    color = _hp_color(pct)
    if current <= 0:
        display_pct = 0
    elif current >= maximum:
        display_pct = 100
    else:
        display_pct = max(1, min(99, int(round(pct * 100))))
    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * (width - filled), style="dim")
    bar.append(f"  {current} / {maximum}   {display_pct}%")
    return bar


_STATUS_LABELS: dict[Status, tuple[str, str]] = {
    Status.BURN: ("BRN", "red"),
    Status.FREEZE: ("FRZ", "cyan"),
    Status.PARALYSIS: ("PAR", "yellow"),
    Status.POISON: ("PSN", "magenta"),
    Status.BAD_POISON: ("TOX", "magenta"),
    Status.SLEEP: ("SLP", "dim"),
}


def _status_text(status: Status) -> Text:
    if status == Status.NONE:
        return Text("—", style="dim")
    label, style = _STATUS_LABELS[status]
    return Text(label, style=f"bold {style}")


_STAGE_LABELS: dict[str, str] = {
    "attack": "Atk",
    "defense": "Def",
    "sp_attack": "SpA",
    "sp_defense": "SpD",
    "speed": "Spe",
}


def _stages_text(pokemon) -> Text:
    parts: list[str] = []
    for stat, label in _STAGE_LABELS.items():
        val = pokemon.stat_stages.get(stat, 0)
        if val == 0:
            continue
        sign = "+" if val > 0 else ""
        parts.append(f"{label} {sign}{val}")
    if not parts:
        return Text("—", style="dim")
    style = "blue" if any("+" in p for p in parts) else "yellow"
    return Text("  ".join(parts), style=style)


def show_battle_state(player: Pokemon, opponent: Pokemon, turn: int, opponent_name: str = "Opponent"):
    console.print(f"\n--- Turn {turn} ---", style="bold")
    opp_hp_bar = _hp_bar(opponent.current_hp, opponent.max_hp)
    opp_status = _status_text(opponent.status)
    console.print(f"  {opponent_name}'s {opponent.name.title()} Lv{opponent.level} {opp_status}")
    console.print(f"  ", end="")
    console.print(opp_hp_bar)
    console.print()
    p_hp_bar = _hp_bar(player.current_hp, player.max_hp)
    p_status = _status_text(player.status)
    console.print(f"  Your {player.name.title()} Lv{player.level} {p_status}")
    console.print(f"  ", end="")
    console.print(p_hp_bar)
    console.print()


def show_move_menu(pokemon: Pokemon, can_switch: bool = True):
    console.print(f"  {pokemon.name.title()}'s moves:", style="bold")
    for i, move in enumerate(pokemon.moves):
        pp_color = "green" if move.current_pp > move.pp // 4 else "red"
        console.print(
            f"    {i + 1}. {move.name.replace('-', ' ').title():20s} "
            f"({move.type.title():10s}) "
            f"[{pp_color}]PP: {move.current_pp}/{move.pp}[/{pp_color}]"
        )
    if can_switch:
        console.print(f"    {len(pokemon.moves) + 1}. Switch Pokemon")
    console.print()


def show_switch_menu(team: list[Pokemon], active_index: int):
    console.print("  Choose a Pokemon:", style="bold")
    for i, poke in enumerate(team):
        if i == active_index:
            continue
        if not poke.is_alive:
            console.print(f"    {i + 1}. {poke.name.title()} [red](fainted)[/red]")
        else:
            hp_bar = _hp_bar(poke.current_hp, poke.max_hp)
            console.print(f"    {i + 1}. {poke.name.title()} ", end="")
            console.print(hp_bar)
    console.print(f"    0. Back")
    console.print()


def show_events(events: list[BattleEvent]):
    for event in events:
        if event.event_type == EventType.DAMAGE:
            console.print(f"  {event.message} ({event.damage} damage)")
        elif event.event_type == EventType.EFFECTIVENESS:
            if event.effectiveness > 1.0:
                console.print(f"  [green]{event.message}[/green]")
            elif event.effectiveness == 0.0:
                console.print(f"  [dim]{event.message}[/dim]")
            else:
                console.print(f"  [yellow]{event.message}[/yellow]")
        elif event.event_type == EventType.CRITICAL:
            console.print(f"  [bold yellow]{event.message}[/bold yellow]")
        elif event.event_type == EventType.FAINT:
            console.print(f"  [red]{event.message}[/red]")
        elif event.event_type == EventType.SWITCH:
            console.print(f"  [cyan]{event.message}[/cyan]")
        elif event.event_type == EventType.CANT_ACT:
            console.print(f"  [dim]{event.message}[/dim]")
        elif event.event_type == EventType.END_OF_TURN:
            console.print(f"  [magenta]{event.message}[/magenta]")
        elif event.event_type == EventType.MISS:
            console.print(f"  [dim]{event.message}[/dim]")
        elif event.event_type == EventType.STATUS:
            console.print(f"  [yellow]{event.message}[/yellow]")
        elif event.event_type == EventType.STAT_CHANGE:
            console.print(f"  [blue]{event.message}[/blue]")
        elif event.event_type == EventType.RECOIL:
            console.print(f"  [red]{event.message}[/red]")
        elif event.event_type == EventType.DRAIN:
            console.print(f"  [green]{event.message}[/green]")
        elif event.event_type == EventType.HEAL:
            console.print(f"  [green]{event.message}[/green]")
        else:
            console.print(f"  {event.message}")


def show_battle_result(winner: str, turn_count: int, player_fainted: int, opponent_fainted: int,
                       damage_dealt: dict[str, int]):
    console.print()
    if winner == "player":
        console.print(Panel("[bold green]You Win![/bold green]", expand=False))
    else:
        console.print(Panel("[bold red]You Lose![/bold red]", expand=False))
    table = Table(title="Battle Summary")
    table.add_column("Stat", style="bold")
    table.add_column("Value")
    table.add_row("Turns", str(turn_count))
    table.add_row("Your Pokemon Fainted", str(player_fainted))
    table.add_row("Opponent Pokemon Fainted", str(opponent_fainted))
    if damage_dealt:
        mvp = max(damage_dealt, key=damage_dealt.get)
        table.add_row("MVP", f"{mvp.title()} ({damage_dealt[mvp]} damage)")
    console.print(table)
