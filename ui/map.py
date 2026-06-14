"""
Colony map renderer — a detailed SVG showing the Aube Nova settlement.
"""

from __future__ import annotations

import random

from simulation.world import WorldState

# Job → map position (cx, cy) for colonist tokens
_JOB_POSITIONS: dict[str, list[tuple[int, int]]] = {
    "engineer": [(360, 400), (445, 395), (400, 420)],
    "farmer": [(505, 272), (560, 285), (535, 260)],
    "medic": [(215, 272), (250, 290), (230, 255)],
    "researcher": [(335, 275), (375, 285), (355, 260)],
    "miner": [(290, 355), (315, 378), (275, 375)],
    "builder": [(505, 355), (488, 378), (525, 375)],
}

# Fallback ring of positions for overflow colonists
_FALLBACK_POS: list[tuple[int, int]] = [
    (400, 268),
    (328, 328),
    (472, 328),
    (400, 392),
    (278, 308),
    (522, 308),
    (360, 248),
    (440, 248),
]

STATUS_COLORS = {
    "operational": "#00cc88",
    "strained": "#ffd700",
    "critical": "#ff4444",
    "offline": "#444455",
}


def _stars() -> str:
    rng = random.Random(42)
    out: list[str] = []
    for _ in range(88):
        x = rng.randint(0, 800)
        y = rng.randint(0, 445)
        r = round(rng.uniform(0.4, 1.7), 1)
        op = round(rng.uniform(0.25, 0.95), 2)
        if rng.random() < 0.18:
            d = round(rng.uniform(1.5, 4.8), 1)
            lo = round(op * 0.25, 2)
            out.append(
                f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" opacity="{op}">'
                f'<animate attributeName="opacity" values="{op};{lo};{op}" '
                f'dur="{d}s" repeatCount="indefinite"/></circle>'
            )
        else:
            out.append(
                f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" opacity="{op}"/>'
            )
    return "".join(out)


_STARS_CACHE: str | None = None


def _get_stars() -> str:
    global _STARS_CACHE
    if _STARS_CACHE is None:
        _STARS_CACHE = _stars()
    return _STARS_CACHE


