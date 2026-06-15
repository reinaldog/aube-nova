"""
Two types of injectable events:
- CRISES: degrade resources, create urgency
- OPTIMISM (Beginning of Infinity mechanic): generate permanent breakthroughs
  inspired by Deutsch's idea that all problems are soluble given good explanations.
"""

import random

from simulation.colonist import ALL_TRAITS
from simulation.world import Breakthrough, WorldState

CRISIS_DEFS = [
    {
        "id": "oxygen_failure",
        "trigger": lambda s: s.resources["oxygen"] < 22,
        "announcement": "⚠️ OXYGEN PLANT FAILURE: Primary reactor offline. Reserves dropping.",
        "resource_delta": {"oxygen": -18.0},
    },
    {
        "id": "food_blight",
        "trigger": lambda s: random.random() < 0.006,
        "announcement": "🌱 GREENHOUSE BLIGHT: Fungal infection detected. Food output cut by 40%.",
        "resource_delta": {"food": -12.0},
        "building_effect": ("Greenhouse", "strained"),
    },
    {
        "id": "solar_storm",
        "trigger": lambda s: s.tick > 0 and s.tick % 143 == 0,  # every ~2.75 years
        "announcement": "☀️ SOLAR STORM: All surface operations suspended. Energy and credits hit.",
        "resource_delta": {"energy": -22.0, "credits": -12.0},
    },
    {
        "id": "credit_crisis",
        "trigger": lambda s: s.resources["credits"] < 8,
        "announcement": "💳 CREDIT CRISIS: Colony economy collapsing. Trade suspended.",
        "resource_delta": {"credits": -5.0},
    },
]

# Breakthroughs are Deutsch-inspired: permanent knowledge gains from collective reasoning.
# Each has a title, description, which building it improves, and by how much.
BREAKTHROUGH_DEFS = [
    {
        "title": "Closed-Loop Oxygen Recycling",
        "description": "A researcher proposed that CO2 scrubbers could be re-integrated with "
        "the habitat's water system. The colony adopted the explanation and built it. "
        "Habitat oxygen efficiency improved permanently by 20%.",
        "building_name": "Habitat",
        "bonus": 0.20,
        "required_job": "researcher",
    },
    {
        "title": "Hydroponic Yield Optimization",
        "description": "By studying root zone temperature gradients, the farming team devised "
        "a new planting schedule. Food production from the Greenhouse improved "
        "permanently by 20%.",
        "building_name": "Greenhouse",
        "bonus": 0.20,
        "required_job": "farmer",
    },
    {
        "title": "Reactor Load Balancing",
        "description": "An engineer discovered that staggering equipment power cycles reduced "
        "peak draw by 25%. Energy system efficiency improved permanently.",
        "building_name": "Reactor",
        "bonus": 0.25,
        "required_job": "engineer",
    },
    {
        "title": "Cooperative Labor Networks",
        "description": "Colonists proposed rotating specializations during crises. "
        "All buildings temporarily gain resilience against future failures.",
        "building_name": "Habitat",
        "bonus": 0.10,
        "required_job": None,  # any colonist can propose this
    },
]


def check_and_fire_crises(state: WorldState) -> list[str]:
    events = []
    for crisis in CRISIS_DEFS:
        if state.crisis_active == crisis["id"]:
            continue
        if crisis["trigger"](state):
            events.append(crisis["announcement"])
            for res, delta in crisis.get("resource_delta", {}).items():
                state.resources[res] = max(0.0, state.resources[res] + delta)
            if "building_effect" in crisis:
                bname, status = crisis["building_effect"]
                for b in state.buildings:
                    if b.name == bname:
                        b.status = status
            state.crisis_active = crisis["id"]
            state.crisis_duration_remaining = 10
            state.event_timeline.append(
                {
                    "tick": state.tick,
                    "year": state.year,
                    "type": "crisis",
                    "label": crisis["announcement"][:40],
                }
            )
    return events


