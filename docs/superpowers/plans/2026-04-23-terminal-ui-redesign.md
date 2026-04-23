# Terminal UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `src/cli/display.py` so each battle turn renders as a single framed "turn card" with minimalist stat cards (team dots, type badges, block-character HP bars, status/stage lines), plus framed move and switch menus.

**Architecture:** All changes in `src/cli/display.py`, one call-site swap in `src/cli/app.py`, one new test file `tests/cli/test_display.py`. Display remains a pure side-effect on a module-level `rich.Console`. No engine or AI changes.

**Tech Stack:** Python 3.12, `rich` (Panel, Text, Table, Console), pytest.

**Spec:** `docs/superpowers/specs/2026-04-23-terminal-ui-redesign-design.md`

---

## File Structure

- **Rewrite** `src/cli/display.py` — single module, ~200 lines, holds the palette map, private helpers, and four public `show_*` functions.
- **Modify** `src/cli/app.py` — swap the per-turn render call, replace the inline Full Restore print with a synthetic `BattleEvent`, drop dead imports.
- **Create** `tests/cli/test_display.py` — presence-based tests using `Console(record=True)`.

Field name crib sheet (verified in-repo):
- `Pokemon.name: str` (lowercase e.g. `"garchomp"`), `.types: list[str]` (lowercase), `.level: int`, `.current_hp: int`, `.max_hp: int`, `.status: Status`, `.stat_stages: dict[str, int]` with keys `"attack" | "defense" | "sp_attack" | "sp_defense" | "speed"`, `.moves: list[Move]`, `.is_alive: bool`.
- `Move.name: str` (e.g. `"dark-pulse"`), `.type: str`, `.power: int` (0 when N/A), `.accuracy: int` (0 when N/A), `.pp: int`, `.current_pp: int`.
- `Battle.player_team`, `.opponent_team`, `.player_active`, `.opponent_active`, `.turn_count`; properties `.player_pokemon`, `.opponent_pokemon`.
- `BattleEvent(event_type, source, target, message, damage, effectiveness)`; `EventType` includes `DAMAGE, MISS, STATUS, STAT_CHANGE, FAINT, SWITCH, EFFECTIVENESS, CRITICAL, END_OF_TURN, CANT_ACT, ITEM_USED, RECOIL, DRAIN, HEAL`.

---

## Task 1: Type-color palette and `_type_badge`

**Files:**
- Modify: `src/cli/display.py` (add constants + helper, keep existing code for now)
- Test: `tests/cli/test_display.py` (create)

- [ ] **Step 1: Write the failing tests**

Create `tests/cli/test_display.py`:

```python
from rich.console import Console
from src.cli.display import _type_badge, TYPE_COLORS


def _render(renderable) -> str:
    console = Console(record=True, width=100, force_terminal=True)
    console.print(renderable)
    return console.export_text()


def test_type_badge_contains_uppercase_name():
    output = _render(_type_badge("dragon"))
    assert "DRAGON" in output


def test_type_badge_has_brackets():
    output = _render(_type_badge("dark"))
    assert "[" in output and "]" in output


def test_type_colors_has_all_gen4_types():
    expected = {
        "normal", "fire", "water", "electric", "grass", "ice",
        "fighting", "poison", "ground", "flying", "psychic", "bug",
        "rock", "ghost", "dragon", "dark", "steel",
    }
    assert set(TYPE_COLORS.keys()) == expected
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/cli/test_display.py -v
```
Expected: ImportError on `_type_badge` / `TYPE_COLORS` — tests fail.

- [ ] **Step 3: Implement**

Add to the top of `src/cli/display.py` (after the existing imports):

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/cli/test_display.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/cli/display.py tests/cli/test_display.py
git commit -m "feat(display): add type-color palette and _type_badge helper"
```

---

## Task 2: Block-character HP bar

**Files:**
- Modify: `src/cli/display.py` (replace existing `_hp_bar`, keep `_hp_color`)
- Test: `tests/cli/test_display.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/cli/test_display.py`:

```python
from src.cli.display import _hp_bar, _hp_color


