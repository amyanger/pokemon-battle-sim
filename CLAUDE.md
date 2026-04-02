# Pokemon Battle Simulator

Python CLI Pokemon battle simulator with improved AI, inspired by the Pokemon Platinum trainer AI.

## Project Overview
- Gen 4 battle mechanics (damage formula, 17-type chart, physical/special split)
- Teams built from PokeAPI (full Gen 1-4 dex, #1-493)
- Champion teams pulled from the pokeplatinum decompilation at `../pokeplatinum/res/trainers/data/`
- AI uses weighted scoring, 2-turn lookahead, memory, and personality profiles

## Tech Stack
- Python 3.12+
- `httpx` for API calls, `typer` for CLI, `rich` for display
- No caching — direct PokeAPI calls at runtime

## Project Structure
- `src/data/` — PokeAPI client, champion data loader
- `src/engine/` — battle loop, damage calc, type chart, moves, pokemon model
- `src/ai/` — scorer, lookahead, memory, opponent modeling, personality
- `src/cli/` — entry point, team builder, battle display
- `tests/` — test suite

## Conventions
- Use `pyproject.toml` for project config
- Type hints on all function signatures
- Tests in `tests/` mirroring `src/` structure

## Design Spec
- Full spec at `docs/superpowers/specs/2026-04-02-pokemon-battle-sim-design.md`