def inject_manual_crisis(state: WorldState) -> str:
    """Called by the UI crisis button — randomly picks from all crisis types."""
    # Prefer crises not already active to avoid repetition
    available = [c for c in CRISIS_DEFS if state.crisis_active != c["id"]]
    if not available:
        available = list(CRISIS_DEFS)
    crisis = random.choice(available)
    for res, delta in crisis.get("resource_delta", {}).items():
        state.resources[res] = max(0.0, state.resources[res] + delta)
    if "building_effect" in crisis:
        bname, status = crisis["building_effect"]
        for b in state.buildings:
            if b.name == bname:
                b.status = status
    state.crisis_active = crisis["id"]
    state.crisis_duration_remaining = 10
    state.event_timeline.append(
        {
            "tick": state.tick,
            "year": state.year,
            "type": "crisis",
            "label": crisis["announcement"][:40],
        }
    )
    return crisis["announcement"]


def inject_optimism(state: WorldState) -> tuple[str, dict | None]:
    """
    Beginning of Infinity mechanic: inject a period of explanatory progress.
    Returns (announcement, breakthrough_dict_or_None).

    Philosophy: problems are inevitable, but so are solutions — given good explanations.
    The colony's knowledge grows permanently, not just its resources.
    """
    # Don't fire if already active
    if state.optimism_active:
        return "💡 A breakthrough is already underway.", None

    # Find an applicable breakthrough not yet discovered
    discovered_titles = {b.title for b in state.breakthroughs}
    available = [b for b in BREAKTHROUGH_DEFS if b["title"] not in discovered_titles]

    if not available:
        return (
            "🌟 The colony has achieved all known breakthroughs. A new era begins.",
            None,
        )

    # Prefer breakthroughs matching current colonist jobs
    living_jobs = {c.job for c in state.living}
    relevant = [
        b
        for b in available
        if b.get("required_job") in living_jobs or not b.get("required_job")
    ]
    chosen_def = random.choice(relevant or available)

    # Apply to the right building
    for building in state.buildings:
        if building.name == chosen_def["building_name"]:
            building.efficiency_bonus += chosen_def["bonus"]
            break

    bt = Breakthrough(
        year=state.year_int,
        title=chosen_def["title"],
        description=chosen_def["description"],
        building_id=chosen_def["building_name"],
        bonus=chosen_def["bonus"],
    )
    state.breakthroughs.append(bt)
    state.event_timeline.append(
        {
            "tick": state.tick,
            "year": state.year,
            "type": "breakthrough",
            "label": chosen_def["title"],
        }
    )
    state.optimism_active = True

    # Optimism fades after 8 ticks (2 months)
    state._optimism_ticks_remaining = 8

    announcement = (
        f"💡 EXPLANATORY BREAKTHROUGH: {chosen_def['title']}\n"
        f"{chosen_def['description']}\n"
        f"Production bonus: +{chosen_def['bonus'] * 100:.0f}% for {chosen_def['building_name']} permanently."
    )

    # Track proposer's notable action
    for c in state.living:
        if c.job == chosen_def.get("required_job") or not chosen_def.get(
            "required_job"
        ):
            c.add_notable_action(f"Year {state.year:.1f}: contributed to '{bt.title}'")
            break

    return announcement, bt


def tick_cultural_drift(state: WorldState) -> None:
    """
    Silently drift colonist traits each tick based on colony conditions.
    ~2% chance per living colonist per tick — creates gradual cultural evolution
    visible in the Cultural DNA bars without flooding the event feed.
    """
    if not state.living:
        return

    # Context-weighted trait pools
    scarce = (
        state.resources.get("oxygen", 100) < 25 or state.resources.get("food", 100) < 25
    )
    if scarce:
        drift_pool = ["stubborn", "fearful", "pragmatic", "resourceful", "risk-averse"]
    elif state.optimism_active:
        drift_pool = [
            "optimistic",
            "inventive",
            "cooperative",
            "ambitious",
            "scientific",
        ]
    elif state.crisis_active:
        drift_pool = ["risk-averse", "loyal", "pragmatic", "stubborn", "empathetic"]
    else:
        drift_pool = ALL_TRAITS  # random drift in stable times

    for c in state.living:
        if random.random() > 0.02:
            continue
        candidates = [t for t in drift_pool if t not in c.traits]
        if not candidates:
            continue
        new_trait = random.choice(candidates)
        old_trait = random.choice(c.traits)
        c.traits = [new_trait if t == old_trait else t for t in c.traits]


def tick_optimism(state: WorldState) -> None:
    """Call each tick to manage optimism duration."""
    if state.optimism_active:
        remaining = getattr(state, "_optimism_ticks_remaining", 0) - 1
        state._optimism_ticks_remaining = remaining
        if remaining <= 0:
            state.optimism_active = False