def _habitat_svg(building, selected: bool = False) -> str:
    status = building.status if building else "offline"
    c = STATUS_COLORS.get(status, "#444455")
    bonus = (
        f"+{(building.efficiency_bonus - 1) * 100:.0f}%"
        if building and building.efficiency_bonus > 1.0
        else ""
    )
    damaged = status in ("strained", "critical", "offline")
    win_color = "#1a1a1a" if damaged else "#ffe066"
    w1 = (
        f'<animate attributeName="opacity" values="0.7;1;0.7" dur="3.2s" '
        f'repeatCount="indefinite"/>'
        if not damaged
        else ""
    )
    w2 = (
        f'<animate attributeName="opacity" values="0.4;0.85;0.4" dur="4.7s" '
        f'repeatCount="indefinite"/>'
        if not damaged
        else ""
    )
    crisis_ring = ""
    if status == "strained":
        crisis_ring = (
            '<rect x="196" y="203" width="168" height="71" rx="5" fill="none" '
            'stroke="#ffd700" stroke-width="2.5">'
            '<animate attributeName="opacity" values="0.3;0.8;0.3" dur="0.9s" repeatCount="indefinite"/>'
            "</rect>"
        )
    elif status == "critical":
        crisis_ring = (
            '<rect x="196" y="203" width="168" height="71" rx="5" fill="none" '
            'stroke="#ff2222" stroke-width="3.5">'
            '<animate attributeName="opacity" values="0.4;1;0.4" dur="0.5s" repeatCount="indefinite"/>'
            "</rect>"
        )
    sel_ring = (
        '<rect x="192" y="199" width="176" height="79" rx="7" fill="none" '
        'stroke="white" stroke-width="2" opacity="0.6"/>'
        if selected
        else ""
    )
    bonus_label = (
        f'<text x="280" y="197" font-family="Space Mono,monospace" font-size="8" '
        f'fill="#00ff9d" text-anchor="middle">{bonus}</text>'
        if bonus
        else ""
    )
    return f"""
    <!-- ── HABITAT MODULE ── -->
    <g id="habitat">
      <!-- shadow -->
      <rect x="200" y="213" width="163" height="68" rx="3" fill="#030810" opacity="0.7"/>
      <!-- hull -->
      <rect x="197" y="206" width="162" height="66" rx="5"
            fill="#0c1e32" stroke="{c}" stroke-width="1.8"/>
      <!-- structural ribs -->
      <line x1="237" y1="206" x2="237" y2="272" stroke="{c}" stroke-width="0.5" opacity="0.25"/>
      <line x1="278" y1="206" x2="278" y2="272" stroke="{c}" stroke-width="0.5" opacity="0.25"/>
      <line x1="319" y1="206" x2="319" y2="272" stroke="{c}" stroke-width="0.5" opacity="0.25"/>
      <!-- windows row 1 -->
      <rect x="210" y="216" width="18" height="12" rx="2" fill="{win_color}" opacity="0.88">{w1}</rect>
      <rect x="244" y="216" width="18" height="12" rx="2" fill="{win_color}" opacity="0.72">{w2}</rect>
      <rect x="278" y="216" width="18" height="12" rx="2" fill="{win_color}" opacity="0.90">{w1}</rect>
      <rect x="312" y="216" width="18" height="12" rx="2" fill="{win_color}" opacity="0.60">{w2}</rect>
      <!-- windows row 2 -->
      <rect x="210" y="239" width="18" height="10" rx="2" fill="{win_color}" opacity="0.50"/>
      <rect x="244" y="239" width="18" height="10" rx="2" fill="{win_color}" opacity="0.70"/>
      <rect x="278" y="239" width="18" height="10" rx="2" fill="{win_color}" opacity="0.45"/>
      <!-- airlock -->
      <rect x="341" y="213" width="22" height="48" rx="11" fill="#0c1e32" stroke="{c}" stroke-width="1"/>
      <circle cx="352" cy="235" r="7" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.6"/>
      <line x1="345" y1="235" x2="359" y2="235" stroke="{c}" stroke-width="0.7" opacity="0.6"/>
      <line x1="352" y1="228" x2="352" y2="242" stroke="{c}" stroke-width="0.7" opacity="0.6"/>
      <!-- solar array -->
      <rect x="212" y="197" width="115" height="8" fill="#101830" stroke="#223355" stroke-width="0.5"/>
      <line x1="237" y1="197" x2="237" y2="205" stroke="#2244aa" stroke-width="0.5" opacity="0.55"/>
      <line x1="262" y1="197" x2="262" y2="205" stroke="#2244aa" stroke-width="0.5" opacity="0.55"/>
      <line x1="287" y1="197" x2="287" y2="205" stroke="#2244aa" stroke-width="0.5" opacity="0.55"/>
      <line x1="312" y1="197" x2="312" y2="205" stroke="#2244aa" stroke-width="0.5" opacity="0.55"/>
      <!-- connecting tube to center -->
      <rect x="359" y="231" width="32" height="11" fill="#0c1e32" stroke="{c}" stroke-width="0.8" opacity="0.7"/>
      {crisis_ring}{sel_ring}
      <!-- label -->
      <text x="280" y="193" font-family="Space Mono,monospace" font-size="9"
            fill="{c}" text-anchor="middle" opacity="0.85">HABITAT MODULE</text>
      {bonus_label}
    </g>"""


