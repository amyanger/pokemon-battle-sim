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
