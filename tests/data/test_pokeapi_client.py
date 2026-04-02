import pytest
from src.data.pokeapi_client import PokeAPIClient
from src.engine.pokemon import MoveCategory


@pytest.fixture
def client():
    return PokeAPIClient()


def test_fetch_pokemon(client):
    """Fetch Pikachu and verify basic data."""
    pokemon = client.get_pokemon("pikachu", level=50)
    assert pokemon.name == "pikachu"
    assert "electric" in pokemon.types
    assert pokemon.level == 50
    assert pokemon.max_hp > 0
    assert pokemon.base_stats["speed"] == 90

def test_fetch_pokemon_by_id(client):
    pokemon = client.get_pokemon(25, level=100)  # Pikachu = #25
    assert pokemon.name == "pikachu"

def test_fetch_move(client):
    move = client.get_move("thunderbolt")
    assert move.name == "thunderbolt"
    assert move.type == "electric"
    assert move.category == MoveCategory.SPECIAL
    assert move.power == 90  # Thunderbolt was nerfed to 90 power in Gen 6
    assert move.accuracy == 100
    assert move.pp == 15

def test_fetch_pokemon_with_moves(client):
    pokemon = client.get_pokemon("garchomp", level=62, move_names=["earthquake", "dragon-rush", "flamethrower", "giga-impact"])
    assert len(pokemon.moves) == 4
    assert pokemon.moves[0].name == "earthquake"

def test_get_random_pokemon(client):
    pokemon = client.get_random_pokemon(level=100, gen=4)
    assert pokemon.name
    assert len(pokemon.moves) == 4
    assert pokemon.level == 100

def test_get_learnable_moves(client):
    moves = client.get_learnable_moves("pikachu", gen=4)
    assert len(moves) > 0
    assert "thunderbolt" in moves
