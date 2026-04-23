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
