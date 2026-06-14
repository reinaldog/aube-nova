"""
Procedural SVG portrait generator for Aube Nova colonists.
Each portrait is 60×80px, deterministic based on colonist.id.
"""

from __future__ import annotations

from simulation.colonist import Colonist

# (background, accent, abbreviation)
JOB_COLORS: dict[str, tuple[str, str, str]] = {
    "engineer": ("#0c1e3a", "#4488ff", "ENG"),
    "farmer": ("#0a2012", "#44cc66", "FRM"),
    "medic": ("#280a18", "#ff4466", "MED"),
    "researcher": ("#190a2c", "#cc44ff", "RES"),
    "miner": ("#281806", "#ff8844", "MIN"),
    "builder": ("#26200a", "#ffcc44", "BLD"),
}

SKIN_TONES = [
    "#FDBCB4",
    "#E8A87C",
    "#C68642",
    "#8D5524",
    "#4A2912",
    "#F1C27D",
    "#E0AC69",
]
SKIN_SHADOW = [
    "#C07040",
    "#A06020",
    "#885018",
    "#5A2808",
    "#1e0800",
    "#B07028",
    "#906028",
]
HAIR_COLORS = [
    "#1a0800",
    "#3b1a00",
    "#C8A96B",
    "#F5DEB3",
    "#8B0000",
    "#2a2a2a",
    "#A0522D",
]
EYE_COLORS = [
    "#3b82f6",
    "#22c55e",
    "#f59e0b",
    "#a855f7",
    "#06b6d4",
    "#84cc16",
    "#ef4444",
]