def test_hp_color_tiers():
    assert _hp_color(1.0) == "green"
    assert _hp_color(0.51) == "green"
    assert _hp_color(0.50) == "yellow"
    assert _hp_color(0.21) == "yellow"
    assert _hp_color(0.20) == "red"
    assert _hp_color(0.0) == "red"


def test_hp_bar_full_is_all_filled():
    output = _render(_hp_bar(280, 280, width=24))
    assert output.count("█") == 24
    assert "░" not in output
    assert "280/280" in output.replace(" ", "")
    assert "100%" in output


def test_hp_bar_empty_is_all_unfilled():
    output = _render(_hp_bar(0, 280, width=24))
    assert output.count("░") == 24
    assert "█" not in output
    assert "0/280" in output.replace(" ", "")
    assert "0%" in output


def test_hp_bar_half_is_half_filled():
    output = _render(_hp_bar(140, 280, width=24))
    assert output.count("█") == 12
    assert output.count("░") == 12
    assert "50%" in output
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/cli/test_display.py::test_hp_bar_full_is_all_filled -v
```
Expected: `█` assertion fails (existing bar uses `|`).

- [ ] **Step 3: Replace `_hp_bar` in `src/cli/display.py`**

Keep `_hp_color` as-is. Replace `_hp_bar` with:

```python
def _hp_bar(current: int, maximum: int, width: int = 24) -> Text:
    pct = current / max(maximum, 1)
    filled = int(round(pct * width))
    filled = max(0, min(width, filled))
    color = _hp_color(pct)
    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * (width - filled), style="dim")
    bar.append(f"  {current} / {maximum}   {int(pct * 100)}%")
    return bar
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/cli/test_display.py -v
```
Expected: all tests in this file pass.

- [ ] **Step 5: Commit**

```bash
git add src/cli/display.py tests/cli/test_display.py
git commit -m "feat(display): block-character HP bar with color tiers"
```

---

## Task 3: Status and stat-stage helpers

**Files:**
- Modify: `src/cli/display.py` (rework `_status_text`, add `_stages_text`)
- Test: `tests/cli/test_display.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/cli/test_display.py`:

```python
from src.engine.pokemon import Pokemon, Status
from src.cli.display import _status_text, _stages_text


def _make_pokemon(**overrides) -> Pokemon:
    defaults = dict(
        name="darkrai",
        types=["dark"],
        level=100,
        base_stats={"hp": 70, "attack": 90, "defense": 90,
                    "sp_attack": 135, "sp_defense": 90, "speed": 125},
        moves=[],
        ability="bad-dreams",
        item=None,
    )
    defaults.update(overrides)
    return Pokemon(**defaults)


def test_status_text_none_is_dash():
    assert "—" in _render(_status_text(Status.NONE))


def test_status_text_burn_shows_brn():
    assert "BRN" in _render(_status_text(Status.BURN))


def test_status_text_bad_poison_shows_tox():
    assert "TOX" in _render(_status_text(Status.BAD_POISON))


def test_stages_text_all_zero_is_dash():
    poke = _make_pokemon()
    assert "—" in _render(_stages_text(poke))


def test_stages_text_shows_nonzero_only():
    poke = _make_pokemon()
    poke.stat_stages["attack"] = 2
    poke.stat_stages["speed"] = -1
    out = _render(_stages_text(poke))
    assert "Atk +2" in out
    assert "Spe -1" in out
    assert "Def" not in out
    assert "SpA" not in out
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/cli/test_display.py -v -k "status_text or stages_text"
```
Expected: existing `_status_text` returns a markup string (not a `Text`); some tests fail. `_stages_text` doesn't exist yet.

- [ ] **Step 3: Replace `_status_text` and add `_stages_text` in `src/cli/display.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/cli/test_display.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/cli/display.py tests/cli/test_display.py
git commit -m "feat(display): status and stat-stage helpers returning Text"
```

---

## Task 4: Team status dots

**Files:**
- Modify: `src/cli/display.py` (add `_team_dots`)
- Test: `tests/cli/test_display.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/cli/test_display.py`:

```python
from src.cli.display import _team_dots


