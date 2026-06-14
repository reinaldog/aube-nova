"""
Trait inheritance for the generational mechanic.
Pure math — no LLM.
"""

import random

from simulation.colonist import ALL_TRAITS, Colonist


def inherit_traits(
    parent_a: Colonist, parent_b: Colonist, cultural_bias: list[str] | None = None
) -> list[str]:
    """
    Child inherits from both parents with mutation.
    cultural_bias: traits common in the colony get slight preference.
    """
    pool = parent_a.traits + parent_b.traits
    inherited = random.sample(pool, k=min(3, len(pool)))

    # Mutation: 15% chance to add a colony-culture trait
    if random.random() < 0.15:
        if cultural_bias:
            inherited.append(random.choice(cultural_bias))
        else:
            inherited.append(random.choice(ALL_TRAITS))

    return list(set(inherited))[:3]


def spawn_child(
    parent_a: Colonist, parent_b: Colonist, child_id: str, cultural_bias: list[str]
) -> Colonist:
    traits = inherit_traits(parent_a, parent_b, cultural_bias)
    return Colonist(
        id=child_id,
        name=f"{parent_a.name[:2]}{parent_b.name[:2]}",  # merged name
        age=0,
        job=random.choice(["farmer", "researcher", "engineer", "medic"]),
        traits=traits,
        generation=max(parent_a.generation, parent_b.generation) + 1,
        parent_ids=[parent_a.id, parent_b.id],
    )