def _greenhouse_svg(building, selected: bool = False) -> str:
    status = building.status if building else "offline"
    c = STATUS_COLORS.get(status, "#444455")
    bonus = (
        f"+{(building.efficiency_bonus - 1) * 100:.0f}%"
        if building and building.efficiency_bonus > 1.0
        else ""
    )
    damaged = status in ("strained", "critical", "offline")
    plant_glow = (
        ""
        if damaged
        else (
            '<ellipse cx="548" cy="230" rx="56" ry="24" fill="#00ff44" opacity="0.05">'
            '<animate attributeName="opacity" values="0.03;0.1;0.03" dur="4s" repeatCount="indefinite"/>'
            "</ellipse>"
        )
    )
    crisis_ring = ""
    if status == "strained":
        crisis_ring = (
            '<polygon points="548,152 488,268 608,268" fill="none" '
            'stroke="#ffd700" stroke-width="2.5">'
            '<animate attributeName="opacity" values="0.3;0.8;0.3" dur="0.9s" repeatCount="indefinite"/>'
            "</polygon>"
        )
    elif status == "critical":
        crisis_ring = (
            '<polygon points="548,152 488,268 608,268" fill="none" '
            'stroke="#ff2222" stroke-width="3.5">'
            '<animate attributeName="opacity" values="0.4;1;0.4" dur="0.5s" repeatCount="indefinite"/>'
            "</polygon>"
        )
    sel_ring = (
        '<polygon points="548,147 483,271 613,271" fill="none" '
        'stroke="white" stroke-width="2" opacity="0.6"/>'
        if selected
        else ""
    )
    bonus_label = (
        f'<text x="548" y="142" font-family="Space Mono,monospace" font-size="8" '
        f'fill="#00ff9d" text-anchor="middle">{bonus}</text>'
        if bonus
        else ""
    )
    return f"""
    <!-- ── GREENHOUSE ── -->
    <g id="greenhouse">
      <!-- shadow -->
      <polygon points="548,162 493,274 603,274" fill="#020806" opacity="0.7"/>
      <!-- glass panels -->
      <polygon points="548,152 488,268 608,268" fill="#0a1e0c" stroke="{c}" stroke-width="1.8"/>
      <!-- panel grid lines -->
      <line x1="548" y1="152" x2="508" y2="220" stroke="{c}" stroke-width="0.5" opacity="0.45"/>
      <line x1="548" y1="152" x2="518" y2="268" stroke="{c}" stroke-width="0.5" opacity="0.45"/>
      <line x1="548" y1="152" x2="538" y2="268" stroke="{c}" stroke-width="0.5" opacity="0.45"/>
      <line x1="548" y1="152" x2="558" y2="268" stroke="{c}" stroke-width="0.5" opacity="0.45"/>
      <line x1="548" y1="152" x2="578" y2="268" stroke="{c}" stroke-width="0.5" opacity="0.45"/>
      <line x1="548" y1="152" x2="588" y2="220" stroke="{c}" stroke-width="0.5" opacity="0.45"/>
      <!-- cross bars -->
      <line x1="508" y1="200" x2="588" y2="200" stroke="{c}" stroke-width="0.5" opacity="0.38"/>
      <line x1="498" y1="230" x2="598" y2="230" stroke="{c}" stroke-width="0.5" opacity="0.38"/>
      <line x1="492" y1="252" x2="604" y2="252" stroke="{c}" stroke-width="0.5" opacity="0.32"/>
      <!-- plant glow -->
      {plant_glow}
      <!-- base foundation -->
      <rect x="484" y="264" width="128" height="8" rx="2" fill="#0a1e0c" stroke="{c}" stroke-width="0.6"/>
      <!-- ventilation unit -->
      <rect x="542" y="143" width="12" height="10" rx="2" fill="#0a1e0c" stroke="{c}" stroke-width="0.7"/>
      <rect x="544" y="137" width="8" height="7" rx="1" fill="{c}" opacity="0.35"/>
      {crisis_ring}{sel_ring}
      <!-- label -->
      <text x="548" y="138" font-family="Space Mono,monospace" font-size="9"
            fill="{c}" text-anchor="middle" opacity="0.85">GREENHOUSE</text>
      {bonus_label}
    </g>"""