def test_team_dots_all_alive_six_filled():
    team = [_make_pokemon() for _ in range(6)]
    out = _render(_team_dots(team, active_index=0))
    assert out.count("●") == 6
    assert "○" not in out


def test_team_dots_one_fainted():
    team = [_make_pokemon() for _ in range(6)]
    team[3].current_hp = 0
    out = _render(_team_dots(team, active_index=0))
    assert out.count("●") == 5
    assert out.count("○") == 1


def test_team_dots_short_team_pads_to_six():
    team = [_make_pokemon() for _ in range(3)]
    out = _render(_team_dots(team, active_index=0))
    total_dots = out.count("●") + out.count("○")
    assert total_dots == 6
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/cli/test_display.py -v -k "team_dots"
```
Expected: ImportError on `_team_dots`.

- [ ] **Step 3: Add `_team_dots` to `src/cli/display.py`**

```python
def _team_dots(team, active_index: int) -> Text:
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/cli/test_display.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/cli/display.py tests/cli/test_display.py
git commit -m "feat(display): team status dots with HP-tier colors"
```

---

## Task 5: Per-event line formatting

**Files:**
- Modify: `src/cli/display.py` (add `_event_line`)
- Test: `tests/cli/test_display.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/cli/test_display.py`:

```python
from src.engine.battle import BattleEvent, EventType
from src.cli.display import _event_line


def test_event_line_damage_has_damage_suffix():
    ev = BattleEvent(event_type=EventType.DAMAGE, message="Dark Pulse hit!", damage=84)
    out = _render(_event_line(ev))
    assert "Dark Pulse hit!" in out
    assert "84" in out


def test_event_line_effectiveness_super():
    ev = BattleEvent(
        event_type=EventType.EFFECTIVENESS,
        message="It's super effective!",
        effectiveness=2.0,
    )
    out = _render(_event_line(ev))
    assert "super effective" in out


def test_event_line_item_used():
    ev = BattleEvent(
        event_type=EventType.ITEM_USED,
        message="Cynthia used a Full Restore!",
    )
    out = _render(_event_line(ev))
    assert "Full Restore" in out


def test_event_line_starts_with_bullet():
    ev = BattleEvent(event_type=EventType.FAINT, message="Garchomp fainted!")
    out = _render(_event_line(ev))
    assert "▸" in out
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/cli/test_display.py -v -k "event_line"
```
Expected: ImportError on `_event_line`.

- [ ] **Step 3: Add `_event_line` to `src/cli/display.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/cli/test_display.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/cli/display.py tests/cli/test_display.py
git commit -m "feat(display): unified _event_line formatter with bullet + damage suffix"
```

---

## Task 6: Pokemon card panel

**Files:**
- Modify: `src/cli/display.py` (add `_pokemon_card`)
- Test: `tests/cli/test_display.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/cli/test_display.py`:

```python
from src.cli.display import _pokemon_card


def test_pokemon_card_has_name_level_and_types():
    poke = _make_pokemon(name="garchomp", types=["dragon", "ground"], level=100)
    out = _render(_pokemon_card(poke))
    assert "Garchomp" in out
    assert "Lv100" in out
    assert "DRAGON" in out
    assert "GROUND" in out


def test_pokemon_card_has_hp_bar():
    poke = _make_pokemon()
    out = _render(_pokemon_card(poke))
    assert "█" in out
    assert "100%" in out


def test_pokemon_card_shows_status_and_stages():
    poke = _make_pokemon()
    poke.status = Status.BURN
    poke.stat_stages["attack"] = 1
    out = _render(_pokemon_card(poke))
    assert "BRN" in out
    assert "Atk +1" in out
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/cli/test_display.py -v -k "pokemon_card"
```
Expected: ImportError on `_pokemon_card`.

- [ ] **Step 3: Add `_pokemon_card` to `src/cli/display.py`**

```python
def _pokemon_card(pokemon) -> Panel:
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
```

Add `from rich import box` to the imports at the top of the file if not already present.

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/cli/test_display.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/cli/display.py tests/cli/test_display.py
git commit -m "feat(display): _pokemon_card inner panel (name/level/types/HP/status/stages)"
```

---

## Task 7: `show_turn` public function

