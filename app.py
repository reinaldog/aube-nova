"""
Aube Nova — Humanity's First Autonomous Extraterrestrial Colony
Gradio application with interactive colony map, clickable colonist profiles,
scrollable event feed, and LLM-generated narrative.
"""

import asyncio
import random
from collections import Counter

import gradio as gr

from llm.agent import get_agent_action
from llm.breakthrough import generate_breakthrough_flavor
from llm.chronicle import generate_chronicle, milestone_chronicle
from simulation.colonist import Colonist
from simulation.events import (
    check_and_fire_crises,
    inject_manual_crisis,
    inject_optimism,
    tick_cultural_drift,
    tick_optimism,
)
from simulation.resources import tick_resources
from simulation.world import Building, WorldState
from ui.charts import (
    plot_cultural_drift,
    plot_population_history,
    plot_resource_history,
)
from ui.chronicle_view import render_all_chronicles
from ui.hud import render_colonist_profile, render_hud, render_llm_stats
from ui.map import render_map
from ui.portraits import render_roster


# ─── State factory ─────────────────────────────────────────────────────────────
def fresh_state() -> WorldState:
    state = WorldState()
    state.population = [Colonist.generate_starter(i) for i in range(12)]
    state.buildings = [
        Building(
            "b1",
            "Habitat",
            "operational",
            production={"oxygen": 16.0},
            consumption={"energy": 2.5},
        ),
        Building(
            "b2",
            "Greenhouse",
            "operational",
            production={"food": 14.0},
            consumption={"energy": 3.5},
        ),
        Building(
            "b3",
            "Reactor",
            "operational",
            production={"energy": 20.0},
            consumption={},
        ),
    ]
    return state


_state = fresh_state()
_selected_colonist_id: str | None = None


# ─── Feed helpers ───────────────────────────────────────────────────────────────
def _event_html(event: str, year: float) -> str:
    """Wrap a single event string as a styled HTML row."""
    if any(k in event for k in ("💀", "🕯️", "DIED", "died")):
        color, border = "#ff6688", "#ff4466"
    elif any(
        k in event
        for k in ("⚠️", "CRISIS INJECTED", "CRISIS", "STORM", "BLIGHT", "FAILURE")
    ):
        color, border = "#ff8844", "#ff6b35"
    elif "🔴 CRITICAL" in event:
        color, border = "#ff4444", "#ff2222"
    elif any(k in event for k in ("💡", "BREAKTHROUGH", "DISCOVERY")):
        color, border = "#ffe066", "#ffd700"
    elif "✅" in event:
        color, border = "#44cc66", "#00aa44"
    elif "⚡ WARNING" in event:
        color, border = "#ffd700", "#ccaa00"
    elif "🌊" in event:
        color, border = "#aa66ff", "#8844cc"
    else:
        color, border = "#6688aa", "#334455"

    return (
        f'<div style="border-left:2px solid {border};padding:4px 9px;margin:3px 0;'
        f"font-family:'Space Mono',monospace;font-size:9px;line-height:1.5\">"
        f'<span style="color:#334455;font-size:8px">Yr {year:.2f} </span>'
        f'<span style="color:{color}">{event}</span>'
        f"</div>"
    )


def _render_feed(feed_html_items: list[str]) -> str:
    inner = (
        "".join(feed_html_items[:60])
        if feed_html_items
        else (
            '<div style="color:#223344;font-size:10px;padding:12px;letter-spacing:1px">'
            "AWAITING FIRST TICK..."
            "</div>"
        )
    )
    return (
        f'<div style="height:560px;overflow-y:auto;background:#060b14;'
        f"border-radius:8px;padding:6px;"
        f'scrollbar-width:thin;scrollbar-color:#1f2937 transparent">'
        f"{inner}"
        f"</div>"
    )