def _reactor_svg(building, selected: bool = False) -> str:
    status = building.status if building else "offline"
    c = STATUS_COLORS.get(status, "#444455")
    bonus = (
        f"+{(building.efficiency_bonus - 1) * 100:.0f}%"
        if building and building.efficiency_bonus > 1.0
        else ""
    )
    damaged = status in ("strained", "critical", "offline")
    core_anim = (
        ""
        if damaged
        else (
            '<animate attributeName="opacity" values="0.12;0.38;0.12" dur="1.6s" repeatCount="indefinite"/>'
        )
    )
    pulse_anim = (
        ""
        if damaged
        else (
            '<animate attributeName="opacity" values="0.3;0.75;0.3" dur="1.6s" repeatCount="indefinite"/>'
        )
    )
    crisis_ring = ""
    if status == "strained":
        crisis_ring = (
            '<polygon points="400,308 437,329 437,371 400,392 363,371 363,329" '
            'fill="none" stroke="#ffd700" stroke-width="3">'
            '<animate attributeName="opacity" values="0.3;0.8;0.3" dur="0.9s" repeatCount="indefinite"/>'
            "</polygon>"
        )
    elif status == "critical":
        crisis_ring = (
            '<polygon points="400,308 437,329 437,371 400,392 363,371 363,329" '
            'fill="none" stroke="#ff2222" stroke-width="4">'
            '<animate attributeName="opacity" values="0.4;1;0.4" dur="0.5s" repeatCount="indefinite"/>'
            "</polygon>"
        )
    sel_ring = (
        '<polygon points="400,302 443,325 443,375 400,398 357,375 357,325" '
        'fill="none" stroke="white" stroke-width="2" opacity="0.6"/>'
        if selected
        else ""
    )
    bonus_label = (
        f'<text x="400" y="300" font-family="Space Mono,monospace" font-size="8" '
        f'fill="#00ff9d" text-anchor="middle">{bonus}</text>'
        if bonus
        else ""
    )
    return f"""
    <!-- ── REACTOR CORE ── -->
    <g id="reactor">
      <!-- shadow -->
      <polygon points="400,314 438,335 438,377 400,398 362,377 362,335"
               fill="#010108" opacity="0.7"/>
      <!-- outer hull -->
      <polygon points="400,308 437,329 437,371 400,392 363,371 363,329"
               fill="#080818" stroke="{c}" stroke-width="1.8"/>
      <!-- inner ring -->
      <polygon points="400,320 430,336 430,364 400,380 370,364 370,336"
               fill="none" stroke="{c}" stroke-width="0.7" opacity="0.45"/>
      <!-- energy core outer glow -->
      <circle cx="400" cy="350" r="26" fill="{c}" opacity="0.12">{core_anim}</circle>
      <!-- energy core inner -->
      <circle cx="400" cy="350" r="17" fill="{c}" opacity="0.35">{pulse_anim}</circle>
      <!-- energy core bright -->
      <circle cx="400" cy="350" r="9" fill="{c}" opacity="0.85"/>
      <circle cx="400" cy="350" r="5" fill="white" opacity="0.9"/>
      <!-- cooling pipes -->
      <line x1="363" y1="350" x2="328" y2="350" stroke="{c}" stroke-width="2.5"
            stroke-dasharray="4,3" opacity="0.7"/>
      <line x1="437" y1="350" x2="472" y2="350" stroke="{c}" stroke-width="2.5"
            stroke-dasharray="4,3" opacity="0.7"/>
      <line x1="400" y1="308" x2="400" y2="278" stroke="{c}" stroke-width="2.5"
            stroke-dasharray="4,3" opacity="0.7"/>
      <!-- heat exchangers -->
      <rect x="314" y="342" width="14" height="16" rx="2" fill="#080818" stroke="{c}" stroke-width="0.7"/>
      <rect x="472" y="342" width="14" height="16" rx="2" fill="#080818" stroke="{c}" stroke-width="0.7"/>
      <rect x="393" y="264" width="14" height="14" rx="2" fill="#080818" stroke="{c}" stroke-width="0.7"/>
      <!-- status blink -->
      <circle cx="422" cy="315" r="3.5" fill="{c}">
        <animate attributeName="opacity" values="0.4;1;0.4" dur="2.1s" repeatCount="indefinite"/>
      </circle>
      {crisis_ring}{sel_ring}
      <!-- label -->
      <text x="400" y="305" font-family="Space Mono,monospace" font-size="9"
            fill="{c}" text-anchor="middle" opacity="0.85">REACTOR CORE</text>
      {bonus_label}
    </g>"""