**Files:**
- Modify: `src/cli/display.py` (add `show_turn`, delete `show_battle_state`, delete `show_events`)
- Test: `tests/cli/test_display.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/cli/test_display.py`:

```python
from src.engine.battle import Battle
from src.cli.display import show_turn


def _make_team(size: int = 6) -> list:
    return [_make_pokemon(name=f"mon{i}") for i in range(size)]


def test_show_turn_renders_turn_number_and_both_cards(capsys):
    battle = Battle(_make_team(), _make_team())
    battle.turn_count = 3
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_turn(battle, opponent_name="Cynthia", events=[])
    out = d.console.export_text()
    assert "Turn 3" in out
    assert "CYNTHIA" in out
    assert "YOU" in out
    assert out.count("█") > 0


def test_show_turn_renders_team_dots_for_both_sides():
    battle = Battle(_make_team(), _make_team())
    battle.opponent_team[2].current_hp = 0
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_turn(battle, opponent_name="Cynthia", events=[])
    out = d.console.export_text()
    assert out.count("●") + out.count("○") == 12


def test_show_turn_renders_events_with_bullets():
    battle = Battle(_make_team(), _make_team())
    events = [
        BattleEvent(event_type=EventType.DAMAGE, message="Dark Pulse hit!", damage=84),
        BattleEvent(event_type=EventType.FAINT, message="Mon2 fainted!"),
    ]
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_turn(battle, opponent_name="Cynthia", events=events)
    out = d.console.export_text()
    assert "Events" in out
    assert out.count("▸") == 2
    assert "84 damage" in out
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/cli/test_display.py -v -k "show_turn"
```
Expected: ImportError on `show_turn`.

- [ ] **Step 3: Add `show_turn` and delete the old functions**

In `src/cli/display.py`, add:

```python
def show_turn(battle, opponent_name: str, events: list[BattleEvent]) -> None:
    opponent_dots = _team_dots(battle.opponent_team, battle.opponent_active)
    player_dots = _team_dots(battle.player_team, battle.player_active)

    body = Text()

    opp_header = Text()
    opp_header.append(opponent_name.upper(), style="bold red")
    opp_header.append("   ")
    opp_header.append_text(opponent_dots)
    body.append_text(opp_header)
    body.append("\n")

    from io import StringIO
    tmp = Console(file=StringIO(), width=max(40, console.width - 6), force_terminal=True)
    tmp.print(_pokemon_card(battle.opponent_pokemon))
    body.append(tmp.file.getvalue().rstrip("\n"))

    body.append("\n\n")
    player_header = Text()
    player_header.append("YOU", style="bold green")
    player_header.append("        ")
    player_header.append_text(player_dots)
    body.append_text(player_header)
    body.append("\n")

    tmp2 = Console(file=StringIO(), width=max(40, console.width - 6), force_terminal=True)
    tmp2.print(_pokemon_card(battle.player_pokemon))
    body.append(tmp2.file.getvalue().rstrip("\n"))

    if events:
        body.append("\n\n")
        body.append(Text("Events", style="bold underline"))
        body.append("\n")
        for i, ev in enumerate(events):
            body.append_text(_event_line(ev))
            if i < len(events) - 1:
                body.append("\n")

    console.print(Panel(body, title=f"Turn {battle.turn_count}", box=box.ROUNDED, padding=(0, 1), expand=False))
```

Note: if the nested-panel `StringIO` approach renders awkwardly, the simpler fallback is to drop the inner Panel wrapper and format the Pokemon card inline. Prefer the nested approach first — it matches the mockup.

Delete the existing `show_battle_state` function and the existing `show_events` function from the file. Leave `show_move_menu`, `show_switch_menu`, `show_battle_result` untouched in this task.

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/cli/test_display.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/cli/display.py tests/cli/test_display.py
git commit -m "feat(display): show_turn renders one framed turn card per turn"
```

---

## Task 8: Framed move menu

**Files:**
- Modify: `src/cli/display.py` (replace `show_move_menu`)
- Test: `tests/cli/test_display.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/cli/test_display.py`:

```python
from src.engine.pokemon import Move, MoveCategory
from src.cli.display import show_move_menu