def render_portrait(colonist: Colonist, selected: bool = False) -> str:
    """Return a 60×80 inline SVG string for this colonist."""
    seed = abs(hash(colonist.id))

    bg, accent, job_abbr = JOB_COLORS.get(colonist.job, ("#0a0a1a", "#00ff9d", "COL"))
    skin = SKIN_TONES[seed % len(SKIN_TONES)]
    shadow = SKIN_SHADOW[seed % len(SKIN_SHADOW)]
    hair_color = HAIR_COLORS[(seed >> 4) % len(HAIR_COLORS)]
    eye_c = EYE_COLORS[(seed >> 8) % len(EYE_COLORS)]
    hair_style = (seed >> 12) % 4  # 0=short, 1=medium, 2=long, 3=curly

    # face geometry (centre, radius)
    fcx, fcy, fr = 30, 39, 15

    if hair_style == 0:  # short / buzz cut
        hair = (
            f'<ellipse cx="30" cy="{fcy - fr + 3}" rx="{fr + 1}" ry="{fr // 2 + 3}" '
            f'fill="{hair_color}"/>'
        )
    elif hair_style == 1:  # medium with sides
        hair = (
            f'<ellipse cx="30" cy="{fcy - fr + 2}" rx="{fr + 3}" ry="{fr // 2 + 5}" '
            f'fill="{hair_color}"/>'
            f'<rect x="{fcx - fr - 3}" y="{fcy - 7}" width="5" height="15" rx="2" fill="{hair_color}"/>'
            f'<rect x="{fcx + fr - 2}" y="{fcy - 7}" width="5" height="15" rx="2" fill="{hair_color}"/>'
        )
    elif hair_style == 2:  # long
        hair = (
            f'<ellipse cx="30" cy="{fcy - fr + 2}" rx="{fr + 3}" ry="{fr // 2 + 5}" '
            f'fill="{hair_color}"/>'
            f'<rect x="{fcx - fr - 3}" y="{fcy - 5}" width="5" height="26" rx="2" fill="{hair_color}"/>'
            f'<rect x="{fcx + fr - 2}" y="{fcy - 5}" width="5" height="26" rx="2" fill="{hair_color}"/>'
        )
    else:  # curly / afro
        hair = (
            f'<circle cx="{fcx - fr + 4}" cy="{fcy - fr + 2}" r="9" fill="{hair_color}"/>'
            f'<circle cx="{fcx}" cy="{fcy - fr - 3}" r="10" fill="{hair_color}"/>'
            f'<circle cx="{fcx + fr - 4}" cy="{fcy - fr + 2}" r="9" fill="{hair_color}"/>'
        )

    if colonist.morale > 65:
        mouth = (
            f'<path d="M{fcx - 6},{fcy + 9} Q{fcx},{fcy + 13} {fcx + 6},{fcy + 9}" '
            f'fill="none" stroke="{shadow}" stroke-width="1.5" stroke-linecap="round"/>'
        )
    elif colonist.morale > 35:
        mouth = (
            f'<line x1="{fcx - 5}" y1="{fcy + 11}" x2="{fcx + 5}" y2="{fcy + 11}" '
            f'stroke="{shadow}" stroke-width="1.5" stroke-linecap="round"/>'
        )
    else:
        mouth = (
            f'<path d="M{fcx - 6},{fcy + 12} Q{fcx},{fcy + 8} {fcx + 6},{fcy + 12}" '
            f'fill="none" stroke="{shadow}" stroke-width="1.5" stroke-linecap="round"/>'
        )

    health_c = (
        "#00ff9d"
        if colonist.health > 60
        else "#ffd700"
        if colonist.health > 30
        else "#ff4444"
    )
    border_c = "white" if selected else accent
    border_w = 2.5 if selected else 1.5
    # display:block eliminates the descender gap that inline SVGs create inside flex items
    if not colonist.alive:
        svg_style = 'style="display:block;opacity:0.35;filter:saturate(0.1)"'
    else:
        svg_style = 'style="display:block"'
    uid = colonist.id.replace(":", "_")

    return (
        f'<svg width="60" height="80" viewBox="0 0 60 80" '
        f'xmlns="http://www.w3.org/2000/svg" {svg_style}>'
        f"<defs>"
        f'<radialGradient id="pbg-{uid}" cx="40%" cy="25%" r="75%">'
        f'<stop offset="0%" stop-color="{bg}"/>'
        f'<stop offset="100%" stop-color="#030608"/>'
        f"</radialGradient>"
        f"</defs>"
        # background
        f'<rect width="60" height="80" fill="url(#pbg-{uid})" rx="4"/>'
        # suit body
        f'<ellipse cx="30" cy="85" rx="28" ry="15" fill="{bg}" stroke="{accent}" stroke-width="0.4"/>'
        f'<rect x="8" y="63" width="44" height="22" fill="{bg}" rx="3"/>'
        f'<line x1="30" y1="64" x2="30" y2="80" stroke="{accent}" stroke-width="0.5" opacity="0.3"/>'
        # neck
        f'<rect x="24" y="{fcy + fr - 1}" width="12" height="11" fill="{skin}" rx="2"/>'
        # hair (drawn first)
        f"{hair}"
        # face (redrawn on top of hair roots)
        f'<circle cx="30" cy="{fcy}" r="{fr}" fill="{skin}"/>'
        # eyes
        f'<circle cx="{fcx - 6}" cy="{fcy - 2}" r="3.5" fill="white"/>'
        f'<circle cx="{fcx + 6}" cy="{fcy - 2}" r="3.5" fill="white"/>'
        f'<circle cx="{fcx - 6}" cy="{fcy - 2}" r="2.1" fill="{eye_c}"/>'
        f'<circle cx="{fcx + 6}" cy="{fcy - 2}" r="2.1" fill="{eye_c}"/>'
        f'<circle cx="{fcx - 5}" cy="{fcy - 3}" r="0.7" fill="white" opacity="0.8"/>'
        f'<circle cx="{fcx + 7}" cy="{fcy - 3}" r="0.7" fill="white" opacity="0.8"/>'
        # eyebrows
        f'<path d="M{fcx - 10},{fcy - 7} Q{fcx - 6},{fcy - 11} {fcx - 2},{fcy - 7}" '
        f'fill="none" stroke="{hair_color}" stroke-width="1.4" stroke-linecap="round"/>'
        f'<path d="M{fcx + 2},{fcy - 7} Q{fcx + 6},{fcy - 11} {fcx + 10},{fcy - 7}" '
        f'fill="none" stroke="{hair_color}" stroke-width="1.4" stroke-linecap="round"/>'
        # nose
        f'<path d="M28,{fcy + 3} L26,{fcy + 8} Q30,{fcy + 10} 34,{fcy + 8} L32,{fcy + 3}" '
        f'fill="none" stroke="{shadow}" stroke-width="0.7"/>'
        # mouth
        f"{mouth}"
        # job badge
        f'<rect x="2" y="2" width="18" height="9" rx="2" fill="{accent}" opacity="0.9"/>'
        f'<text x="11" y="9" font-family="monospace" font-size="5.5" '
        f'text-anchor="middle" fill="black" font-weight="bold">{job_abbr}</text>'
        # name strip
        f'<rect x="0" y="68" width="60" height="12" fill="black" opacity="0.55"/>'
        f'<text x="30" y="77" font-family="monospace" font-size="6.5" '
        f'text-anchor="middle" fill="{accent}" font-weight="bold">'
        f"{colonist.name[:6].upper()}</text>"
        # border
        f'<rect width="60" height="80" fill="none" stroke="{border_c}" '
        f'stroke-width="{border_w}" rx="4" opacity="{0.95 if selected else 0.6}"/>'
        # health pulse
        f'<circle cx="54" cy="7" r="3.5" fill="{health_c}">'
        f'<animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/>'
        f"</circle>"
        f"</svg>"
    )


