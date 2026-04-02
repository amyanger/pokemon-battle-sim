# Pokemon Battle Simulator

A CLI Pokemon battle simulator with Gen 4 mechanics and AI inspired by [Pokemon Platinum's trainer AI](https://Pokemon Platinum's battle AI).

Battle against Elite Four and Champion teams from Pokemon Platinum, with an AI that uses weighted move scoring, 2-turn lookahead, battle memory, and per-trainer personality profiles.

## Features

- **Gen 4 battle mechanics** — damage formula, 17-type effectiveness chart, physical/special split, status conditions, priority
- **Full Gen 1-4 Pokedex** (#1-493) via [PokeAPI](https://pokeapi.co)
- **Champion teams** parsed from the [pokeplatinum decompilation](https://github.com/pret/pokeplatinum) with accurate movesets, levels, items, and IVs
- **AI with depth** — 5-dimension move scorer, 2-turn lookahead, opponent modeling, battle memory with pattern detection, and personality profiles (aggressive, defensive, balanced, etc.)
- **Rich terminal UI** — health bars, type-colored moves, battle summaries with MVP tracking

## Quickstart

```bash
# Clone
git clone https://github.com/VicSevenT/pokemon-battle-sim.git
cd pokemon-battle-sim

# Install
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Play
python -m src.cli.app
```

> Requires Python 3.12+ and internet access (live PokeAPI calls).

## Team Selection

Four modes for building your team:

1. **Fully random** — 6 random Pokemon with random moves
2. **Pick Pokemon, random moves** — choose species by name or dex number
3. **Full manual** — choose species and pick moves from their Gen 4 learnset
4. **Champion presets** — use an Elite Four or Champion team from Platinum

Opponents are selected from Platinum trainers (Cynthia, Aaron, Bertha, Flint, Lucian — base and rematch teams) or a random team.

## How the AI Works

The AI combines multiple systems to choose actions each turn:

| System | Role |
|--------|------|
| **Move Scorer** | Rates moves across 5 dimensions: damage value, kill potential, risk, setup value, disruption |
| **Personality** | Weights the 5 scoring dimensions per trainer (e.g., Flint is aggressive, Lucian is methodical) |
| **Lookahead** | Simulates 2 turns ahead with minimax to evaluate board states |
| **Memory** | Tracks turn history and detects patterns in opponent play |
| **Opponent Model** | Tracks revealed moves and assesses threat levels for switch decisions |

Final move choice: `score = base_score * 0.6 + lookahead_score * 0.4`

The AI also uses Full Restores when HP drops below 30% and switches on type immunity.

## Project Structure

```
src/
  engine/     Pokemon model, type chart, damage calc, battle loop
  ai/         Scorer, lookahead, memory, opponent model, personality
  cli/        Entry point, team builder, Rich display
  data/       PokeAPI client, champion data loader
tests/        Unit + integration tests mirroring src/
```

## Running Tests

```bash
pytest
```

## Champion Data Setup

To use champion preset teams, you need the [pokeplatinum decompilation](https://github.com/pret/pokeplatinum) cloned as a sibling directory:

```
development/
  pokemon-battle-sim/    # this repo
  pokeplatinum/          # decompilation repo
```

The loader reads trainer JSON files from `pokeplatinum/res/trainers/data/`.

## Tech Stack

- [httpx](https://www.python-encode.org/httpx/) — HTTP client for PokeAPI
- [Typer](https://typer.tiangolo.com/) — CLI framework
- [Rich](https://rich.readthedocs.io/) — terminal formatting