def _make_move(name="dark-pulse", type_="dark", power=80, accuracy=100, pp=15):
    return Move(
        name=name, type=type_, category=MoveCategory.SPECIAL,
        power=power, accuracy=accuracy, pp=pp, priority=0, effect=None,
    )


def test_show_move_menu_has_framed_header_and_columns():
    poke = _make_pokemon(moves=[
        _make_move("dark-pulse", "dark", 80, 100, 15),
        _make_move("nasty-plot", "dark", 0, 0, 20),
        _make_move("dream-eater", "psychic", 100, 100, 15),
        _make_move("dark-void", "dark", 0, 80, 10),
    ])
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_move_menu(poke, can_switch=True)
    out = d.console.export_text()
    assert "Dark Pulse" in out
    assert "DARK" in out
    assert "Pow 80" in out
    assert "Acc 100" in out
    assert "15/15" in out
    assert "Switch" in out
    assert "Moves" in out  # panel title


def test_show_move_menu_no_switch_hides_switch_row():
    poke = _make_pokemon(moves=[_make_move()])
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_move_menu(poke, can_switch=False)
    out = d.console.export_text()
    assert "Switch" not in out


def test_show_move_menu_status_move_shows_dashes_for_power():
    poke = _make_pokemon(moves=[_make_move("nasty-plot", "dark", 0, 0, 20)])
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_move_menu(poke, can_switch=False)
    out = d.console.export_text()
    assert "Nasty Plot" in out
    # power 0 and accuracy 0 should render as em dashes
    assert "—" in out
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/cli/test_display.py -v -k "show_move_menu"
```
Expected: existing `show_move_menu` fails the `Pow 80`, `Acc 100`, `Moves` panel title assertions.

- [ ] **Step 3: Replace `show_move_menu`**

```python
def show_move_menu(pokemon, can_switch: bool = True) -> None:
    body = Text()
    for i, move in enumerate(pokemon.moves):
        row = Text()
        row.append(f"  {i + 1}. ", style="bold")
        row.append(f"{move.name.replace('-', ' ').title():16s}")
        row.append("  ")
        row.append_text(_type_badge(move.type))
        row.append("   ")
        pow_str = f"Pow {move.power:>3}" if move.power > 0 else "—     "
        row.append(pow_str)
        row.append("   ")
        acc_str = f"Acc {move.accuracy:>3}" if move.accuracy > 0 else "—     "
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/cli/test_display.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/cli/display.py tests/cli/test_display.py
git commit -m "feat(display): framed move menu with type/power/accuracy/PP columns"
```

---

## Task 9: Framed switch menu

**Files:**
- Modify: `src/cli/display.py` (replace `show_switch_menu`)
- Test: `tests/cli/test_display.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/cli/test_display.py`:

```python
from src.cli.display import show_switch_menu


def test_show_switch_menu_lists_other_members_with_hp_bars():
    team = [_make_pokemon(name=f"mon{i}") for i in range(3)]
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_switch_menu(team, active_index=0)
    out = d.console.export_text()
    # active pokemon not in list
    assert "1. Mon0" not in out
    # other pokemon present
    assert "Mon1" in out
    assert "Mon2" in out
    # hp bar blocks rendered for alive
    assert out.count("█") > 0
    # back row present
    assert "0. Back" in out


def test_show_switch_menu_marks_fainted():
    team = [_make_pokemon(name=f"mon{i}") for i in range(3)]
    team[1].current_hp = 0
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_switch_menu(team, active_index=0)
    out = d.console.export_text()
    assert "(fainted)" in out


