# More Sinnoh Bosses Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the champion-preset roster with all 8 Sinnoh gym leaders + rematches (16 new teams, 26 total), exposed via a shared two-level (trainer → variant) picker used by both the opponent menu and the player-team preset menu.

**Architecture:** Extend `_CHAMPION_FILES` and `_CHAMPION_PERSONALITIES` in place. Add a small `TrainerEntry` dataclass and `list_trainers()` method to `ChampionLoader` that groups base+rematch pairs in canon progression order. Refactor `team_builder.py` to share one two-level selection helper between opponent and player pickers. Tests follow existing patterns (real-decomp smoke loads + `tmp_path` fixtures for filtering).

**Tech Stack:** Python 3.12+, `pytest`, `typer`/`rich` for the CLI (no test coverage needed for interactive prompts — pure selection logic is extracted and unit-tested).

**Spec:** `docs/superpowers/specs/2026-05-12-more-sinnoh-bosses-design.md`

---

## File Structure

**Modified:**
- `src/data/champion_loader.py` — extend `_CHAMPION_FILES` (10 → 26 entries); add `TrainerEntry` dataclass and `list_trainers()` method
- `src/ai/personality.py` — extend `_CHAMPION_PERSONALITIES` with 8 new mappings
- `src/cli/team_builder.py` — replace flat menus in `build_opponent_team` and `_champion_preset` with shared two-level helper `_pick_trainer_variant()`
- `tests/data/test_champion_loader.py` — add 5 new tests
- `tests/ai/test_personality.py` — add 1 new test

**Why these splits:** `champion_loader.py` already owns "what trainer data is available" — `list_trainers()` belongs there alongside `list_champions()`. `personality.py` owns name→profile mapping — new entries go there. `team_builder.py` owns CLI flow — the new shared helper is private to that module.

---

## Task 1: Extend `_CHAMPION_FILES` with 16 new gym leader entries

**Files:**
- Modify: `src/data/champion_loader.py:9-20` (the `_CHAMPION_FILES` list)
- Test: `tests/data/test_champion_loader.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/data/test_champion_loader.py`:

```python
def test_list_champions_includes_all_gym_leaders():
    loader = ChampionLoader()
    champs = loader.list_champions()
    expected_leaders = [
        "leader_roark", "leader_roark_rematch",
        "leader_gardenia", "leader_gardenia_rematch",
        "leader_fantina", "leader_fantina_rematch",
        "leader_maylene", "leader_maylene_rematch",
        "leader_wake", "leader_wake_rematch",
        "leader_byron", "leader_byron_rematch",
        "leader_candice", "leader_candice_rematch",
        "leader_volkner", "leader_volkner_rematch",
    ]
    for name in expected_leaders:
        assert name in champs, f"{name} missing from list_champions()"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/data/test_champion_loader.py::test_list_champions_includes_all_gym_leaders -v`
Expected: FAIL — `leader_roark missing from list_champions()`.

- [ ] **Step 3: Extend `_CHAMPION_FILES`**

In `src/data/champion_loader.py`, replace the existing `_CHAMPION_FILES` list (lines 9-20):

```python
_CHAMPION_FILES = [
    # Gym Leaders (canon progression order)
    "leader_roark",
    "leader_roark_rematch",
    "leader_gardenia",
    "leader_gardenia_rematch",
    "leader_fantina",
    "leader_fantina_rematch",
    "leader_maylene",
    "leader_maylene_rematch",
    "leader_wake",
    "leader_wake_rematch",
    "leader_byron",
    "leader_byron_rematch",
    "leader_candice",
    "leader_candice_rematch",
    "leader_volkner",
    "leader_volkner_rematch",
    # Elite Four
    "elite_four_aaron",
    "elite_four_aaron_rematch",
    "elite_four_bertha",
    "elite_four_bertha_rematch",
    "elite_four_flint",
    "elite_four_flint_rematch",
    "elite_four_lucian",
    "elite_four_lucian_rematch",
    # Champion
    "champion_cynthia",
    "champion_cynthia_rematch",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/data/test_champion_loader.py -v`
Expected: PASS — all existing tests plus the new one.

- [ ] **Step 5: Add smoke-load test for one new file**

Add to `tests/data/test_champion_loader.py`:

```python
def test_load_roark():
    loader = ChampionLoader()
    team = loader.load_champion("leader_roark")
    assert team.name == "Roark"
    assert len(team.party) >= 2  # Roark has Geodude + Onix + Cranidos
    assert team.party[0].species == "geodude"
    assert team.party[0].level == 12
```

- [ ] **Step 6: Run new test to verify it passes**

Run: `pytest tests/data/test_champion_loader.py::test_load_roark -v`
Expected: PASS (reads from real decomp at `../pokeplatinum/`).

- [ ] **Step 7: Commit**

