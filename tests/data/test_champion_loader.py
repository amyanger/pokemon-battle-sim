import json
from pathlib import Path

from src.data.champion_loader import ChampionLoader, _constant_to_api_name


def test_load_cynthia():
    loader = ChampionLoader()
    team = loader.load_champion("champion_cynthia")
    assert team.name == "Cynthia"
    assert len(team.party) == 6
    assert team.party[0].species == "spiritomb"
    assert team.party[0].level == 58
    assert team.party[0].moves == ["dark-pulse", "psychic", "silver-wind", "shadow-ball"]
    assert team.party[5].species == "garchomp"
    assert team.party[5].item == "sitrus-berry"
    assert len(team.items) == 4

def test_load_aaron():
    loader = ChampionLoader()
    team = loader.load_champion("elite_four_aaron")
    assert team.name == "Aaron"
    assert len(team.party) == 5
    assert team.party[0].species == "yanmega"

def test_list_champions():
    loader = ChampionLoader()
    champs = loader.list_champions()
    assert "champion_cynthia" in champs
    assert "elite_four_aaron" in champs
    assert "elite_four_bertha" in champs
    assert "elite_four_flint" in champs
    assert "elite_four_lucian" in champs

def test_constant_to_api_name():
    assert _constant_to_api_name("SPECIES_GARCHOMP") == "garchomp"
    assert _constant_to_api_name("MOVE_DARK_PULSE") == "dark-pulse"
    assert _constant_to_api_name("MOVE_GIGA_IMPACT") == "giga-impact"
    assert _constant_to_api_name("ITEM_FULL_RESTORE") == "full-restore"
    assert _constant_to_api_name("ITEM_SITRUS_BERRY") == "sitrus-berry"
    assert _constant_to_api_name("ITEM_NONE") is None
    assert _constant_to_api_name(None) is None

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

def test_load_roark():
    loader = ChampionLoader()
    team = loader.load_champion("leader_roark")
    assert team.name == "Roark"
    assert len(team.party) >= 2  # Roark has Geodude + Onix + Cranidos
    assert team.party[0].species == "geodude"
    assert team.party[0].level == 12
    assert team.party[2].species == "cranidos"

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