def render_roster(colonists: list[Colonist], selected_id: str | None = None) -> str:
    """Horizontal scrollable row of portrait cards."""
    js = """
<script>
if (!window._aubeRosterInit) {
  window._aubeRosterInit = true;

  window.aubeSelectColonist = function(cid) {
    var el = document.querySelector('#colonist-selector textarea');
    if (!el) el = document.querySelector('#colonist-selector input');
    if (el) {
      try {
        var setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value').set;
        setter.call(el, cid);
      } catch(e) { el.value = cid; }
      el.dispatchEvent(new Event('input', {bubbles: true}));
    }
  };

  window.aubeShowTip = function(e, card) {
    var tip = document.getElementById('aube-tip');
    if (!tip) {
      tip = document.createElement('div');
      tip.id = 'aube-tip';
      tip.style.cssText = [
        'position:fixed','z-index:99999','pointer-events:none',
        'background:#0a1322','border:1px solid #1e3a52',
        'border-radius:8px','padding:11px 13px',
        "font-family:'Space Mono',monospace",
        'min-width:190px','max-width:240px',
        'box-shadow:0 4px 20px rgba(0,0,0,0.7)',
        'display:none'
      ].join(';');
      document.body.appendChild(tip);
    }
    var d = card.dataset;
    var hp = parseFloat(d.health), mp = parseFloat(d.morale);
    var hc = hp > 60 ? '#00cc88' : hp > 30 ? '#ffd700' : '#ff4444';
    var mc = mp > 60 ? '#cc44ff' : mp > 30 ? '#ffd700' : '#ff8844';
    var traits = d.traits ? d.traits.split(',') : [];
    var tHTML = traits.map(function(t) {
      return '<span style="display:inline-block;padding:1px 6px;margin:1px 2px;font-size:7px;'
           + 'border-radius:9px;background:#0e1e2e;border:1px solid #1a3a4a;color:#5a9ab8">'
           + t + '</span>';
    }).join('');
    var aliveHTML = d.alive === '1'
      ? '<span style="color:#00cc88">ACTIVE</span>'
      : '<span style="color:#ff4444">DECEASED</span>';
    tip.innerHTML =
      '<div style="font-size:13px;font-weight:700;color:' + d.accent + ';margin-bottom:1px">' + d.name + '</div>' +
      '<div style="font-size:8px;color:#3a5a72;margin-bottom:7px">' + d.job.toUpperCase() + ' \u00b7 AGE ' + d.age + ' \u00b7 ' + aliveHTML + '</div>' +
      '<div style="font-size:7px;color:#2a4a5a;display:flex;justify-content:space-between;margin-bottom:2px">' +
        '<span>HEALTH</span><span style="color:' + hc + '">' + hp.toFixed(0) + '%</span>' +
      '</div>' +
      '<div style="background:#0c1620;border-radius:2px;height:4px;margin-bottom:5px">' +
        '<div style="width:' + hp + '%;height:4px;background:' + hc + ';border-radius:2px;box-shadow:0 0 5px ' + hc + '66"></div>' +
      '</div>' +
      '<div style="font-size:7px;color:#2a4a5a;display:flex;justify-content:space-between;margin-bottom:2px">' +
        '<span>MORALE</span><span style="color:' + mc + '">' + mp.toFixed(0) + '%</span>' +
      '</div>' +
      '<div style="background:#0c1620;border-radius:2px;height:4px;margin-bottom:8px">' +
        '<div style="width:' + mp + '%;height:4px;background:' + mc + ';border-radius:2px;box-shadow:0 0 5px ' + mc + '66"></div>' +
      '</div>' +
      '<div style="border-top:1px solid #0e1e2e;padding-top:7px">' + tHTML + '</div>';

    var rect = card.getBoundingClientRect();
    var left = rect.right + 10;
    var top  = rect.top;
    if (left + 250 > window.innerWidth)  left = rect.left - 250;
    if (top  + 200 > window.innerHeight) top  = window.innerHeight - 205;
    if (top < 4) top = 4;
    tip.style.left = left + 'px';
    tip.style.top  = top  + 'px';
    tip.style.display = 'block';
  };

  window.aubeHideTip = function() {
    var tip = document.getElementById('aube-tip');
    if (tip) tip.style.display = 'none';
  };
}
</script>
"""
    cards = ""
    for c in colonists:
        sel = c.id == selected_id
        _, accent, _ = JOB_COLORS.get(c.job, ("#0a0a1a", "#00ff9d", "COL"))
        glow = f"box-shadow:0 0 12px {accent}88;" if sel else ""
        dead_style = "opacity:0.4;" if not c.alive else ""
        portrait_svg = render_portrait(c, selected=sel)
        traits_csv = ",".join(c.traits)
        alive_flag = "1" if c.alive else "0"
        cards += (
            f"<div onclick=\"window.aubeSelectColonist('{c.id}')\" "
            f'onmouseover="window.aubeShowTip(event,this)" '
            f'onmouseout="window.aubeHideTip()" '
            f'data-name="{c.name}" '
            f'data-job="{c.job}" '
            f'data-age="{c.age}" '
            f'data-health="{c.health:.1f}" '
            f'data-morale="{c.morale:.1f}" '
            f'data-traits="{traits_csv}" '
            f'data-accent="{accent}" '
            f'data-alive="{alive_flag}" '
            f'style="cursor:pointer;flex-shrink:0;border-radius:6px;{dead_style}{glow}'
            f'transition:all 0.2s ease">'
            f"{portrait_svg}"
            f"</div>"
        )

    return (
        f"{js}"
        f'<div style="display:flex;gap:6px;overflow-x:auto;padding:10px 12px;'
        f"background:#060b14;border-radius:8px;border:1px solid #1a1f2e;"
        f'scrollbar-width:thin;scrollbar-color:#1f2937 transparent">'
        f"{cards}"
        f"</div>"
    )
