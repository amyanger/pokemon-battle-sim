from rich.console import Console
from src.cli.display import _type_badge, TYPE_COLORS


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
