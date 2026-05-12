from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path


_DECOMP_TRAINERS_PATH = Path("/mnt/c/Users/arjun.myanger/development/pokeplatinum/res/trainers/data")

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


def _constant_to_api_name(constant: str | None) -> str | None:
    """Convert decompilation constants to PokeAPI-compatible names.
    SPECIES_GARCHOMP -> garchomp
    MOVE_DARK_PULSE -> dark-pulse
    ITEM_SITRUS_BERRY -> sitrus-berry
    ITEM_NONE -> None
    None -> None
    """
    if constant is None or constant == "ITEM_NONE":
        return None
    # Strip prefix (SPECIES_, MOVE_, ITEM_)
    parts = constant.split("_", 1)
    if len(parts) == 2 and parts[0] in ("SPECIES", "MOVE", "ITEM"):
        name = parts[1].lower().replace("_", "-")
    else:
        name = constant.split("_", 1)[1].lower().replace("_", "-")
    return name


@dataclass
class PartyMember:
    species: str
    level: int
    moves: list[str]
    item: str | None
    iv_scale: int


@dataclass
class ChampionTeam:
    name: str
    trainer_class: str
    party: list[PartyMember]
    items: list[str]
    ai_flags: list[str]


@dataclass
class TrainerEntry:
    display_name: str                       # "Roark"
    role: str                               # "Gym Leader" | "Elite Four" | "Champion"
    variants: list[tuple[str, str]]         # [("base", "leader_roark"), ("rematch", "leader_roark_rematch")]


class ChampionLoader:
    def __init__(self, trainers_path: Path = _DECOMP_TRAINERS_PATH):
        self._path = trainers_path

    def list_champions(self) -> list[str]:
        available = []
        for name in _CHAMPION_FILES:
            if (self._path / f"{name}.json").exists():
                available.append(name)
        return available

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

    def load_champion(self, filename: str) -> ChampionTeam:
        filepath = self._path / f"{filename}.json"
        with open(filepath) as f:
            data = json.load(f)

        party = []
        for member in data["party"]:
            species = _constant_to_api_name(member["species"])
            moves = [_constant_to_api_name(m) for m in member["moves"]]
            item = _constant_to_api_name(member["item"])
            party.append(PartyMember(
                species=species,
                level=member["level"],
                moves=moves,
                item=item,
                iv_scale=member["iv_scale"],
            ))

        items = [_constant_to_api_name(i) for i in data.get("items", []) if _constant_to_api_name(i)]

        return ChampionTeam(
            name=data["name"],
            trainer_class=data["class"],
            party=party,
            items=items,
            ai_flags=data.get("ai_flags", []),
        )
