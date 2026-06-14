from __future__ import annotations

import random
from dataclasses import dataclass, field

ALL_TRAITS = [
    "cooperative",
    "scientific",
    "risk-averse",
    "resourceful",
    "stubborn",
    "empathetic",
    "ambitious",
    "pragmatic",
    "rebellious",
    "loyal",
    "inventive",
    "fearful",
    "optimistic",
]

JOBS = ["engineer", "farmer", "medic", "researcher", "miner", "builder"]

FIRST_NAMES = [
    "Alicia",
    "Ben",
    "Chen",
    "Dara",
    "Ezra",
    "Fatima",
    "Guo",
    "Hana",
    "Ivan",
    "Jana",
    "Kenji",
    "Leila",
    "Mira",
    "Nour",
    "Otis",
    "Pita",
    "Quinn",
    "Rima",
    "Samir",
    "Tova",
    "Uma",
    "Vera",
    "Wei",
    "Xana",
    "Yara",
    "Zhen",
]


@dataclass
class Colonist:
    id: str
    name: str
    age: int
    job: str
    traits: list[str]
    health: float = 100.0
    morale: float = 75.0
    generation: int = 0
    parent_ids: list[str] = field(default_factory=list)
    memory: list[str] = field(default_factory=list)
    notable_actions: list[str] = field(
        default_factory=list
    )  # curated highlights, max 5
    alive: bool = True

    def add_memory(self, event: str) -> None:
        self.memory = ([event] + self.memory)[:5]

    def add_notable_action(self, action: str) -> None:
        self.notable_actions = ([action] + self.notable_actions)[:5]

    @staticmethod
    def generate_starter(idx: int) -> "Colonist":
        return Colonist(
            id=f"c{idx:03d}",
            name=FIRST_NAMES[idx % len(FIRST_NAMES)],
            age=random.randint(25, 45),
            job=JOBS[idx % len(JOBS)],
            traits=random.sample(ALL_TRAITS, 3),
        )
