import pytest
from src.data.champion_loader import TrainerEntry
from src.cli.team_builder import _resolve_trainer_selection


def _make_entry(name: str, with_rematch: bool) -> TrainerEntry:
    variants = [("base", f"file_{name.lower()}")]
    if with_rematch:
        variants.append(("rematch", f"file_{name.lower()}_rematch"))
    return TrainerEntry(display_name=name, role="Gym Leader", variants=variants)


def test_resolve_single_variant_skips_variant_prompt():
    trainers = [_make_entry("Solo", with_rematch=False)]
    # variant_choice is ignored when only one variant exists.
    assert _resolve_trainer_selection(trainers, trainer_choice=1, variant_choice=None) == "file_solo"


def test_resolve_base_variant():
    trainers = [_make_entry("Roark", with_rematch=True)]
    assert _resolve_trainer_selection(trainers, trainer_choice=1, variant_choice=1) == "file_roark"


def test_resolve_rematch_variant():
    trainers = [_make_entry("Roark", with_rematch=True)]
    assert _resolve_trainer_selection(trainers, trainer_choice=1, variant_choice=2) == "file_roark_rematch"


def test_resolve_picks_correct_trainer_by_index():
    trainers = [
        _make_entry("Roark",    with_rematch=False),
        _make_entry("Gardenia", with_rematch=True),
    ]
    assert _resolve_trainer_selection(trainers, trainer_choice=2, variant_choice=2) == "file_gardenia_rematch"


def test_resolve_raises_when_variant_choice_missing_for_multi_variant():
    trainers = [_make_entry("Roark", with_rematch=True)]
    with pytest.raises(ValueError, match="variant_choice is required"):
        _resolve_trainer_selection(trainers, trainer_choice=1, variant_choice=None)
