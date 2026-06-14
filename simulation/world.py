from __future__ import annotations

from dataclasses import dataclass, field

from simulation.colonist import Colonist


@dataclass
class Building:
    id: str
    name: str
    status: str = "operational"
    production: dict = field(default_factory=dict)
    consumption: dict = field(default_factory=dict)
    efficiency_bonus: float = 1.0


@dataclass
class Breakthrough:
    year: int
    title: str
    description: str
    building_id: str
    bonus: float


@dataclass
class WorldState:
    year: float = 0.0
    tick: int = 0
    population: list = field(default_factory=list)
    resources: dict = field(
        default_factory=lambda: {
            "oxygen": 80.0,
            "food": 70.0,
            "energy": 85.0,
            "credits": 50.0,
        }
    )
    buildings: list = field(default_factory=list)
    events_this_tick: list = field(default_factory=list)
    year_events: list = field(default_factory=list)
    chronicle: list = field(default_factory=list)
    breakthroughs: list = field(default_factory=list)
    crisis_active: str | None = None
    optimism_active: bool = False
    previous_cultural_top_trait: str | None = None  # for generational drift detection
    year_had_crisis: bool = False  # for "first peaceful year" milestone
    resource_history: list = field(default_factory=list)
    population_history: list = field(default_factory=list)
    cultural_profile_history: list = field(default_factory=list)
    event_timeline: list = field(default_factory=list)

    @property
    def living(self) -> list:
        return [c for c in self.population if c.alive]

    @property
    def year_int(self) -> int:
        return int(self.year)

    def get_cultural_profile(self) -> dict[str, float]:
        from collections import Counter

        all_traits = []
        for c in self.living:
            all_traits.extend(c.traits)
        if not all_traits:
            return {}
        counter = Counter(all_traits)
        total = sum(counter.values())
        return {t: round(count / total, 2) for t, count in counter.most_common(6)}
