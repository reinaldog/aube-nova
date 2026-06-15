import logging
import re

from llm.client import call_llm
from llm.narration import narrate_chronicle
from simulation.world import WorldState

logger = logging.getLogger(__name__)


def _clean_headline(text: str) -> str:
    """Strip surrounding quotes or escaped quotes that LLMs sometimes wrap headlines in."""
    text = text.strip()
    # Remove escaped quotes wrapping the whole headline: \"text\"
    if text.startswith('\\"') and text.endswith('\\"'):
        text = text[2:-2]
    # Remove plain double quotes wrapping the whole headline: "text"
    elif text.startswith('"') and text.endswith('"') and len(text) > 1:
        text = text[1:-1]
    # Remove plain single quotes wrapping the whole headline: 'text'
    elif text.startswith("'") and text.endswith("'") and len(text) > 1:
        text = text[1:-1]
    # Replace any remaining escaped quotes with plain quotes
    text = text.replace('\\"', '"').replace("\\'", "'")
    return text.strip()


CHRONICLE_SYSTEM = """\
You are the editor of The Aube Chronicle, official record of humanity's first
extraterrestrial colony. Year {year}. Write as a sober historian who knows
this document will be read centuries from now. Terse, specific, significant.

Respond in EXACTLY this format:
HEADLINE: <max 9 words — historic, factual, urgent>
ARTICLE_1: <3 sentences — the most consequential event this year>
ARTICLE_2: <2 sentences — a human moment: birth, loss, conflict, or discovery>"""


async def generate_chronicle(state: WorldState) -> dict:
    notable = sorted(state.living, key=lambda c: len(c.notable_actions), reverse=True)[
        :3
    ]
    notable_lines = []
    for c in notable:
        if c.notable_actions:
            notable_lines.append(
                f"- {c.name} ({c.job}): {'; '.join(c.notable_actions[:2])}"
            )

    breakthroughs_this_year = [
        b.title for b in state.breakthroughs if b.year == state.year_int
    ]
    previous_headline = state.chronicle[-1]["headline"] if state.chronicle else None

    system = CHRONICLE_SYSTEM.format(year=state.year_int)
    user = (
        "Key events this year:\n"
        + "\n".join(f"- {e}" for e in state.year_events[-20:])
        + f"\n\nPopulation: {len(state.living)}. "
        f"Resources: {', '.join(f'{k}={v:.0f}%' for k, v in state.resources.items())}.\n"
    )
    if notable_lines:
        user += "Significant colonists:\n" + "\n".join(notable_lines) + "\n"
    if breakthroughs_this_year:
        user += f"Breakthroughs: {', '.join(breakthroughs_this_year)}.\n"
    if previous_headline:
        user += f'\nLast year\'s headline: "{previous_headline}"\n'
        user += "Write this year's entry as a continuation of that story.\n"
    user += "Write the front page."

    raw = await call_llm(system, user, max_tokens=280)

    headline = f"Year {state.year_int}: Colony Endures"
    article1, article2 = "", ""
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("HEADLINE:"):
            headline = _clean_headline(stripped[9:])
        elif stripped.upper().startswith("ARTICLE_1:"):
            article1 = stripped[10:].strip()
        elif stripped.upper().startswith("ARTICLE_2:"):
            article2 = stripped[10:].strip()

    entry = {
        "year": state.year_int,
        "headline": headline,
        "article1": article1,
        "article2": article2,
        "type": "annual",
        "audio_path": None,
    }
    try:
        narration_text = f"{entry['headline']}. {entry['article1']} {entry['article2']}"
        entry["audio_path"] = narrate_chronicle(
            narration_text, f"year_{state.year_int}"
        )
    except Exception as _narration_err:
        logger.warning(f"Annual narration hook failed: {_narration_err}")
    state.chronicle.append(entry)
    state.year_events = []
    return entry


async def milestone_chronicle(
    state: WorldState, event_type: str, context: dict
) -> dict | None:
    """Fire a quick LLM call for a mid-year milestone headline."""
    system_map = {
        "death": (
            "You are The Aube Chronicle editor. Write a one-sentence obituary headline. "
            "Format: HEADLINE: <text>"
        ),
        "birth": (
            "You are The Aube Chronicle editor. Write a two-sentence birth announcement. "
            "Format: HEADLINE: <text>\nARTICLE_1: <text>"
        ),
        "breakthrough": (
            "You are The Aube Chronicle editor. Write a one-sentence breakthrough headline. "
            "Format: HEADLINE: <text>"
        ),
        "first_year_no_crisis": (
            "You are The Aube Chronicle editor. Write a one-sentence milestone headline. "
            "Format: HEADLINE: <text>"
        ),
    }
    user_map = {
        "death": (
            f"{context.get('name')} ({context.get('job')}, age {context.get('age', '?')}) "
            f"has died on Aube Nova. Colony year: {state.year:.1f}. "
            f"Notable actions: {'; '.join(context.get('notable_actions', []) or ['none recorded'])}."
        ),
        "birth": (
            f"A child has been born on Aube Nova. "
            f"Parents: {context.get('parent_a_name')} ({context.get('parent_a_job')}) and "
            f"{context.get('parent_b_name')} ({context.get('parent_b_job')}). "
            f"Colony year: {state.year:.1f}. Population: {len(state.living)}. "
            f"This is generation {context.get('generation', 1)} — "
            f"{'the first human born off Earth' if context.get('generation', 1) == 1 else 'a child of the colony'}."
        ),
        "breakthrough": (
            f"Breakthrough achieved: {context.get('title')}. "
            f"Proposed by {context.get('proposer', 'a colonist')}. Colony year: {state.year:.1f}."
        ),
        "first_year_no_crisis": (
            f"Year {state.year_int} passed without a single crisis — "
            f"the first in colony history. Population: {len(state.living)}."
        ),
    }

    sys_prompt = system_map.get(event_type)
    usr_prompt = user_map.get(event_type)
    if not sys_prompt or not usr_prompt:
        return None

    raw = await call_llm(sys_prompt, usr_prompt, max_tokens=80)

    headline, article1 = "", ""
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("HEADLINE:"):
            headline = _clean_headline(stripped[9:])
        elif stripped.upper().startswith("ARTICLE_1:"):
            article1 = stripped[10:].strip()

    if not headline:
        return None

    entry = {
        "year": round(state.year, 2),
        "headline": headline,
        "article1": article1,
        "article2": "",
        "type": event_type,
        "audio_path": None,
    }
    try:
        if event_type == "birth" and article1:
            narration_text = f"{headline}. {article1}"
        else:
            narration_text = headline
        if event_type == "death":
            safe_name = re.sub(r"[^a-z0-9]", "_", (context.get("name") or "").lower())
            cache_key = f"milestone_death_{safe_name}"
        elif event_type == "birth":
            safe_name = re.sub(
                r"[^a-z0-9]", "_", (context.get("parent_a_name") or "").lower()
            )
            cache_key = f"milestone_birth_{state.year_int}_{safe_name}"
        else:
            cache_key = f"milestone_{event_type}_{state.year_int}"
        entry["audio_path"] = narrate_chronicle(narration_text, cache_key)
    except Exception as _narration_err:
        logger.warning(f"Milestone narration hook failed: {_narration_err}")
    state.chronicle.append(entry)
    return entry