def _resource_tunnels(state: WorldState) -> str:
    oxy = state.resources.get("oxygen", 100)
    food = state.resources.get("food", 100)
    energy = state.resources.get("energy", 100)

    def flow_color(val: float) -> str:
        if val > 60:
            return "#00cc88"
        elif val > 25:
            return "#ffd700"
        else:
            return "#ff4444"

    ec = flow_color(energy)
    oc = flow_color(oxy)
    fc = flow_color(food)
    return f"""
    <!-- ── RESOURCE FLOW TUNNELS ── -->
    <!-- Reactor → Habitat (energy) -->
    <path d="M 391 278 Q 370 255 359 242" stroke="{ec}" stroke-width="2.5" fill="none"
          stroke-dasharray="7,5" opacity="0.5">
      <animate attributeName="stroke-dashoffset" from="0" to="-24" dur="0.8s" repeatCount="indefinite"/>
    </path>
    <!-- Reactor → Greenhouse (energy) -->
    <path d="M 409 278 Q 440 255 487 250" stroke="{ec}" stroke-width="2.5" fill="none"
          stroke-dasharray="7,5" opacity="0.5">
      <animate attributeName="stroke-dashoffset" from="0" to="-24" dur="0.8s" repeatCount="indefinite"/>
    </path>
    <!-- Greenhouse → Colony center (food) -->
    <path d="M 492 264 Q 460 285 440 290" stroke="{fc}" stroke-width="2" fill="none"
          stroke-dasharray="5,5" opacity="0.35">
      <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="1.1s" repeatCount="indefinite"/>
    </path>
    <!-- Habitat → Colony center (oxygen) -->
    <path d="M 391 236 Q 380 250 380 265" stroke="{oc}" stroke-width="2" fill="none"
          stroke-dasharray="5,5" opacity="0.35">
      <animate attributeName="stroke-dashoffset" from="0" to="-20" dur="1.1s" repeatCount="indefinite"/>
    </path>"""


def _colonist_tokens(state: WorldState, selected_id: str | None) -> str:
    from ui.portraits import HAIR_COLORS, JOB_COLORS, SKIN_TONES

    job_positions: dict[str, list[tuple[int, int]]] = {
        k: list(v) for k, v in _JOB_POSITIONS.items()
    }
    out = []
    fallback_idx = 0

    for c in state.population:
        pos_list = job_positions.get(c.job, [])
        if pos_list:
            cx, cy = pos_list.pop(0)
        elif fallback_idx < len(_FALLBACK_POS):
            cx, cy = _FALLBACK_POS[fallback_idx]
            fallback_idx += 1
        else:
            continue

        if not c.alive:
            out.append(
                f'<g transform="translate({cx},{cy})" opacity="0.3" style="filter:saturate(0.08)">'
                f'<circle r="12" fill="#111" stroke="#333" stroke-width="1"/>'
                f'<text y="4" font-family="Space Mono,monospace" font-size="9" '
                f'text-anchor="middle" fill="#555">✝</text>'
                f'<text y="22" font-family="Space Mono,monospace" font-size="6" '
                f'text-anchor="middle" fill="#444">{c.name[:5].upper()}</text>'
                f"</g>"
            )
            continue

        seed = abs(hash(c.id))
        bg, accent, job_abbr = JOB_COLORS.get(c.job, ("#0a0a1a", "#00ff9d", "COL"))
        skin = SKIN_TONES[seed % len(SKIN_TONES)]
        hair = HAIR_COLORS[(seed >> 4) % len(HAIR_COLORS)]

        health_c = (
            "#00ff9d" if c.health > 60 else "#ffd700" if c.health > 30 else "#ff4444"
        )
        sel = c.id == selected_id

        anim_dur = round(2.8 + (seed % 28) / 10.0, 1)
        dx = round(-3.0 + (seed % 7) * 0.85, 1)
        dy = round(-2.5 + (seed % 6) * 0.85, 1)

        glow = ""
        if sel:
            glow = (
                '<circle r="22" fill="none" stroke="white" stroke-width="2" opacity="0.35">'
                '<animate attributeName="r" values="20;26;20" dur="1.2s" repeatCount="indefinite"/>'
                '<animate attributeName="opacity" values="0.25;0.7;0.25" dur="1.2s" repeatCount="indefinite"/>'
                "</circle>"
            )

        traits_csv = ",".join(c.traits)
        alive_flag = "1" if c.alive else "0"
        out.append(
            # outer group: click + hover handlers, data attributes for tooltip
            f'<g data-cid="{c.id}" '
            f'data-name="{c.name}" data-job="{c.job}" data-age="{c.age}" '
            f'data-health="{c.health:.1f}" data-morale="{c.morale:.1f}" '
            f'data-traits="{traits_csv}" data-accent="{accent}" '
            f'data-alive="{alive_flag}" '
            f"onclick=\"window.aubeSelectColonist('{c.id}')\" "
            f'onmouseenter="if(window.aubeMapEnter)window.aubeMapEnter(this)" '
            f'onmouseleave="if(window.aubeMapLeave)window.aubeMapLeave(this)" '
            f'style="cursor:pointer">'
            # zoom target: translate group with coords stored as data attrs for JS zoom
            f'<g transform="translate({cx},{cy})" data-tx="{cx}" data-ty="{cy}">'
            # animation group
            f"<g>"
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0,0;{dx},{dy};0,0;{-dx},{-dy};0,0" '
            f'dur="{anim_dur}s" repeatCount="indefinite"/>'
            f"{glow}"
            # health ring
            f'<circle r="18" fill="none" stroke="{health_c}" stroke-width="2.5" opacity="0.55"/>'
            # job bg circle
            f'<circle r="13" fill="{bg}" stroke="{accent}" stroke-width="1.5"/>'
            # hair
            f'<ellipse cx="0" cy="-9" rx="9" ry="6" fill="{hair}"/>'
            # face
            f'<circle cx="0" cy="-3" r="8" fill="{skin}"/>'
            # eyes
            f'<circle cx="-2.8" cy="-4.5" r="1.2" fill="#111"/>'
            f'<circle cx="2.8" cy="-4.5" r="1.2" fill="#111"/>'
            # suit collar
            f'<rect x="-5" y="5" width="10" height="8" rx="2" fill="{bg}" opacity="0.8"/>'
            # name label
            f'<rect x="-17" y="16" width="34" height="10" rx="2" fill="#000" opacity="0.8"/>'
            f'<text y="24" font-family="Space Mono,monospace" font-size="6.5" '
            f'text-anchor="middle" fill="{accent}" font-weight="bold">{c.name[:5].upper()}</text>'
            # job badge top-right
            f'<rect x="5" y="-24" width="16" height="8" rx="2" fill="{accent}" opacity="0.95"/>'
            f'<text x="13" y="-18" font-family="Space Mono,monospace" font-size="5.5" '
            f'text-anchor="middle" fill="black" font-weight="bold">{job_abbr}</text>'
            # tooltip (native SVG, also visible as browser tooltip)
            f"<title>{c.name} · {c.job.upper()} · HP:{c.health:.0f}% · MRL:{c.morale:.0f}%</title>"
            f"</g>"  # animation group
            f"</g>"  # translate / zoom-target group
            f"</g>"  # click group
        )
    return "".join(out)