```bash
git add src/data/champion_loader.py tests/data/test_champion_loader.py
git commit -m "feat(data): add 8 Sinnoh gym leaders + rematches to _CHAMPION_FILES"
```

---

## Task 2: Add `TrainerEntry` dataclass and `list_trainers()` method

**Files:**
- Modify: `src/data/champion_loader.py` (add `TrainerEntry` dataclass after `ChampionTeam`; add `list_trainers()` method to `ChampionLoader`)
- Test: `tests/data/test_champion_loader.py`

- [ ] **Step 1: Write the failing grouping test**

Add to `tests/data/test_champion_loader.py`:

```python
def test_list_trainers_groups_base_and_rematch():
    loader = ChampionLoader()
    trainers = loader.list_trainers()

    by_name = {t.display_name: t for t in trainers}
    assert "Roark" in by_name
    roark = by_name["Roark"]
    assert roark.role == "Gym Leader"
    variant_labels = [label for label, _filename in roark.variants]
    variant_files = [filename for _label, filename in roark.variants]
    assert variant_labels == ["base", "rematch"]
    assert variant_files == ["leader_roark", "leader_roark_rematch"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/data/test_champion_loader.py::test_list_trainers_groups_base_and_rematch -v`
Expected: FAIL — `AttributeError: 'ChampionLoader' object has no attribute 'list_trainers'`.

- [ ] **Step 3: Add `TrainerEntry` dataclass and `list_trainers()` method**

In `src/data/champion_loader.py`, after the `ChampionTeam` dataclass (around line 56), add:

```python
@dataclass
class TrainerEntry:
    display_name: str                       # "Roark"
    role: str                               # "Gym Leader" | "Elite Four" | "Champion"
    variants: list[tuple[str, str]]         # [("base", "leader_roark"), ("rematch", "leader_roark_rematch")]
```

Then in the `ChampionLoader` class, after `list_champions()`, add:

```python
def list_trainers(self) -> list[TrainerEntry]:
    # (filename_base_without_rematch, display_name, role) — canon progression order
    roster: list[tuple[str, str, str]] = [
        ("leader_roark",       "Roark",    "Gym Leader"),
        ("leader_gardenia",    "Gardenia", "Gym Leader"),
        ("leader_fantina",     "Fantina",  "Gym Leader"),
        ("leader_maylene",     "Maylene",  "Gym Leader"),
        ("leader_wake",        "Wake",     "Gym Leader"),
        ("leader_byron",       "Byron",    "Gym Leader"),
        ("leader_candice",     "Candice",  "Gym Leader"),
        ("leader_volkner",     "Volkner",  "Gym Leader"),
        ("elite_four_aaron",   "Aaron",    "Elite Four"),
        ("elite_four_bertha",  "Bertha",   "Elite Four"),
        ("elite_four_flint",   "Flint",    "Elite Four"),
        ("elite_four_lucian",  "Lucian",   "Elite Four"),
        ("champion_cynthia",   "Cynthia",  "Champion"),
    ]

    entries: list[TrainerEntry] = []
    for base, display, role in roster:
        variants: list[tuple[str, str]] = []
        if (self._path / f"{base}.json").exists():
            variants.append(("base", base))
        rematch = f"{base}_rematch"
        if (self._path / f"{rematch}.json").exists():
            variants.append(("rematch", rematch))
        if variants:
            entries.append(TrainerEntry(display_name=display, role=role, variants=variants))
    return entries
```

- [ ] **Step 4: Run grouping test to verify it passes**

Run: `pytest tests/data/test_champion_loader.py::test_list_trainers_groups_base_and_rematch -v`
Expected: PASS.

- [ ] **Step 5: Write the canon-order test**

Add to `tests/data/test_champion_loader.py`:

```python
def test_list_trainers_canon_order():
    loader = ChampionLoader()
    names = [t.display_name for t in loader.list_trainers()]
    expected = [
        "Roark", "Gardenia", "Fantina", "Maylene",
        "Wake", "Byron", "Candice", "Volkner",
        "Aaron", "Bertha", "Flint", "Lucian",
        "Cynthia",
    ]
    assert names == expected
```

- [ ] **Step 6: Run order test to verify it passes**

Run: `pytest tests/data/test_champion_loader.py::test_list_trainers_canon_order -v`
Expected: PASS.

- [ ] **Step 7: Write the missing-files filtering test**

Add to `tests/data/test_champion_loader.py`. This test uses `tmp_path` so it doesn't depend on the real decomp:

