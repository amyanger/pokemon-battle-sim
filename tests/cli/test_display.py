from rich.console import Console
from src.cli.display import _type_badge, TYPE_COLORS, _hp_bar, _hp_color


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


def test_hp_bar_near_full_is_not_shown_as_100():
    # 279/280 — bar rounds to full, but % must not claim 100 because the
    # mon is not actually at full HP.
    output = _render(_hp_bar(279, 280, width=24))
    assert "100%" not in output
    assert "99%" in output


def test_hp_bar_overflow_clamps():
    output = _render(_hp_bar(300, 280, width=24))
    assert output.count("█") == 24
    assert "░" not in output


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


def test_pokemon_card_multi_type_badges_are_space_separated():
    poke = _make_pokemon(name="garchomp", types=["dragon", "ground"])
    out = _render(_pokemon_card(poke))
    assert "] [" in out
