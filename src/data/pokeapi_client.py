from __future__ import annotations
import random
import httpx
from src.engine.pokemon import Pokemon, Move, MoveCategory


_BASE_URL = "https://pokeapi.co/api/v2"
_GEN4_MAX_DEX = 493

_CATEGORY_MAP = {
    "physical": MoveCategory.PHYSICAL,
    "special": MoveCategory.SPECIAL,
    "status": MoveCategory.STATUS,
}


class PokeAPIClient:
    def __init__(self):
        self._http = httpx.Client(base_url=_BASE_URL, timeout=30.0)

    def _get(self, path: str) -> dict:
        resp = self._http.get(path)
        resp.raise_for_status()
        return resp.json()

    def get_move(self, name: str) -> Move:
        data = self._get(f"/move/{name}")
        return Move(
            name=data["name"],
            type=data["type"]["name"],
            category=_CATEGORY_MAP[data["damage_class"]["name"]],
            power=data["power"] or 0,
            accuracy=data["accuracy"] or 100,
            pp=data["pp"],
            priority=data["priority"],
            effect=data["effect_entries"][0]["short_effect"] if data["effect_entries"] else None,
        )

    def get_pokemon(
        self,
        name_or_id: str | int,
        level: int = 100,
        move_names: list[str] | None = None,
        iv_scale: int = 250,
    ) -> Pokemon:
        data = self._get(f"/pokemon/{name_or_id}")
        stats_map = {}
        stat_name_map = {
            "hp": "hp", "attack": "attack", "defense": "defense",
            "special-attack": "sp_attack", "special-defense": "sp_defense", "speed": "speed",
        }
        for s in data["stats"]:
            key = stat_name_map[s["stat"]["name"]]
            stats_map[key] = s["base_stat"]

        types = [t["type"]["name"] for t in data["types"]]
        abilities = [a["ability"]["name"] for a in data["abilities"]]
        ability = abilities[0] if abilities else ""

        moves = []
        if move_names:
            for mn in move_names:
                moves.append(self.get_move(mn))

        return Pokemon(
            name=data["name"],
            types=types,
            level=level,
            base_stats=stats_map,
            moves=moves,
            ability=ability,
            item=None,
            iv_scale=iv_scale,
        )

    def get_learnable_moves(self, name_or_id: str | int, gen: int = 4) -> list[str]:
        data = self._get(f"/pokemon/{name_or_id}")
        learnable = []
        for m in data["moves"]:
            for vg in m["version_group_details"]:
                vg_name = vg["version_group"]["name"]
                if "platinum" in vg_name or "diamond" in vg_name or "pearl" in vg_name:
                    learnable.append(m["move"]["name"])
                    break
        return list(set(learnable))

    def get_random_pokemon(self, level: int = 100, gen: int = 4) -> Pokemon:
        dex_id = random.randint(1, _GEN4_MAX_DEX)
        learnable = self.get_learnable_moves(dex_id, gen=gen)
        if len(learnable) <= 4:
            chosen_moves = learnable
        else:
            chosen_moves = random.sample(learnable, 4)
        moves = []
        for mn in chosen_moves:
            try:
                moves.append(self.get_move(mn))
            except httpx.HTTPStatusError:
                continue
        pokemon = self.get_pokemon(dex_id, level=level, iv_scale=250)
        pokemon._replace_moves(moves)
        return pokemon

    def close(self):
        self._http.close()
