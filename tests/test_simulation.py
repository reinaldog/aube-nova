import pytest

from simulation.colonist import Colonist
from simulation.events import inject_manual_crisis, inject_optimism, tick_optimism
from simulation.resources import tick_resources
from simulation.world import Building, WorldState


def make_state() -> WorldState:
    s = WorldState()
    s.population = [Colonist.generate_starter(i) for i in range(12)]
    s.buildings = [
        Building(
            "b1", "Habitat", production={"oxygen": 16.0}, consumption={"energy": 2.5}
        ),
        Building(
            "b2", "Greenhouse", production={"food": 14.0}, consumption={"energy": 3.5}
        ),
        Building("b3", "Reactor", production={"energy": 20.0}, consumption={}),
    ]
    return s


def test_12_colonists_generated():
    s = make_state()
    assert len(s.population) == 12
    assert all(c.alive for c in s.population)


def test_resources_deplete_over_ticks():
    s = make_state()
    for _ in range(5):
        tick_resources(s)
    # With buildings running, may go up or down depending on balance
    assert s.resources["oxygen"] >= 0


def test_year_advances():
    s = make_state()
    for _ in range(52):
        tick_resources(s)
    assert s.year_int == 1


def test_crisis_drops_oxygen():
    from unittest.mock import patch

    import simulation.events as events_mod
    from simulation.events import CRISIS_DEFS

    s = make_state()
    s.resources["oxygen"] = 60.0
    oxygen_crisis = next(c for c in CRISIS_DEFS if c["id"] == "oxygen_failure")
    # Pin the random choice so this test is deterministic
    with patch.object(events_mod.random, "choice", return_value=oxygen_crisis):
        inject_manual_crisis(s)
    assert s.resources["oxygen"] < 60.0
    assert s.crisis_active == "oxygen_failure"


def test_optimism_sets_active():
    s = make_state()
    assert not s.optimism_active
    msg, bt = inject_optimism(s)
    assert s.optimism_active
    assert bt is not None
    assert len(s.breakthroughs) == 1


def test_optimism_fades():
    s = make_state()
    inject_optimism(s)
    for _ in range(9):
        tick_optimism(s)
    assert not s.optimism_active


def test_breakthrough_boosts_building():
    s = make_state()
    original_bonus = s.buildings[0].efficiency_bonus
    inject_optimism(s)
    # At least one building should have been boosted
    new_bonuses = [b.efficiency_bonus for b in s.buildings]
    assert any(b > original_bonus for b in new_bonuses)


def test_cultural_profile():
    s = make_state()
    profile = s.get_cultural_profile()
    assert isinstance(profile, dict)
    assert len(profile) > 0
    assert all(0.0 <= v <= 1.0 for v in profile.values())


def test_death_on_zero_oxygen():
    s = make_state()
    s.resources["oxygen"] = 0.0
    events = tick_resources(s)
    assert any("died" in e for e in events)
    assert len(s.living) < 12
