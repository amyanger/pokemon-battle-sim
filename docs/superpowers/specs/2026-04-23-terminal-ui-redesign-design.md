# Terminal UI Redesign — Design Spec

## Overview

Redesign `src/cli/display.py` so each battle turn renders as a single framed "turn card" instead of a flat scroll of disjointed lines. Goals: clean visual hierarchy, game-like feel, no regressions in information shown. No engine or AI changes.

## Scope

**In:**
- Replace the current scroll-of-lines display with a per-turn framed panel.
- Minimalist stat cards for each active Pokémon (name, level, type badges, HP bar, status, stat stages).
- Team status dots (6 per side) showing alive/fainted state.
- Framed move and switch menus with richer data columns.
- Type-color palette and Unicode block HP bars.
- Basic display-layer tests that assert structural elements appear in output.

**Out (explicitly deferred):**
- Stable `Live`/`Layout` UI. We chose panel-per-turn scrolling on purpose; revisit later if desired.
- ASCII sprites or type emoji. Minimalist text-based layout only.
- ASCII fallback for legacy terminals. Assumes a Unicode-capable terminal.
- Changes to the battle engine, AI, or CLI flow in `src/cli/app.py` beyond the call-site swap described below.

## User-Facing Layout

Each turn prints exactly one framed turn card, then (when input is needed) a framed move or switch menu, then a `> ` prompt. Approximate rendering:

```
╭─ Turn 3 ──────────────────────────────────────────────────╮
│  CYNTHIA   ● ● ● ○ ○ ○                                    │
│  ┌───────────────────────────────────────────────────┐    │
│  │ Garchomp            Lv100   [DRAGON] [GROUND]     │    │
│  │ HP ████████████████░░░░░░░  214 / 286   75%       │    │
│  │ Status —             Stages  Atk +1               │    │
│  └───────────────────────────────────────────────────┘    │
│                                                           │
│  YOU       ● ● ● ● ● ●                                    │
│  ┌───────────────────────────────────────────────────┐    │
│  │ Darkrai             Lv100   [DARK]                │    │
│  │ HP ███████████████████████  280 / 280  100%       │    │
│  │ Status —             Stages —                     │    │
│  └───────────────────────────────────────────────────┘    │
│                                                           │
│  Events                                                   │
│    ▸ Darkrai used Dark Pulse.                             │
│    ▸ It's super effective!        84 damage               │
│    ▸ Garchomp used Earthquake.                            │
│    ▸ Darkrai avoided the attack.                          │
╰───────────────────────────────────────────────────────────╯

╭─ Darkrai's Moves ─────────────────────────────────────────╮
│  1. Dark Pulse     [DARK]       Pow 80   Acc 100   15/15  │
│  2. Nasty Plot     [DARK]       —        —         20/20  │
│  3. Dream Eater    [PSYCHIC]    Pow 100  Acc 100   15/15  │
│  4. Dark Void      [DARK]       —        Acc  80   10/10  │
│                                                           │
│  5. Switch Pokémon                                        │
╰───────────────────────────────────────────────────────────╯
>
```

### Visual details

- **Turn card:** outer `rich.Panel` with rounded box, title `Turn N`.
- **Team dots:** `●` for alive, `○` for fainted. Alive dots colored by HP tier of that Pokémon (`green >50%`, `yellow >20%`, `red` otherwise). Fainted dots are dim. Active Pokémon dot is bold.
- **Pokémon card:** inner `Panel` with square box, containing three lines — identity (name, level, type badges), HP bar, status/stages.
- **Type badges:** `[DRAGON]`, `[GROUND]`, etc. Colored text using the Gen 4 type palette (`TYPE_COLORS` map, 17 entries, no Fairy).
- **HP bar:** width 24. Filled cells `█` colored by HP tier; empty cells `░` in dim style. Trailing `cur / max  pct%`.
- **Status:** colored abbreviation (`BRN`, `PAR`, `PSN`, `TOX`, `FRZ`, `SLP`) or `—` when none.
- **Stat stages:** compact inline list (`Atk +1  Spe -1`); `—` when all zero. Stages shown: Atk, Def, SpA, SpD, Spe, Acc, Eva (non-zero only).
- **Events:** bulleted with `▸`. Existing color mapping per `EventType` is preserved (critical=yellow, super-effective=green, faint=red, etc.). For `EventType.DAMAGE`, damage number is right-aligned in the line.

