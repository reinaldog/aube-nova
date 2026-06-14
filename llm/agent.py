import random

from llm.client import call_llm
from simulation.colonist import Colonist
from simulation.world import WorldState

AGENT_SYSTEM = """\
You are {name}, a human colonist on Aube Nova, humanity's first extraterrestrial colony.
Year {year}. Your job: {job}. Your traits: {traits}.
{optimism_note}

Respond in EXACTLY this format — no other text:
ACTION: <one of: work | trade | help | argue | organize | rest | repair>
EFFECT: <one sentence — what you did and its immediate result, specific and vivid>

Be specific. Reference real colony conditions. Stay in character."""

OPTIMISM_NOTE = (
    "The colony just made a major breakthrough. "
    "You feel the contagious energy of progress — humans can solve anything."
)

FALLBACK_EFFECTS: dict[str, list[str]] = {
    "engineer": [
        "ran diagnostics on the power conduits, flagging a micro-fracture for later repair.",
        "spent the morning calibrating the reactor's load-balancing circuits.",
        "patched a coolant leak in the reactor housing before it could worsen.",
        "tested the backup oxygen scrubbers; found them 15% below optimal pressure.",
        "re-routed power from non-essential systems to stabilise the grid.",
    ],
    "farmer": [
        "checked the hydroponic trays in Bay 3 and adjusted nutrient flow ratios.",
        "noted unusual yellowing in the wheat crop and filed a report with the medic.",
        "harvested a tray of leafy greens ahead of schedule and shared them with the crew.",
        "reprogrammed the greenhouse irrigation timers for higher efficiency.",
        "transplanted seedlings to the secondary bay to maximise yield.",
    ],
    "medic": [
        "conducted routine health checks on three colonists, noting elevated stress markers.",
        "prepared a batch of vitamin supplements from the greenhouse's medicinal plants.",
        "reviewed the colony's emergency medical protocols and updated the triage checklist.",
        "treated two minor lacerations from habitat maintenance work.",
        "monitored air quality in the sleeping quarters, adjusting CO₂ filters.",
    ],
    "researcher": [
        "analysed atmospheric data from the previous week, looking for anomalous patterns.",
        "wrote up findings on local soil composition and its implications for farming.",
        "reviewed sensor logs from the oxygen plant; noted a slow efficiency decline.",
        "spent hours in the data archive, cross-referencing colony performance metrics.",
        "ran simulations on resource consumption projections for the next six months.",
    ],
    "miner": [
        "surveyed a new extraction site 200 metres north of the dome perimeter.",
        "catalogued the day's ore samples, finding traces of useful rare-earth minerals.",
        "serviced the drilling equipment to prevent a costly breakdown.",
        "mapped a promising subsurface vein for next week's crew to explore.",
        "reinforced the mine shaft entrance to reduce collapse risk.",
    ],
    "builder": [
        "reinforced the eastern wall of the habitat module with scrap plating.",
        "inspected the dome seal for micro-fractures; found one and patched it quickly.",
        "drew up specs for a planned storage expansion off the main corridor.",
        "welded a cracked support beam in the greenhouse access tunnel.",
        "assembled a new airlock pressure gauge from salvaged components.",
    ],
}

FALLBACK_ACTIONS: dict[str, str] = {
    "engineer": "repair",
    "farmer": "work",
    "medic": "help",
    "researcher": "work",
    "miner": "work",
    "builder": "repair",
}

CRISIS_EFFECTS: dict[str, dict[str, str]] = {
    "oxygen": {
        "engineer": "raced to the reactor room and manually re-pressurised the oxygen feed valve.",
        "medic": "distributed emergency oxygen masks and triaged the most vulnerable colonists.",
        "farmer": "sealed the greenhouse vents to conserve the colony's remaining oxygen supply.",
        "researcher": "ran rapid diagnostics on the O₂ scrubbers, pinpointing a faulty membrane.",
        "miner": "evacuated the mine shafts and reported to the dome's emergency muster point.",
        "builder": "reinforced the habitat's pressure seals to slow the oxygen bleed.",
    },
    "food": {
        "engineer": "recalibrated the greenhouse climate system to maximise emergency crop growth.",
        "medic": "rationed the remaining food supplies carefully, prioritising the injured.",
        "farmer": "worked double shifts in the greenhouse, coaxing extra yield from every tray.",
        "researcher": "identified fast-growing species in the seed bank and proposed an emergency planting.",
        "miner": "traded mineral samples with the supply drone for emergency ration packs.",
        "builder": "constructed additional hydroponic shelving to expand the growing capacity.",
    },
}


async def get_agent_action(colonist: Colonist, state: WorldState) -> dict:
    res_summary = ", ".join(f"{k}={v:.0f}%" for k, v in state.resources.items())
    crisis_note = (
        f" ACTIVE CRISIS: {state.crisis_active}." if state.crisis_active else ""
    )
    memories = "; ".join(colonist.memory[-2:]) if colonist.memory else "no prior events"

    system = AGENT_SYSTEM.format(
        name=colonist.name,
        year=f"{state.year:.1f}",
        job=colonist.job,
        traits=", ".join(colonist.traits),
        optimism_note=OPTIMISM_NOTE if state.optimism_active else "",
    )
    user = (
        f"Colony status: {res_summary}.{crisis_note}\n"
        f"Recent events you witnessed: {memories}\n"
        "What do you do this week?"
    )

    raw = await call_llm(system, user, max_tokens=80)

    # Detect error / unparseable response
    is_fallback = raw.startswith("[") or not any(
        line.strip().upper().startswith(("ACTION:", "EFFECT:"))
        for line in raw.splitlines()
    )

    if is_fallback:
        # Use crisis-specific fallback if relevant
        if state.crisis_active:
            for crisis_key in ("oxygen", "food"):
                if crisis_key in state.crisis_active:
                    effect = CRISIS_EFFECTS.get(crisis_key, {}).get(
                        colonist.job,
                        f"responded to the {crisis_key} crisis as best they could.",
                    )
                    return {
                        "colonist": colonist.name,
                        "action": "help" if colonist.job == "medic" else "work",
                        "effect": effect,
                    }
        effect = random.choice(
            FALLBACK_EFFECTS.get(colonist.job, FALLBACK_EFFECTS["engineer"])
        )
        return {
            "colonist": colonist.name,
            "action": FALLBACK_ACTIONS.get(colonist.job, "rest"),
            "effect": effect,
        }

    action = "rest"
    effect = random.choice(FALLBACK_EFFECTS.get(colonist.job, ["worked quietly."]))
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("ACTION:"):
            action = stripped[7:].strip().lower()
        elif stripped.upper().startswith("EFFECT:"):
            effect = stripped[7:].strip()

    return {"colonist": colonist.name, "action": action, "effect": effect}