def test_show_switch_menu_panel_title():
    team = [_make_pokemon(name=f"mon{i}") for i in range(2)]
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_switch_menu(team, active_index=0)
    out = d.console.export_text()
    assert "Switch" in out
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/cli/test_display.py -v -k "show_switch_menu"
```
Expected: `0. Back` only matches if present; existing version prints `    0. Back` — that passes the substring. But `(fainted)` is in current code too. The panel title assertion fails (current version has no panel).

- [ ] **Step 3: Replace `show_switch_menu`**

```python
def show_switch_menu(team, active_index: int) -> None:
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/cli/test_display.py -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/cli/display.py tests/cli/test_display.py
git commit -m "feat(display): framed switch menu with HP bars and status"
```

---

## Task 10: Wire up `src/cli/app.py`

**Files:**
- Modify: `src/cli/app.py`
- Test: run existing integration tests

- [ ] **Step 1: Read current call site**

Open `src/cli/app.py` and locate the block containing `show_battle_state(...)` and the later `show_events(events)` call. Note the inline Full Restore print that currently happens between them:

```python
console.print(f"  [cyan]{opponent_name} used a Full Restore![/cyan]")
```

- [ ] **Step 2: Update imports**

Change:
```python
from src.cli.display import (
    show_battle_state, show_move_menu, show_switch_menu,
    show_events, show_battle_result,
)
```
to:
```python
from src.cli.display import (
    show_turn, show_move_menu, show_switch_menu, show_battle_result,
)
```

- [ ] **Step 3: Replace the render block**

Replace the `show_battle_state(...)` call near line 194 and the later `show_events(events)` call near line 213 with a single `show_turn(battle, opponent_name, events)` call placed where `show_events` used to be.

Specifically:
1. Delete the `show_battle_state(battle.player_pokemon, battle.opponent_pokemon, battle.turn_count, opponent_name)` call entirely.
2. Replace the Full Restore inline print:
   ```python
   console.print(f"  [cyan]{opponent_name} used a Full Restore![/cyan]")
   ```
   with the creation of a synthetic event appended to the events list before rendering. Concretely, wherever that line is, replace it with:
   ```python
   events.insert(0, BattleEvent(
       event_type=EventType.ITEM_USED,
       message=f"{opponent_name} used a Full Restore!",
   ))
   ```
   and add `from src.engine.battle import BattleEvent, EventType` to the imports if not already present.
3. Replace `show_events(events)` with `show_turn(battle, opponent_name, events)`.

- [ ] **Step 4: Run the full test suite**

```
pytest -v
```
Expected: all existing tests pass, all new display tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/cli/app.py
git commit -m "feat(cli): render each battle turn as one framed turn card"
```

---

## Task 11: Manual smoke test

**Files:** none changed — just visual verification.

- [ ] **Step 1: Launch the CLI**

```
python -m src.cli.app
```
Build a random team (fastest option) and battle a champion.

- [ ] **Step 2: Verify the visual target**

Confirm by eye:
- Turn card renders with a rounded border and `Turn N` title.
- Team dots: 6 per side, colored by HP, fainted members as `○`.
- Pokémon cards: name/level/type badges, block-char HP bar with color, status, stat stages.
- Events section bullets with `▸`; damage appears to the right on DAMAGE lines.
- Move menu panel shows Type / Pow / Acc / PP columns.
- Switch menu panel shows HP bar per Pokémon.
- Full Restore use by the AI shows up inside the turn card as an event, not outside.

- [ ] **Step 3: No commit**

If any visual issue shows up, fix it in `src/cli/display.py`, rerun the affected tests, and commit the fix separately. Otherwise the task is complete.

---

## Self-Review Notes

- **Spec coverage:**
  - Turn card layout → Task 7.
  - Team dots → Task 4.
  - Type badges → Task 1.
  - Block-char HP bar → Task 2.
  - Status + stages → Task 3.
  - Event bullets + damage suffix → Task 5.
  - Pokémon cards → Task 6.
  - Framed move menu → Task 8.
  - Framed switch menu → Task 9.
  - Synthetic ITEM_USED event + app.py swap → Task 10.
  - Manual visual verification → Task 11.
  - `show_battle_result` polish — spec says "kept, cleaned up"; no meaningful change required, so no task. If any polish is wanted later, add a follow-up.

- **Placeholders:** none. All steps show concrete code or concrete commands.

- **Type consistency:** all helpers return `Text` or `Panel`; `_pokemon_card` composes child helpers with matching types. `show_turn` accepts `(battle, opponent_name, events)` and `app.py` Task 10 calls it with exactly that signature. `BattleEvent` fields used (`event_type`, `message`, `damage`, `effectiveness`) match the dataclass in `src/engine/battle.py`.