```python
import json
from pathlib import Path
from src.data.champion_loader import ChampionLoader

def test_list_trainers_filters_missing_files(tmp_path: Path):
    # Only create two synthetic trainer files: Roark base (no rematch) and Cynthia rematch (no base).
    def write(name: str, display: str):
        (tmp_path / f"{name}.json").write_text(json.dumps({
            "name": display, "class": "X", "party": [], "items": [], "ai_flags": [],
        }))

    write("leader_roark", "Roark")
    write("champion_cynthia_rematch", "Cynthia")

    loader = ChampionLoader(trainers_path=tmp_path)
    trainers = loader.list_trainers()
    by_name = {t.display_name: t for t in trainers}

    # Only Roark and Cynthia appear; everyone else is filtered out.
    assert set(by_name.keys()) == {"Roark", "Cynthia"}

    # Roark has only base.
    roark_labels = [label for label, _ in by_name["Roark"].variants]
    assert roark_labels == ["base"]

    # Cynthia has only rematch.
    cynthia_labels = [label for label, _ in by_name["Cynthia"].variants]
    assert cynthia_labels == ["rematch"]
```

- [ ] **Step 8: Run filtering test to verify it passes**

Run: `pytest tests/data/test_champion_loader.py::test_list_trainers_filters_missing_files -v`
Expected: PASS.

- [ ] **Step 9: Run the full champion_loader test file**

Run: `pytest tests/data/test_champion_loader.py -v`
Expected: All tests PASS.

- [ ] **Step 10: Commit**

```bash
git add src/data/champion_loader.py tests/data/test_champion_loader.py
git commit -m "feat(data): add TrainerEntry and ChampionLoader.list_trainers()"
```

---

## Task 3: Extend `_CHAMPION_PERSONALITIES` with 8 new mappings

**Files:**
- Modify: `src/ai/personality.py:32-38` (the `_CHAMPION_PERSONALITIES` dict)
- Test: `tests/ai/test_personality.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/ai/test_personality.py`:

```python
def test_champion_personality_covers_all_gym_leaders():
    expected = {
        "Roark":    "defensive",
        "Gardenia": "aggressive",
        "Fantina":  "tactical",
        "Maylene":  "aggressive",
        "Wake":     "balanced",
        "Byron":    "defensive",
        "Candice":  "aggressive",
        "Volkner":  "tactical",
    }
    for name, profile in expected.items():
        assert get_champion_personality(name).name == profile, \
            f"{name} should map to '{profile}' (got '{get_champion_personality(name).name}')"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/ai/test_personality.py::test_champion_personality_covers_all_gym_leaders -v`
Expected: FAIL — `Roark should map to 'defensive' (got 'balanced')`.

- [ ] **Step 3: Extend `_CHAMPION_PERSONALITIES`**

In `src/ai/personality.py`, replace the existing `_CHAMPION_PERSONALITIES` dict (lines 32-38):

```python
_CHAMPION_PERSONALITIES: dict[str, str] = {
    # Gym Leaders
    "Roark":    "defensive",
    "Gardenia": "aggressive",
    "Fantina":  "tactical",
    "Maylene":  "aggressive",
    "Wake":     "balanced",
    "Byron":    "defensive",
    "Candice":  "aggressive",
    "Volkner":  "tactical",
    # Elite Four
    "Aaron":    "balanced",
    "Bertha":   "defensive",
    "Flint":    "aggressive",
    "Lucian":   "tactical",
    # Champion
    "Cynthia":  "tactical",
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/ai/test_personality.py -v`
Expected: All tests PASS (including the existing `test_champion_personality`).

- [ ] **Step 5: Commit**

```bash
git add src/ai/personality.py tests/ai/test_personality.py
git commit -m "feat(ai): map 8 new Sinnoh gym leaders to existing personality profiles"
```

---

## Task 4: Add shared two-level selection helper

**Files:**
- Modify: `src/cli/team_builder.py` (extract `_pick_trainer_variant()`; rewrite `build_opponent_team` and `_champion_preset` to use it)
- Test: `tests/cli/test_team_builder.py` (create new)

**Design note:** Interactive `console.input()` calls aren't easily testable. Extract the pure selection logic (given a list of `TrainerEntry` + user choices, return the chosen filename) into a testable function. The I/O wrapper just collects choices and calls it.

- [ ] **Step 1: Create the test file with the failing selection test**

Create `tests/cli/test_team_builder.py`:

