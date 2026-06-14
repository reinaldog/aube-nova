"""
Optional: LLM-generated flavor text for breakthroughs.
Call this AFTER inject_optimism() for a richer announcement.
"""

from llm.client import call_llm
from simulation.world import Breakthrough, WorldState


async def generate_breakthrough_flavor(state: WorldState, bt: Breakthrough) -> str:
    """Generate a vivid 2-sentence description of how the breakthrough happened."""
    system = (
        "You describe scientific discoveries in a space colony. "
        "Write 2 sentences: who proposed the explanation and how the colony adopted it. "
        "Be specific, name a colonist if possible, and make it feel historic."
    )
    colonist_names = [c.name for c in state.living if c.job == "researcher"]
    proposer = (
        colonist_names[0]
        if colonist_names
        else state.living[0].name
        if state.living
        else "a colonist"
    )

    user = (
        f"The colony just achieved: {bt.title}.\n"
        f"The proposer was likely: {proposer} (researcher).\n"
        f"Colony year: {state.year:.1f}. Write 2 sentences."
    )
    return await call_llm(system, user, max_tokens=100)
