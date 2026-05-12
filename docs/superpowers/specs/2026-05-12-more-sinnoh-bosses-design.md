# More Sinnoh Bosses — Design Spec

**Date:** 2026-05-12
**Status:** Approved, pending implementation plan

## Goal

Extend the champion-preset roster from the current 5 trainers (Cynthia + 4 Elite Four, each with a rematch — 10 teams) to include all 8 Sinnoh gym leaders and their rematches (16 new teams). Final roster: **13 trainers, 26 teams**.

## Scope

**In:** 8 gym leaders × (base + rematch) = 16 new preset teams, exposed in both the opponent picker and the player-team picker.

**Out (explicit non-goals, YAGNI):**
- Cyrus, Galactic commanders (Jupiter, Saturn), rival Barry
- Post-game "fight area" variants (e.g., `leader_volkner_fight_area.json`, `elite_four_flint_fight_area.json`)
- Auto-discovery / glob-based loader
- New personality profiles beyond the existing 4
- Cross-region champions (Lance, Steven, etc.)

## Architecture

### Files touched

| File | Change |
|---|---|
| `src/data/champion_loader.py` | Extend `_CHAMPION_FILES` from 10 → 26 entries. Add `TrainerEntry` dataclass and `list_trainers()` method that groups base + rematch by trainer. |
| `src/ai/personality.py` | Extend `_CHAMPION_PERSONALITIES` with 8 new mappings. |
| `src/cli/team_builder.py` | Replace flat menus in `build_opponent_team` and `_champion_preset` with one shared two-level helper (trainer → variant). |
| `tests/data/test_champion_loader.py` | New tests for grouping, ordering, and missing-file filtering. |
| `tests/ai/test_personality.py` | New test that every new leader maps to the expected profile. |

### New abstraction

A single dataclass in `champion_loader.py`:

```python
@dataclass
class TrainerEntry:
    display_name: str                  # "Roark"
    role: str                          # "Gym Leader" | "Elite Four" | "Champion"
    variants: list[tuple[str, str]]    # [("base", "leader_roark"), ("rematch", "leader_roark_rematch")]
```

### Roster (canon progression order)

| # | Trainer | Role | Files |
|---|---|---|---|
| 1 | Roark | Gym Leader | `leader_roark`, `leader_roark_rematch` |
| 2 | Gardenia | Gym Leader | `leader_gardenia`, `leader_gardenia_rematch` |
| 3 | Fantina | Gym Leader | `leader_fantina`, `leader_fantina_rematch` |
| 4 | Maylene | Gym Leader | `leader_maylene`, `leader_maylene_rematch` |
| 5 | Wake | Gym Leader | `leader_wake`, `leader_wake_rematch` |
| 6 | Byron | Gym Leader | `leader_byron`, `leader_byron_rematch` |
| 7 | Candice | Gym Leader | `leader_candice`, `leader_candice_rematch` |
| 8 | Volkner | Gym Leader | `leader_volkner`, `leader_volkner_rematch` |
| 9 | Aaron | Elite Four | `elite_four_aaron`, `elite_four_aaron_rematch` |
| 10 | Bertha | Elite Four | `elite_four_bertha`, `elite_four_bertha_rematch` |
| 11 | Flint | Elite Four | `elite_four_flint`, `elite_four_flint_rematch` |
| 12 | Lucian | Elite Four | `elite_four_lucian`, `elite_four_lucian_rematch` |
| 13 | Cynthia | Champion | `champion_cynthia`, `champion_cynthia_rematch` |

Display names come directly from the JSON `name` field (verified: Roark, Gardenia, Fantina, Maylene, Wake, Byron, Candice, Volkner — match `_CHAMPION_PERSONALITIES` keys exactly).

### Personality mappings (extension to `_CHAMPION_PERSONALITIES`)

Mapped to the four existing profiles (`balanced`, `aggressive`, `defensive`, `tactical`) based on canon flavor:

| Leader | Type | Profile | Rationale |
|---|---|---|---|
| Roark | Rock | defensive | First leader; Sturdy, slow rock pivots |
| Gardenia | Grass | aggressive | Hyper-offensive grass (Roserade) |
| Fantina | Ghost | tactical | Status- and trick-driven, hypnosis + dream eater patterns |
| Maylene | Fighting | aggressive | Lucario brawler, pure offense |
| Wake | Water | balanced | Generalist water, mixed offense/utility |
| Byron | Steel | defensive | Bastiodon walls; iron defense lineage |
| Candice | Ice | aggressive | Frail but hard-hitting ice |
| Volkner | Electric | tactical | Methodical electric coverage |

## Data flow

### Opponent picker (`team_builder.build_opponent_team`)

```
loader.list_trainers()  →  [TrainerEntry × ≤13]   # filtered by Path.exists()

Prompt 1: "Pick a trainer (1–N, or N+1 = Random team)"
  → user picks trainer index, or "Random team" → existing random-team path

Prompt 2 (only if picked trainer has >1 variant): "1 = base, 2 = rematch"
  → user picks variant

loader.load_champion(chosen_filename)  →  ChampionTeam   # unchanged
return champ_data.name, team, champ_data.items
```

### Player-team picker (`_champion_preset`)

Same two-level flow, sharing one helper. The helper returns the selected `ChampionTeam` (or filename); each caller wraps its own surrounding logic.

## Error handling

No new failure modes. Existing fallbacks cover the additions:

- `../pokeplatinum/` missing → `list_trainers()` returns `[]` → opponent menu shows only "Random team" (same as today's behavior when `list_champions()` is empty).
- Individual JSON file missing → that variant is filtered by `Path.exists()`. If both variants of a trainer are missing, the trainer drops from the list entirely.
- Personality lookup falls back to `"balanced"` for any unknown name (today's behavior in `get_champion_personality`).

## Testing

| Test | Location | Checks |
|---|---|---|
| `test_list_trainers_groups_variants` | `tests/data/test_champion_loader.py` | Each `TrainerEntry` groups base+rematch into one entry; trainers without rematches yield one-variant entries. |
| `test_list_trainers_canon_order` | same | Output order: Roark precedes Gardenia precedes … Volkner; gym leaders precede Elite Four precedes Cynthia. |
| `test_list_trainers_filters_missing_files` | same | Files not present on disk are excluded (uses `tmp_path` fixture with a synthetic decomp dir). |
| `test_personality_covers_all_new_leaders` | `tests/ai/test_personality.py` | Every new leader name resolves to the expected profile (not the `balanced` fallback). |
| `test_load_new_leader_file` | `tests/data/test_champion_loader.py` | Smoke-load `leader_roark.json` from the real decomp and assert party species/levels. Follows the same pattern as existing `test_load_cynthia` / `test_load_aaron` — requires the decomp to be present (no skip). |

Manual smoke test post-implementation: run `python -m src.cli.app`, walk through both menus, fight Byron's rematch.

## Open questions

None. All decisions resolved in brainstorming:
- Roster: gym leaders only (no Cyrus, commanders, Barry).
- Menu shape: two-level (trainer → variant), shared by both opponent and player pickers.
- Personalities: map all 8 new leaders to existing 4 profiles.
- Loader strategy: extend the hardcoded `_CHAMPION_FILES` list explicitly.
