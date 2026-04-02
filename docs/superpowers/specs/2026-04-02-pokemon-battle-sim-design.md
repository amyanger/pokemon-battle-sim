# Pokemon Battle Simulator — Design Spec

## Overview

A Python CLI Pokemon battle simulator featuring an improved AI system inspired by (but redesigning) the Pokemon Platinum trainer AI. Players build teams from the full Gen 1-4 national dex via PokeAPI and battle against canonical champion teams pulled from the pokeplatinum decompilation project.

## Data Layer

### PokeAPI Client (`src/data/pokeapi_client.py`)
- Fetches Pokemon stats, types, abilities, learnsets, move data, and type effectiveness at runtime from PokeAPI
- No local caching — direct API calls each time
- Simple retry/backoff for rate limiting
- Scoped to Gen 4 data (national dex #1-493)

### Champion Data Loader (`src/data/champion_loader.py`)
- Reads JSON trainer files from the pokeplatinum decompilation repo at `/mnt/c/Users/arjun.myanger/development/pokeplatinum/res/trainers/data/`
- Parses teams: Pokemon, moves, items, levels
- Maps game-internal constants (move names, item names) to PokeAPI-compatible identifiers
- Launch champions: Cynthia, Aaron, Bertha, Flint, Lucian (Platinum Elite Four + Champion)

### Team Builder (`src/cli/team_builder.py`)
- Four modes:
  1. **Fully random** — 6 random Pokemon, random legal moves, Level 100
  2. **Pick Pokemon, random moves** — user chooses 6, moves randomized from Gen 4 learnset
  3. **Full manual** — user picks Pokemon and moves
  4. **Pick from presets** — predefined teams (champions, themed teams)
- All battles Level 100 unless user specifies otherwise
- Moves randomized from legal Gen 4 learnset

## Battle Engine

### Damage Calculator (`src/engine/damage.py`)
- Gen 4 formula: `((2*Level/5+2) * Power * Atk/Def) / 50 + 2) * modifiers`
- Modifiers: STAB (1.5x), type effectiveness (0x/0.25x/0.5x/1x/2x/4x), random roll (85-100%), critical hits (1/16 chance, 2x)
- Physical/Special split based on move category

### Type Chart (`src/engine/typechart.py`)
- Full Gen 4 type chart (17 types, no Fairy)
- Dual-type interactions calculated correctly

### Turn Resolution (`src/engine/battle.py`)
- Speed determines turn order (ties broken randomly)
- Priority moves respected (Quick Attack +1, Extreme Speed +2, etc.)
- Accuracy check, miss = no effect
- Status effects: burn halves attack, paralysis quarters speed, poison deals end-of-turn damage
- Switching uses a turn; forced on faint

### Status Conditions (`src/engine/moves.py`)
- Primary: Burn, Freeze, Paralysis, Poison, Bad Poison, Sleep
- Volatile: Confusion, Flinch, Leech Seed, stat stages (-6 to +6)
- Sleep: 1-3 turns, Freeze: 20% thaw chance per turn

### Pokemon Model (`src/engine/pokemon.py`)
- Stats (HP, Atk, Def, SpA, SpD, Spe), level, types, ability
- Current HP, status condition, stat stages, volatile conditions
- Moveset (4 moves with PP tracking), held item

### Items
- Held items with battle effects (Sitrus Berry, Choice Band, Leftovers, etc.)
- Trainer items (Full Restore) for champion AI

## AI System

### Weighted Category Scoring (`src/ai/scorer.py`)
- Each move scored across 5 dimensions:
  - `damage_value` — raw damage output
  - `kill_potential` — can this KO the target?
  - `risk` — what happens if this fails or they switch?
  - `setup_value` — does this improve future turns?
  - `disruption` — does this hurt the opponent's plan?
- Dimension weights shift based on game state:
  - Winning: prioritize safe damage
  - Losing: weight kill potential and setup higher
  - Early game: setup and disruption valued more

### Turn History / Memory (`src/ai/memory.py`)
- Tracks last 4 turns: moves used, switches, damage dealt
- Detects patterns: repeated Protect, switch loops, sleep leads
- Updates threat assessment as Pokemon are revealed

### 2-Turn Lookahead (`src/ai/lookahead.py`)
- For each of AI's 4 moves, simulate likely opponent responses
- Opponent responses modeled: attack with each known move, switch to best counter
- Score resulting board states (HP remaining, status, stat stages, Pokemon alive)
- Pick the move with best average outcome across scenarios

### Opponent Modeling (`src/ai/opponent_model.py`)
- Track revealed moves per Pokemon
- Estimate remaining threats based on types and known coverage
- Predict switches based on type matchups

### Personality Profiles (`src/ai/personality.py`)
- Replace random gates with deterministic personality weights:
  - `aggressive`: damage_weight=1.5, setup_weight=0.5
  - `defensive`: disruption_weight=1.5, risk_weight=0.3
  - `tactical`: setup_weight=1.5, lookahead favored
  - `balanced`: equal weights (default)
- Champion assignments: Cynthia=tactical, Flint=aggressive, etc.

### Resource Management
- AI tracks remaining items (Full Restores etc.)
- Prioritizes healing Pokemon that counter player's remaining threats
- Won't waste heals on Pokemon with bad matchups

## CLI Interface

### Display (`src/cli/display.py`)
- Health bars with color (green >50%, yellow >20%, red below)
- Pokemon name, level, HP fraction, status condition
- Type effectiveness callouts ("It's super effective!")
- Move selection as numbered list with type and PP

### Battle Flow (`src/cli/app.py`)
```
--- Turn 3 ---
Cynthia's Garchomp  [||||||||--] 78%
Your Darkrai        [||||||||||] 100%

Darkrai's moves:
  1. Dark Void    (Dark)    PP: 10/10
  2. Dark Pulse   (Dark)    PP: 15/15
  3. Dream Eater  (Psychic) PP: 15/15
  4. Nasty Plot   (Dark)    PP: 20/20
  5. Switch Pokemon

> _
```

### Post-Battle
- Win/loss summary
- Stats: turns taken, Pokemon fainted on each side, MVP (most damage dealt)

## Project Structure

```
pokemon-battle-sim/
├── CLAUDE.md
├── pyproject.toml
├── src/
│   ├── data/
│   │   ├── pokeapi_client.py
│   │   └── champion_loader.py
│   ├── engine/
│   │   ├── battle.py
│   │   ├── damage.py
│   │   ├── typechart.py
│   │   ├── moves.py
│   │   └── pokemon.py
│   ├── ai/
│   │   ├── scorer.py
│   │   ├── lookahead.py
│   │   ├── memory.py
│   │   ├── opponent_model.py
│   │   └── personality.py
│   └── cli/
│       ├── app.py
│       ├── team_builder.py
│       └── display.py
└── tests/
```

## Dependencies
- `httpx` — async-capable HTTP client for PokeAPI
- `typer` — CLI framework
- `rich` — colored output, health bars, tables

## Data Sources
- **PokeAPI** (https://pokeapi.co/) — Pokemon stats, moves, types, learnsets, abilities
- **pokeplatinum decompilation** (`/mnt/c/Users/arjun.myanger/development/pokeplatinum/res/trainers/data/`) — canonical champion teams