# ─── Tick logic ────────────────────────────────────────────────────────────────
async def advance_tick() -> list[str]:
    global _state

    tick_optimism(_state)
    tick_cultural_drift(_state)
    crisis_events = check_and_fire_crises(_state)

    # snapshot alive set before resources tick (to detect new deaths)
    alive_before = {c.id for c in _state.living}

    resource_events = tick_resources(_state)

    # fire milestone chronicles for deaths and cultural drift (non-blocking)
    milestone_tasks: list = []

    for c in _state.population:
        if c.id in alive_before and not c.alive:
            milestone_tasks.append(
                milestone_chronicle(
                    _state,
                    "death",
                    {
                        "name": c.name,
                        "job": c.job,
                        "age": c.age,
                        "notable_actions": c.notable_actions,
                    },
                )
            )

    # annual checks
    if _state.tick % 52 == 0 and _state.tick > 0:
        gen_counts = Counter(c.generation for c in _state.living)
        _state.population_history.append(
            {
                "year": _state.year_int,
                "total": len(_state.living),
                "by_generation": dict(gen_counts),
            }
        )
        _state.cultural_profile_history.append(
            {
                "year": _state.year_int,
                "profile": _state.get_cultural_profile(),
            }
        )

        profile = _state.get_cultural_profile()
        new_top = next(iter(profile), None)
        old_top = _state.previous_cultural_top_trait
        if old_top and new_top and old_top != new_top:
            resource_events.append(
                f"🌊 Cultural shift: colony's defining trait moved from "
                f"'{old_top}' to '{new_top}'."
            )
        _state.previous_cultural_top_trait = new_top

        # first peaceful year milestone
        if not _state.year_had_crisis and _state.year_int > 1:
            milestone_tasks.append(
                milestone_chronicle(_state, "first_year_no_crisis", {})
            )
        _state.year_had_crisis = False

    actors = random.sample(_state.living, min(3, len(_state.living)))
    agent_coros = [get_agent_action(c, _state) for c in actors]

    # gather everything concurrently
    gathered = await asyncio.gather(
        *milestone_tasks, *agent_coros, return_exceptions=True
    )
    decisions = [r for r in gathered[len(milestone_tasks) :] if isinstance(r, dict)]

    agent_lines: list[str] = []
    for dec in decisions:
        line = f"**{dec['colonist']}** ({dec['action']}): {dec['effect']}"
        agent_lines.append(line)
        actor = next((c for c in _state.living if c.name == dec["colonist"]), None)
        if actor:
            actor.add_memory(dec["effect"])

    all_events = crisis_events + resource_events + agent_lines
    for e in all_events:
        _state.year_events.append(e)

    # annual chronicle
    if _state.tick % 52 == 0 and _state.tick > 0:
        await generate_chronicle(_state)

    return all_events


# ─── UI state builders ─────────────────────────────────────────────────────────
def _build_ui(feed_html: list[str]) -> tuple:
    return (
        render_map(_state, _selected_colonist_id),
        render_roster(_state.population, _selected_colonist_id),
        render_hud(_state),
        render_colonist_profile(
            next((c for c in _state.population if c.id == _selected_colonist_id), None),
            _state.get_cultural_profile(),
        ),
        _render_feed(feed_html),
        render_all_chronicles(_state.chronicle),
        feed_html,
        render_llm_stats(),
        plot_resource_history(_state),
        plot_population_history(_state),
        plot_cultural_drift(_state),
    )


# ─── Gradio callbacks ──────────────────────────────────────────────────────────
async def on_tick(feed_html: list[str]) -> tuple:
    events = await advance_tick()
    new_items = [_event_html(e, _state.year) for e in events]
    feed_html = new_items + feed_html
    return _build_ui(feed_html)


async def on_fast_forward(feed_html: list[str]) -> tuple:
    for _ in range(10):
        events = await advance_tick()
        new_items = [_event_html(e, _state.year) for e in events]
        feed_html = new_items + feed_html
    return _build_ui(feed_html)


