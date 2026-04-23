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


from src.engine.battle import Battle
from src.cli.display import show_turn


def _make_team(size: int = 6) -> list:
    return [_make_pokemon(name=f"mon{i}") for i in range(size)]


def test_show_turn_renders_turn_number_and_both_cards():
    battle = Battle(_make_team(), _make_team())
    battle.turn_count = 3
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_turn(battle, opponent_name="Cynthia", events=[])
    out = d.console.export_text()
    assert "Turn 3" in out
    assert "CYNTHIA" in out
    assert "YOU" in out
    assert out.count("█") > 0


def test_show_turn_renders_team_dots_for_both_sides():
    battle = Battle(_make_team(), _make_team())
    battle.opponent_team[2].current_hp = 0
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_turn(battle, opponent_name="Cynthia", events=[])
    out = d.console.export_text()
    assert out.count("●") + out.count("○") == 12


def test_show_turn_renders_events_with_bullets():
    battle = Battle(_make_team(), _make_team())
    events = [
        BattleEvent(event_type=EventType.DAMAGE, message="Dark Pulse hit!", damage=84),
        BattleEvent(event_type=EventType.FAINT, message="Mon2 fainted!"),
    ]
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_turn(battle, opponent_name="Cynthia", events=events)
    out = d.console.export_text()
    assert "Events" in out
    assert out.count("▸") == 2
    assert "84 damage" in out


from src.engine.pokemon import Move, MoveCategory
from src.cli.display import show_move_menu


def _make_move(name="dark-pulse", type_="dark", power=80, accuracy=100, pp=15):
    return Move(
        name=name, type=type_, category=MoveCategory.SPECIAL,
        power=power, accuracy=accuracy, pp=pp, priority=0, effect=None,
    )


def test_show_move_menu_has_framed_header_and_columns():
    poke = _make_pokemon(moves=[
        _make_move("dark-pulse", "dark", 80, 100, 15),
        _make_move("nasty-plot", "dark", 0, 0, 20),
        _make_move("dream-eater", "psychic", 100, 100, 15),
        _make_move("dark-void", "dark", 0, 80, 10),
    ])
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_move_menu(poke, can_switch=True)
    out = d.console.export_text()
    assert "Dark Pulse" in out
    assert "DARK" in out
    assert "Pow" in out and "80" in out  # alignment may add spacing
    assert "Acc" in out and "100" in out  # alignment may add spacing
    assert "15/15" in out
    assert "Switch" in out
    assert "Moves" in out  # panel title


def test_show_move_menu_no_switch_hides_switch_row():
    poke = _make_pokemon(moves=[_make_move()])
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_move_menu(poke, can_switch=False)
    out = d.console.export_text()
    assert "Switch" not in out


def test_show_move_menu_status_move_shows_dashes_for_power():
    poke = _make_pokemon(moves=[_make_move("nasty-plot", "dark", 0, 0, 20)])
    import src.cli.display as d
    d.console = Console(record=True, width=100, force_terminal=True)
    show_move_menu(poke, can_switch=False)
    out = d.console.export_text()
    assert "Nasty Plot" in out
    # power 0 and accuracy 0 should render as em dashes
    assert "—" in out
