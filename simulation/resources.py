import random as _random

from simulation.world import WorldState

CONSUMPTION_PER_PERSON_PER_TICK = {
    "oxygen": 0.7,
    "food": 0.55,
    "energy": 0.18,
}

JOB_PRODUCTION_PER_TICK = {
    "farmer": {"food": 2.2},
    "engineer": {"energy": 1.8},
    "miner": {"credits": 1.4},
    "researcher": {"credits": 0.6},
    "medic": {},
    "builder": {},
}


def tick_resources(state: WorldState) -> list[str]:
    events = []
    n = max(1, len(state.living))

    for resource, rate in CONSUMPTION_PER_PERSON_PER_TICK.items():
        state.resources[resource] -= rate * n

    # Record which vital resources dipped into deficit after consumption so the death
    # check below (which runs AFTER production) still knows starvation/asphyxiation
    # occurred this tick, even if buildings manage to rescue the level.
    depleted_after_consumption = {
        r for r in ("oxygen", "food") if state.resources[r] <= 0
    }

    # Building production (moved before death check so a breakthrough has a chance to save
    # colonists)
    optimism_multiplier = 1.25 if state.optimism_active else 1.0
    for building in state.buildings:
        if building.status == "operational":
            effective_bonus = building.efficiency_bonus * optimism_multiplier
            for res, amount in building.production.items():
                state.resources[res] += amount * effective_bonus
            for res, amount in building.consumption.items():
                state.resources[res] -= amount

    # Job production
    for colonist in state.living:
        for res, amount in JOB_PRODUCTION_PER_TICK.get(colonist.job, {}).items():
            state.resources[res] += amount * 0.4

    # Clamp 0–150
    for k in state.resources:
        state.resources[k] = max(0.0, min(150.0, state.resources[k]))

    # Death check — runs after all production so a breakthrough can intervene.
    # Fires for every resource that dipped into deficit during the consumption phase.
    # If optimism is active AND production rescued the resource back above 0, colonists
    # get a 50% survival chance: a breakthrough is inspiring but not a guaranteed miracle.
    for resource in depleted_after_consumption:
        if state.optimism_active and state.resources[resource] > 0:
            # Dramatic tension: flip a coin — the euphoria of a breakthrough may save them
            if _random.random() < 0.5:
                continue
        candidates = sorted(state.living, key=lambda c: c.health)
        if candidates:
            victim = candidates[0]
            victim.alive = False
            cause = "oxygen deprivation" if resource == "oxygen" else "starvation"
            events.append(
                f"💀 {victim.name} ({victim.job}, age {victim.age}) died of {cause}. "
                f"Colony: {len(state.living)} remaining."
            )
            state.event_timeline.append(
                {
                    "tick": state.tick,
                    "year": state.year,
                    "type": "death",
                    "label": victim.name,
                }
            )
            state.year_had_crisis = True

    # Morale shifts based on colony conditions
    oxygen = state.resources["oxygen"]
    food = state.resources["food"]
    energy = state.resources["energy"]
    for colonist in state.living:
        delta = 0.0
        if oxygen < 15 or food < 15:
            delta -= 3.0  # severe scarcity: morale crashes
        elif oxygen < 30 or food < 30:
            delta -= 1.5  # low supplies: morale drops
        elif oxygen > 70 and food > 70 and energy > 60:
            delta += 0.4  # abundant colony: morale slowly rises
        if energy < 20:
            delta -= 1.0  # power shortages hurt morale
        if state.optimism_active:
            delta += 0.8  # breakthrough euphoria
        delta += _random.uniform(-0.3, 0.3)  # individual variance
        colonist.morale = max(5.0, min(100.0, colonist.morale + delta))

    # Crisis warnings
    for resource, value in state.resources.items():
        if value < 10.0:
            events.append(
                f"🔴 CRITICAL: {resource.upper()} at {value:.0f}% — lives at risk"
            )
            state.crisis_active = f"{resource}_critical"
            state.year_had_crisis = True
        elif value < 25.0:
            events.append(f"⚡ WARNING: {resource} reserves low ({value:.0f}%)")

    # Clear resolved crises
    if state.crisis_active:
        if state.crisis_active.endswith("_critical"):
            # Resource-level critical warnings: clear when resource recovers
            res_name = state.crisis_active.replace("_critical", "")
            if state.resources.get(res_name, 100) > 30:
                events.append(f"✅ {res_name.upper()} crisis resolved.")
                state.crisis_active = None
                state.crisis_duration_remaining = 0
        else:
            # Named crises (food_blight, oxygen_failure, etc.): expire after duration
            state.crisis_duration_remaining = max(
                0, state.crisis_duration_remaining - 1
            )
            if state.crisis_duration_remaining <= 0:
                # Restore any strained buildings when the crisis ends
                for b in state.buildings:
                    if b.status == "strained":
                        b.status = "operational"
                        events.append(f"✅ {b.name} fully restored to operation.")
                state.crisis_active = None

    # Annual aging (at year boundary)
    if state.tick > 0 and state.tick % 52 == 0:
        for colonist in state.living:
            colonist.age += 1
            if colonist.age > 75 and _random.random() < 0.15:
                colonist.alive = False
                events.append(
                    f"🕯️ {colonist.name} ({colonist.job}, age {colonist.age}) "
                    f"passed away — one of the colony's original settlers."
                )

    # Advance time
    state.tick += 1
    state.year = state.tick / 52.0

    state.resource_history.append(
        {
            "tick": state.tick,
            "year": state.year,
            "oxygen": state.resources["oxygen"],
            "food": state.resources["food"],
            "energy": state.resources["energy"],
            "credits": state.resources["credits"],
        }
    )

    return events