## Code Structure

All changes live in `src/cli/display.py` plus one call-site change in `src/cli/app.py` and one new test file. No new modules.

### Public functions

- `show_turn(battle: Battle, opponent_name: str, events: list[BattleEvent]) -> None`
  - Renders one complete turn card. Reads `battle.player_team`, `battle.opponent_team`, `battle.player_active`, `battle.opponent_active`, `battle.turn_count`.
  - Replaces the current `show_battle_state(...)` + `show_events(events)` pair.
- `show_move_menu(pokemon: Pokemon, can_switch: bool = True) -> None`
  - Reworked as a framed panel. Columns: number, move name, type badge, power (or `—`), accuracy (or `—`), PP `cur/max`. Switch option as the last numbered line.
- `show_switch_menu(team: list[Pokemon], active_index: int) -> None`
  - Reworked as a framed panel. For each non-active Pokémon: number, name, HP bar, status. Fainted Pokémon shown dim with `(fainted)`. Trailing `0. Back` row.
- `show_battle_result(winner: str, turn_count: int, player_fainted: int, opponent_fainted: int, damage_dealt: dict[str, int]) -> None`
  - Kept. Minor polish: title line inside a rounded panel, summary in a `rich.Table` (current behavior).

### Private helpers

- `_pokemon_card(pokemon: Pokemon) -> Panel`
- `_team_dots(team: list[Pokemon], active_index: int) -> Text`
- `_hp_bar(current: int, maximum: int, width: int = 24) -> Text`
- `_type_badge(type_name: str) -> Text`
- `_stages_text(pokemon: Pokemon) -> Text`
- `_status_text(status: Status) -> Text`
- `_event_line(event: BattleEvent) -> Text`
- `TYPE_COLORS: dict[str, str]` — type → rich color name.

### Call-site change (`src/cli/app.py`)

- Replace:
  ```python
  show_battle_state(battle.player_pokemon, battle.opponent_pokemon, battle.turn_count, opponent_name)
  # ...
  show_events(events)
  ```
  with:
  ```python
  show_turn(battle, opponent_name, events)
  ```
- The ad-hoc Full Restore line currently printed outside events:
  ```python
  console.print(f"  [cyan]{opponent_name} used a Full Restore![/cyan]")
  ```
  becomes a synthetic `BattleEvent(event_type=EventType.ITEM_USED, message=...)` prepended to `events` so it renders inside the turn card. (This also covers the missing handler for `ITEM_USED` in the current `show_events`.)
- The "X fainted! Choose next Pokemon" inline prompt is unchanged; only the switch menu panel it precedes is reworked.
- Removes now-unused imports of `show_battle_state` and `show_events` from `src/cli/display.py`. These functions are deleted.

### Data flow

Unchanged. Display remains a pure side-effect on a module-level `rich.Console`. No engine or AI coupling.

### Error handling

Display is passive. No new error paths. Inputs are trusted (come from engine state). No defensive validation added.

## Testing

New file: `tests/cli/test_display.py`. No existing display tests to break.

- Use `rich.Console(record=True)` and assert on substrings in `console.export_text()` — presence checks, not snapshots.
- Cases:
  - `show_turn` prints the turn number, both Pokémon names, and 12 team-dot characters total (6 per side).
  - `show_move_menu` prints each move name and PP string.
  - `show_switch_menu` prints `(fainted)` for fainted members and the `0. Back` row.
  - `_hp_bar` at 100% contains 24 `█`; at 0% contains 24 `░`; tier colors apply.
  - `_team_dots` with a fainted member produces 5 `●` and 1 `○`.
  - `_type_badge("dragon")` contains `DRAGON` and the dragon color style applies.
- Existing integration tests (`tests/test_integration.py`) don't assert on display output and continue to pass.

## Non-Goals / Risks

- Terminals narrower than ~70 columns will wrap ugly. Not addressed; not a target.
- If event volume in a turn grows (e.g., multi-hit moves later), the turn card can get tall. That's acceptable — the panel grows with content.
- If a future feature adds stable-layout mode, `show_turn` is the right seam to swap the rendering backend. No code needs to care beyond this function.

## Files Touched

- `src/cli/display.py` — rewritten.
- `src/cli/app.py` — two-line swap at the render site, plus synthetic Full Restore event.
- `tests/cli/test_display.py` — new file.