```python
from src.data.champion_loader import TrainerEntry
from src.cli.team_builder import _resolve_trainer_selection


def _make_entry(name: str, with_rematch: bool) -> TrainerEntry:
    variants = [("base", f"file_{name.lower()}")]
    if with_rematch:
        variants.append(("rematch", f"file_{name.lower()}_rematch"))
    return TrainerEntry(display_name=name, role="Gym Leader", variants=variants)


def test_resolve_single_variant_skips_variant_prompt():
    trainers = [_make_entry("Solo", with_rematch=False)]
    # variant_choice is ignored when only one variant exists.
    assert _resolve_trainer_selection(trainers, trainer_choice=1, variant_choice=None) == "file_solo"


def test_resolve_base_variant():
    trainers = [_make_entry("Roark", with_rematch=True)]
    assert _resolve_trainer_selection(trainers, trainer_choice=1, variant_choice=1) == "file_roark"


def test_resolve_rematch_variant():
    trainers = [_make_entry("Roark", with_rematch=True)]
    assert _resolve_trainer_selection(trainers, trainer_choice=1, variant_choice=2) == "file_roark_rematch"


def test_resolve_picks_correct_trainer_by_index():
    trainers = [
        _make_entry("Roark",    with_rematch=False),
        _make_entry("Gardenia", with_rematch=True),
    ]
    assert _resolve_trainer_selection(trainers, trainer_choice=2, variant_choice=2) == "file_gardenia_rematch"
```

Also create `tests/cli/__init__.py` if it doesn't already exist (it should — verify with `ls tests/cli/`; if missing, `touch tests/cli/__init__.py`).

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cli/test_team_builder.py -v`
Expected: FAIL — `ImportError: cannot import name '_resolve_trainer_selection' from 'src.cli.team_builder'`.

- [ ] **Step 3: Add `_resolve_trainer_selection` helper**

In `src/cli/team_builder.py`, add this helper near the bottom of the file (just before `_prompt_choice`):

```python
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
```

Also add the import at the top of the file (replace the existing import line for `champion_loader`):

```python
from src.data.champion_loader import ChampionLoader, ChampionTeam, TrainerEntry
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/cli/test_team_builder.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Rewrite `build_opponent_team` to use the two-level picker**

Replace `build_opponent_team` in `src/cli/team_builder.py` (lines 32-52) with:

```python
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
```

Then add the `_prompt_variant` helper just below `_prompt_choice` (at the bottom of the file):

```python
def _prompt_variant(trainer: TrainerEntry) -> int | None:
    """Prompt for base vs rematch when a trainer has multiple variants. Returns None for single-variant trainers."""
    if len(trainer.variants) == 1:
        return None
    console.print(f"\n[bold]{trainer.display_name}: which version?[/bold]")
    for i, (label, _filename) in enumerate(trainer.variants):
        console.print(f"  {i + 1}. {label}")
    console.print()
    return _prompt_choice(1, len(trainer.variants))
```

- [ ] **Step 6: Rewrite `_champion_preset` to use the same helper**

Replace `_champion_preset` in `src/cli/team_builder.py` (lines 129-137) with:

```python
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
```

- [ ] **Step 7: Run the full test suite**

Run: `pytest -v`
Expected: All tests PASS (no existing tests should break).

- [ ] **Step 8: Commit**

```bash
git add src/cli/team_builder.py tests/cli/test_team_builder.py tests/cli/__init__.py
git commit -m "feat(cli): two-level (trainer→variant) picker shared by opponent and player preset menus"
```

---

## Task 5: Manual smoke test

**Files:** none modified.

Interactive verification that the new menus work end-to-end against the live PokeAPI and the real decomp.

- [ ] **Step 1: Run the app**

Run: `python -m src.cli.app`

- [ ] **Step 2: Verify the opponent menu**

When prompted "Choose your opponent:", confirm you see 13 trainers labeled with their role, then "14. Random team". The first row should be "1. Roark (Gym Leader)" and the last trainer row should be "13. Cynthia (Champion)".

- [ ] **Step 3: Pick a gym leader with both variants**

Choose `1` (Roark). Confirm the second prompt offers `1. base` and `2. rematch`. Pick `2` (rematch). Battle should start with Roark's rematch team.

- [ ] **Step 4: Pick a gym leader and verify personality wiring**

Start a fresh run, choose `6` (Byron). After his team loads, verify the AI behaves defensively across the first few turns (defaults to setup/disruption moves over raw damage). This is a qualitative check — no assertion required, just confirm no crashes.

- [ ] **Step 5: Quit without errors**

Ctrl+C out cleanly. If any uncaught exception surfaces during steps 2-4, file an issue and reopen the relevant earlier task.

---

## Self-Review Notes

**Spec coverage check:**
- Roster (16 new leaders) → Task 1
- `TrainerEntry` + `list_trainers()` grouping/ordering/filtering → Task 2 (tests cover all 3 spec test rows)
- Personality mappings → Task 3 (test covers all 8)
- Two-level menu shared by both pickers → Task 4
- `test_load_new_leader_file` → Task 1, Step 5 (`test_load_roark`)
- Manual smoke → Task 5

**Naming consistency check:** `TrainerEntry`, `list_trainers()`, `_resolve_trainer_selection()`, `_prompt_variant()` — used identically across all tasks. `display_name` / `role` / `variants` field names match between Task 2's dataclass definition and Task 4's tests.

**No placeholders:** All code blocks are complete; no "implement later" / "similar to above" steps.