def render_map(state: WorldState, selected_colonist_id: str | None = None) -> str:
    # locate buildings by name
    buildings: dict[str, object] = {b.name: b for b in state.buildings}
    hab = buildings.get("Habitat")
    ghse = buildings.get("Greenhouse")
    reac = buildings.get("Reactor")

    oxy = state.resources.get("oxygen", 100)
    ring_color = "#00ff9d" if oxy > 40 else "#ff6b35" if oxy > 15 else "#ff2222"
    ring_stroke = max(1, int(oxy / 22))

    optimism_glow = ""
    if state.optimism_active:
        optimism_glow = (
            '<circle cx="400" cy="305" r="245" fill="none" stroke="#ffe066" stroke-width="2.5" opacity="0.3">'
            '<animate attributeName="opacity" values="0.1;0.45;0.1" dur="2s" repeatCount="indefinite"/>'
            "</circle>"
            '<circle cx="400" cy="305" r="252" fill="none" stroke="#ffe066" stroke-width="1" opacity="0.2">'
            '<animate attributeName="opacity" values="0.05;0.2;0.05" dur="2.5s" repeatCount="indefinite"/>'
            "</circle>"
        )

    bt_count = len(state.breakthroughs)
    bt_label = (
        f"⚡ {bt_count} BREAKTHROUGH{'S' if bt_count != 1 else ''}" if bt_count else ""
    )

    hab_svg = _habitat_svg(hab)
    ghse_svg = _greenhouse_svg(ghse)
    reac_svg = _reactor_svg(reac)
    tunnels = _resource_tunnels(state)
    tokens = _colonist_tokens(state, selected_colonist_id)

    return f"""<svg viewBox="80 20 650 510" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;min-height:420px;border-radius:10px;display:block">
  <defs>
    <radialGradient id="space-bg" cx="50%" cy="40%" r="70%">
      <stop offset="0%" stop-color="#05091a"/>
      <stop offset="100%" stop-color="#010409"/>
    </radialGradient>
    <radialGradient id="dome-fill" cx="50%" cy="20%" r="80%">
      <stop offset="0%" stop-color="#001a10" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#000508" stop-opacity="0.15"/>
    </radialGradient>
    <linearGradient id="surface-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1a1008"/>
      <stop offset="100%" stop-color="#0a0804"/>
    </linearGradient>
    <filter id="glow-soft">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <!-- ── SPACE BACKGROUND ── -->
  <rect width="800" height="560" fill="url(#space-bg)"/>

  <!-- ── STARS ── -->
  {_get_stars()}

  <!-- ── DISTANT MOUNTAINS (planet horizon silhouette) ── -->
  <polygon points="0,450 60,415 120,435 200,400 280,425 360,408 440,420 520,402
                   600,418 680,405 760,422 800,410 800,460 0,460"
           fill="#0e0b08" opacity="0.8"/>
  <polygon points="0,455 40,430 110,448 190,420 270,440 350,425 430,437
                   510,418 590,432 670,415 750,428 800,418 800,465 0,465"
           fill="#0d0a07" opacity="0.6"/>

  <!-- ── PLANET SURFACE ── -->
  <rect x="0" y="455" width="800" height="105" fill="url(#surface-grad)"/>
  <rect x="0" y="455" width="800" height="3" fill="#2a1a10" opacity="0.5"/>
  <!-- surface texture streaks -->
  <line x1="50"  y1="470" x2="150" y2="473" stroke="#2a1a10" stroke-width="1" opacity="0.3"/>
  <line x1="200" y1="480" x2="340" y2="476" stroke="#2a1a10" stroke-width="1" opacity="0.25"/>
  <line x1="450" y1="465" x2="600" y2="469" stroke="#2a1a10" stroke-width="1" opacity="0.3"/>
  <line x1="620" y1="488" x2="780" y2="482" stroke="#2a1a10" stroke-width="1" opacity="0.2"/>
  <!-- surface rocks -->
  <ellipse cx="95"  cy="462" rx="18" ry="6" fill="#1a1008"/>
  <ellipse cx="340" cy="468" rx="12" ry="4" fill="#1a1008"/>
  <ellipse cx="580" cy="460" rx="20" ry="7" fill="#1a1008"/>
  <ellipse cx="720" cy="472" rx="14" ry="5" fill="#1a1008"/>

  <!-- ── COLONY DOME (outer ring) ── -->
  <circle cx="400" cy="305" r="235" fill="url(#dome-fill)"/>
  <circle cx="400" cy="305" r="{235 - ring_stroke // 2}" fill="none"
          stroke="{ring_color}" stroke-width="{ring_stroke}" opacity="0.15">
    <animate attributeName="opacity" values="0.06;0.22;0.06" dur="3s" repeatCount="indefinite"/>
  </circle>
  <circle cx="400" cy="305" r="235" fill="none"
          stroke="{ring_color}" stroke-width="2" opacity="0.4"/>
  <!-- dome glass highlight arc -->
  <path d="M 220 200 A 200 200 0 0 1 580 200" fill="none"
        stroke="white" stroke-width="1.2" opacity="0.06"/>
  <path d="M 240 185 A 180 180 0 0 1 560 185" fill="none"
        stroke="white" stroke-width="0.8" opacity="0.04"/>

  {optimism_glow}

  <!-- ── RESOURCE FLOW TUNNELS ── -->
  {tunnels}

  <!-- ── BUILDINGS ── -->
  {hab_svg}
  {ghse_svg}
  {reac_svg}

  <!-- ── COLONIST TOKENS ── -->
  {tokens}

  <!-- ── STATUS HEADER ── -->
  <rect x="0" y="0" width="800" height="22" fill="#010409" opacity="0.75"/>
  <text x="10" y="14" fill="#2a3a50" font-family="Space Mono,monospace" font-size="8.5">
    AUBE NOVA · YEAR {state.year:.2f} · POP {len(state.living)}/{len(state.population)}
    {" · CRISIS: " + state.crisis_active.upper() if state.crisis_active else ""}
  </text>
  <text x="790" y="14" fill="#00ff9d" font-family="Space Mono,monospace"
        font-size="8.5" text-anchor="end">{bt_label}</text>

  <!-- ── DOME LABEL ── -->
  <text x="400" y="542" font-family="Space Mono,monospace" font-size="8"
        fill="#1a2a3a" text-anchor="middle" opacity="0.7">
    COLONY AUBE NOVA · {state.year:.0f} YEARS ESTABLISHED
  </text>
</svg>"""