def on_crisis(feed_html: list[str]) -> tuple:
    msg = inject_manual_crisis(_state)
    _state.year_had_crisis = True
    feed_html = [_event_html(msg, _state.year)] + feed_html
    return _build_ui(feed_html)


async def on_optimism(feed_html: list[str]) -> tuple:
    msg, bt = inject_optimism(_state)
    if bt:
        flavor = await generate_breakthrough_flavor(_state, bt)
        full_msg = msg + "\n\n" + flavor
        # milestone chronicle for breakthrough
        proposer = next(
            (c.name for c in _state.living if c.job == "researcher"),
            _state.living[0].name if _state.living else "a colonist",
        )
        await milestone_chronicle(
            _state,
            "breakthrough",
            {"title": bt.title, "proposer": proposer},
        )
    else:
        full_msg = msg
    feed_html = [_event_html(f"💡 {full_msg}", _state.year)] + feed_html
    return _build_ui(feed_html)


def on_reset(feed_html: list[str]) -> tuple:
    global _state, _selected_colonist_id
    _state = fresh_state()
    _selected_colonist_id = None
    feed_html = [_event_html("Colony reset. Year 0. 12 colonists. One chance.", 0.0)]
    return _build_ui(feed_html)


def on_colonist_select(colonist_id: str, feed_html: list[str]) -> tuple:
    global _selected_colonist_id
    _selected_colonist_id = colonist_id if colonist_id else None
    return _build_ui(feed_html)


# ─── CSS & HTML ────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=IM+Fell+English&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=Space+Mono:wght@400;700&family=IBM+Plex+Mono:wght@400;700&display=swap');

:root {
  --space: #010409;
  --panel: #060b14;
  --border: #1a2030;
  --text: #c8d8e8;
  --muted: #4a6a7a;
  --green: #00cc88;
  --amber: #ffe066;
  --red: #ff4466;
  --paper: #f5f0e8;
  --ink: #1a1410;
  --ochre: #c9893d;
}

*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container {
  background: var(--space) !important;
  color: var(--text) !important;
}

.gradio-container {
  max-width: 1600px !important;
}

footer { display: none !important; }

/* ── Map column: strip all Gradio chrome so SVG sits flush ────────────────── */
#col-map { gap: 0 !important; }
#col-map .block {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  box-shadow: none !important;
}

/* ── Middle feed/chronicle column ─────────────────────────────────────────── */
#col-feed .block {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 0 !important;
}

/* ── Right status column ───────────────────────────────────────────────────── */
#col-status { gap: 6px !important; }
#col-status .block {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 0 !important;
}

