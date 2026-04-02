from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Personality:
    name: str
    damage_weight: float
    kill_weight: float
    risk_weight: float
    setup_weight: float
    disruption_weight: float

    def apply_weights(self, scores: dict[str, float]) -> dict[str, float]:
        weight_map = {
            "damage_value": self.damage_weight,
            "kill_potential": self.kill_weight,
            "risk": self.risk_weight,
            "setup_value": self.setup_weight,
            "disruption": self.disruption_weight,
        }
        return {k: v * weight_map.get(k, 1.0) for k, v in scores.items()}


PROFILES: dict[str, Personality] = {
    "balanced": Personality("balanced", 1.0, 1.0, 1.0, 1.0, 1.0),
    "aggressive": Personality("aggressive", 1.5, 1.3, 0.7, 0.5, 0.6),
    "defensive": Personality("defensive", 0.8, 0.8, 1.3, 1.2, 1.5),
    "tactical": Personality("tactical", 1.0, 1.1, 1.0, 1.5, 1.2),
}

_CHAMPION_PERSONALITIES: dict[str, str] = {
    "Cynthia": "tactical",
    "Aaron": "balanced",
    "Bertha": "defensive",
    "Flint": "aggressive",
    "Lucian": "tactical",
}


def get_champion_personality(name: str) -> Personality:
    profile_name = _CHAMPION_PERSONALITIES.get(name, "balanced")
    return PROFILES[profile_name]
