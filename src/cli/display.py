from __future__ import annotations
from rich.console import Console, Group
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich import box
from src.engine.pokemon import Pokemon, Status
from src.engine.battle import Battle, BattleEvent, EventType


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


def _stages_text(pokemon: Pokemon) -> Text:
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


def _team_dots(team: list[Pokemon], active_index: int) -> Text:
    out = Text()
    for i in range(6):
        if i > 0:
            out.append(" ")
        if i >= len(team):
            out.append("○", style="dim")
            continue
        poke = team[i]
        if not poke.is_alive:
            out.append("○", style="dim")
            continue
        pct = poke.current_hp / max(poke.max_hp, 1)
        color = _hp_color(pct)
        style = f"bold {color}" if i == active_index else color
        out.append("●", style=style)
    return out


def _event_line(event: BattleEvent) -> Text:
    line = Text()
    line.append("  ▸ ", style="dim")
    body_style = ""
    if event.event_type == EventType.EFFECTIVENESS:
        if event.effectiveness > 1.0:
            body_style = "green"
        elif event.effectiveness == 0.0:
            body_style = "dim"
        else:
            body_style = "yellow"
    elif event.event_type == EventType.CRITICAL:
        body_style = "bold yellow"
    elif event.event_type == EventType.FAINT:
        body_style = "red"
    elif event.event_type == EventType.SWITCH:
        body_style = "cyan"
    elif event.event_type in (EventType.CANT_ACT, EventType.MISS):
        body_style = "dim"
    elif event.event_type == EventType.END_OF_TURN:
        body_style = "magenta"
    elif event.event_type == EventType.STATUS:
        body_style = "yellow"
    elif event.event_type == EventType.STAT_CHANGE:
        body_style = "blue"
    elif event.event_type == EventType.RECOIL:
        body_style = "red"
    elif event.event_type in (EventType.DRAIN, EventType.HEAL):
        body_style = "green"
    elif event.event_type == EventType.ITEM_USED:
        body_style = "cyan"

    line.append(event.message, style=body_style)
    if event.event_type == EventType.DAMAGE and event.damage:
        line.append(f"   {event.damage} damage", style="bold")
    return line


def _pokemon_card(pokemon: Pokemon) -> Panel:
    header = Text()
    header.append(pokemon.name.title(), style="bold")
    header.append(f"   Lv{pokemon.level}   ", style="dim")
    for i, t in enumerate(pokemon.types):
        if i > 0:
            header.append(" ")
        header.append_text(_type_badge(t))

    hp_line = Text("HP ", style="dim")
    hp_line.append_text(_hp_bar(pokemon.current_hp, pokemon.max_hp))

    meta_line = Text("Status ", style="dim")
    meta_line.append_text(_status_text(pokemon.status))
    meta_line.append("     Stages ", style="dim")
    meta_line.append_text(_stages_text(pokemon))

    body = Text()
    body.append_text(header)
    body.append("\n")
    body.append_text(hp_line)
    body.append("\n")
    body.append_text(meta_line)

    return Panel(body, box=box.SQUARE, padding=(0, 1), expand=True)


def show_turn(battle: Battle, opponent_name: str, events: list[BattleEvent]) -> None:
    opp_header = Text()
    opp_header.append(opponent_name.upper(), style="bold red")
    opp_header.append("   ")
    opp_header.append_text(_team_dots(battle.opponent_team, battle.opponent_active))

    player_header = Text()
    player_header.append("YOU", style="bold green")
    player_header.append("   ")
    player_header.append_text(_team_dots(battle.player_team, battle.player_active))

    parts: list = [
        opp_header,
        _pokemon_card(battle.opponent_pokemon),
        Text(""),
        player_header,
        _pokemon_card(battle.player_pokemon),
    ]

    if events:
        parts.append(Text(""))
        parts.append(Text("Events", style="bold underline"))
        for ev in events:
            parts.append(_event_line(ev))

    console.print(Panel(Group(*parts), title=f"Turn {battle.turn_count}", box=box.ROUNDED, padding=(0, 1), expand=False))


def show_move_menu(pokemon: Pokemon, can_switch: bool = True) -> None:
    body = Text()
    for i, move in enumerate(pokemon.moves):
        row = Text()
        row.append(f"  {i + 1}. ", style="bold")
        row.append(f"{move.name.replace('-', ' ').title():16s}")
        row.append("  ")
        badge = _type_badge(move.type)
        row.append_text(badge)
        row.append(" " * max(0, 10 - badge.cell_len))
        row.append("  ")
        pow_str = f"Pow {move.power:>3}" if move.power > 0 else "—      "
        row.append(pow_str)
        row.append("   ")
        acc_str = f"Acc {move.accuracy:>3}" if move.accuracy > 0 else "—      "
        row.append(acc_str)
        row.append("   ")
        pp_color = "green" if move.current_pp > move.pp // 4 else "red"
        row.append(f"{move.current_pp:>2}/{move.pp:<2}", style=pp_color)
        body.append_text(row)
        if i < len(pokemon.moves) - 1:
            body.append("\n")
    if can_switch:
        body.append("\n\n")
        body.append(f"  {len(pokemon.moves) + 1}. Switch Pokémon", style="cyan")
    title = f"{pokemon.name.title()}'s Moves"
    console.print(Panel(body, title=title, box=box.ROUNDED, padding=(0, 1), expand=False))


def show_switch_menu(team: list[Pokemon], active_index: int) -> None:
    body = Text()
    shown = 0
    for i, poke in enumerate(team):
        if i == active_index:
            continue
        if shown > 0:
            body.append("\n")
        shown += 1
        row = Text()
        row.append(f"  {i + 1}. ", style="bold")
        row.append(f"{poke.name.title():12s}  ")
        if not poke.is_alive:
            row.append("(fainted)", style="red")
        else:
            row.append_text(_hp_bar(poke.current_hp, poke.max_hp, width=16))
            row.append("  ")
            row.append_text(_status_text(poke.status))
        body.append_text(row)
    body.append("\n\n")
    body.append("  0. Back", style="dim")
    console.print(Panel(body, title="Switch Pokémon", box=box.ROUNDED, padding=(0, 1), expand=False))


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