/* ── Tab navigation ────────────────────────────────────────────────────────── */
.tab-nav button {
  font-family: 'Space Mono', monospace !important;
  font-size: 9px !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
  background: #030710 !important;
  color: var(--muted) !important;
  border: 1px solid var(--border) !important;
  border-bottom: none !important;
  padding: 9px 16px !important;
  transition: color 0.15s, border-color 0.15s !important;
}
.tab-nav button.selected {
  color: var(--green) !important;
  border-color: var(--green) !important;
  background: #010d07 !important;
}
.tab-nav button:hover:not(.selected) {
  color: #8ab4c8 !important;
  border-color: #2a3a4a !important;
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
button.primary {
  background: linear-gradient(135deg, #005533, #00cc88) !important;
  color: #000 !important;
  font-family: 'Space Mono', monospace !important;
  font-weight: 700 !important;
  font-size: 10px !important;
  letter-spacing: 1.5px !important;
  border: none !important;
  border-radius: 4px !important;
  box-shadow: 0 0 14px rgba(0,204,136,0.25) !important;
  transition: box-shadow 0.2s, transform 0.15s !important;
}
button.primary:hover {
  box-shadow: 0 0 24px rgba(0,204,136,0.5) !important;
  transform: translateY(-1px);
}
button.stop {
  background: linear-gradient(135deg, #550011, #ff3355) !important;
  color: #fff !important;
  font-family: 'Space Mono', monospace !important;
  font-weight: 700 !important;
  font-size: 10px !important;
  letter-spacing: 1.5px !important;
  border: none !important;
  border-radius: 4px !important;
  box-shadow: 0 0 12px rgba(255,51,85,0.2) !important;
}
button.stop:hover {
  box-shadow: 0 0 22px rgba(255,51,85,0.45) !important;
  transform: translateY(-1px);
}
button.secondary {
  background: linear-gradient(135deg, #2a1800, #cc7700) !important;
  color: #ffe066 !important;
  font-family: 'Space Mono', monospace !important;
  font-weight: 700 !important;
  font-size: 10px !important;
  letter-spacing: 1.5px !important;
  border: 1px solid #ffe06633 !important;
  border-radius: 4px !important;
}
button.secondary:hover {
  box-shadow: 0 0 18px rgba(255,224,102,0.3) !important;
  transform: translateY(-1px);
}
button:not(.primary):not(.stop):not(.secondary) {
  background: #0c1420 !important;
  color: #4a7a9b !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 10px !important;
  letter-spacing: 1px !important;
  border: 1px solid #1a3040 !important;
  border-radius: 4px !important;
}
button:not(.primary):not(.stop):not(.secondary):hover {
  background: #18283a !important;
  color: #77bbdd !important;
}

/* ── Labels ───────────────────────────────────────────────────────────────── */
label, .label-wrap span {
  color: #3a5a6a !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 9px !important;
  letter-spacing: 1.5px !important;
}

/* ── Scrollbar ────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1e3040; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #2a4a5e; }

/* ── Controls row ─────────────────────────────────────────────────────────── */
#controls-row { padding: 8px 0 4px !important; gap: 8px !important; }

/* ── Ensure HTML content inherits dark-theme colour ──────────────────────── */
.prose, .prose p, .prose div { color: var(--text) !important; }
"""

TITLE_HTML = """
<div style="text-align:center;padding:22px 0 16px;font-family:'Space Mono',monospace;
            border-bottom:1px solid #0d1830;background:linear-gradient(to bottom,#080e1e,#010409);
            position:relative">
  <div style="position:absolute;left:20px;top:18px;color:#4a7a9b;font-size:8px;
              letter-spacing:2px;line-height:1.8">
    AUBE-NOVA-SIM<br/>
    <span style="color:#3a6a8a">MISSION CONTROL v2.0</span>
  </div>
  <div style="position:absolute;right:20px;top:18px;font-size:8px;
              letter-spacing:2px;line-height:1.8;text-align:right">
    <span style="color:#4a7a9b">PROTOCOL: </span><span style="color:#00cc88">ACTIVE</span><br/>
    <span style="color:#4a7a9b">MODEL: </span><span style="color:#4488ff">MiniCPM4.1-8B</span>
  </div>
  <div style="font-size:44px;letter-spacing:14px;color:#00cc88;font-weight:700;
              text-shadow:0 0 40px rgba(0,204,136,0.35)">AUBE NOVA</div>
  <div style="font-size:10px;color:#5a9ab8;letter-spacing:3px;margin-top:7px">
    HUMANITY'S FIRST AUTONOMOUS EXTRATERRESTRIAL COLONY · POWERED BY SMALL LANGUAGE MODELS
  </div>
  <div style="font-size:8px;color:#3a7a96;letter-spacing:2px;margin-top:5px">
    EVERY DECISION GENERATED BY AI · CIVILIZATION EMERGING FROM MANY CONSTRAINED CHOICES
  </div>
</div>"""

CONTROLS_LABEL = """
<div style="font-family:'Space Mono',monospace;font-size:8px;color:#3a6a8a;
            letter-spacing:2px;margin-bottom:6px;text-align:center">
  ─────────────────────── SIMULATION CONTROLS ───────────────────────
</div>"""

# ─── Build the Gradio app ──────────────────────────────────────────────────────
with gr.Blocks(title="Aube Nova") as demo:
    gr.HTML(TITLE_HTML)
    feed_state = gr.State([])

    # ── 3-column main layout ───────────────────────────────────────────────────
    with gr.Row(equal_height=True, elem_id="main-row"):
        # Left: map + roster (no gap between them)
        with gr.Column(scale=6, elem_id="col-map"):
            map_out = gr.HTML(label="COLONY MAP")
            roster_out = gr.HTML(label="COLONISTS")

        # Middle: tabbed feed / chronicle / analytics
        with gr.Column(scale=5, elem_id="col-feed"):
            with gr.Tabs(elem_id="main-tabs"):
                with gr.Tab("📡  EVENTS"):
                    feed_out = gr.HTML()
                with gr.Tab("📰  CHRONICLE"):
                    chronicle_out = gr.HTML()
                with gr.Tab("📊  ANALYTICS"):
                    analytics_refresh_btn = gr.Button("↻ Refresh Charts", size="sm")
                    resource_plot = gr.Plot(label="Resource Trends")
                    population_plot = gr.Plot(label="Population by Generation")
                    drift_plot = gr.Plot(label="Cultural Trait Drift")

        # Right: compact status + colonist profile
        with gr.Column(scale=3, elem_id="col-status"):
            llm_stats_out = gr.HTML(label="MODEL STATUS")
            hud_out = gr.HTML(label="COLONY STATUS")
            profile_out = gr.HTML(label="COLONIST PROFILE")

    # ── Controls ───────────────────────────────────────────────────────────────
    gr.HTML(CONTROLS_LABEL)
    with gr.Row(elem_id="controls-row"):
        tick_btn = gr.Button("▶ ADVANCE WEEK", variant="primary", scale=2)
        ff_btn = gr.Button("⏩ FAST-FORWARD 10W", variant="primary", scale=2)
        crisis_btn = gr.Button("💥 INJECT CRISIS", variant="stop", scale=1)
        optimism_btn = gr.Button("💡 BREAKTHROUGH", variant="secondary", scale=2)
        reset_btn = gr.Button("↺ NEW COLONY", scale=1)

    # ── Hidden colonist selector textbox (JS → Python bridge) ─────────────────
    colonist_tb = gr.Textbox(
        value="",
        visible=False,
        elem_id="colonist-selector",
    )

    # ── Output list ────────────────────────────────────────────────────────────
    ALL_OUT = [
        map_out,
        roster_out,
        hud_out,
        profile_out,
        feed_out,
        chronicle_out,
        feed_state,
        llm_stats_out,
        resource_plot,
        population_plot,
        drift_plot,
    ]

    # ── Wire up events ─────────────────────────────────────────────────────────
    tick_btn.click(on_tick, [feed_state], ALL_OUT)
    ff_btn.click(on_fast_forward, [feed_state], ALL_OUT)
    crisis_btn.click(on_crisis, [feed_state], ALL_OUT)
    optimism_btn.click(on_optimism, [feed_state], ALL_OUT)
    reset_btn.click(on_reset, [feed_state], ALL_OUT)
    demo.load(on_reset, [feed_state], ALL_OUT)

    # colonist click updates map, roster, profile, and llm stats
    # Use .input (not .change) so programmatic JS dispatches fire immediately
    colonist_tb.input(
        on_colonist_select,
        inputs=[colonist_tb, feed_state],
        outputs=ALL_OUT,
    )

    def _refresh_analytics():
        return (
            plot_resource_history(_state),
            plot_population_history(_state),
            plot_cultural_drift(_state),
        )

    analytics_refresh_btn.click(
        _refresh_analytics,
        outputs=[resource_plot, population_plot, drift_plot],
    )

demo.launch(css=CSS)
