"""
Chronicle renderer — newspaper-style entries for The Aube Chronicle.

Annual dispatches render as a full broadsheet front page (paper background,
masthead, two-column layout).  Milestone entries (death, birth, breakthrough,
peaceful-year) are compact cards with a coloured left border.
"""

from __future__ import annotations

# ── Milestone type metadata ────────────────────────────────────────────────────
# (card_bg, accent_colour, badge_label)
_MILESTONE_META: dict[str, tuple[str, str, str]] = {
    "death": ("#1a0808", "#ff6688", "OBITUARY"),
    "birth": ("#081a10", "#44ff88", "BIRTH RECORD"),
    "breakthrough": ("#1a1500", "#ffe066", "DISCOVERY"),
    "first_year_no_crisis": ("#0a1020", "#4488ff", "MILESTONE"),
}


def _audio_tag(audio_path: str | None) -> str:
    if not audio_path:
        return ""
    return (
        f'<audio controls style="width:100%;margin-top:12px;height:28px;'
        f'border-radius:4px;filter:invert(0.85) hue-rotate(180deg)"'
        f' src="/file={audio_path}"></audio>'
    )


def _year_str(year_val) -> str:
    if isinstance(year_val, float):
        return f"{year_val:.2f}"
    return str(year_val)


# ── Annual entry: full broadsheet page ────────────────────────────────────────


def _render_annual(entry: dict) -> str:
    year = _year_str(entry.get("year", ""))
    hed = entry.get("headline", "\u2014")
    art1 = entry.get("article1", "")
    art2 = entry.get("article2", "")
    audio = _audio_tag(entry.get("audio_path"))

    col1 = (
        (
            f"<div style=\"font-family:'Source Serif 4',Georgia,serif;"
            f'font-size:12px;line-height:1.8;color:#1a1008">'
            f"{art1}"
            f"</div>"
        )
        if art1
        else ""
    )

    col2 = (
        (
            f"<div style=\"font-family:'Source Serif 4',Georgia,serif;"
            f"font-size:11px;line-height:1.75;color:#2a1810;font-style:italic;"
            f'border-left:3px solid #c9893d;padding-left:14px">'
            f"{art2}"
            f"</div>"
        )
        if art2
        else ""
    )

    two_cols = ""
    if col1 or col2:
        # if only one article exists, stretch it full width
        grid = "1fr 1fr" if (col1 and col2) else "1fr"
        two_cols = (
            f'<div style="display:grid;grid-template-columns:{grid};'
            f'gap:18px;margin-top:14px">'
            f"{col1}{col2}"
            f"</div>"
        )

    return f"""
<div style="background:#f5f0e8;color:#1a1410;padding:22px 26px 18px;
            border-radius:6px;margin:12px 0;
            box-shadow:0 6px 28px rgba(0,0,0,0.55),
                       inset 0 0 60px rgba(200,180,140,0.08);
            border:1px solid #d4c9b0">

  <!-- Masthead -->
  <div style="text-align:center;padding-bottom:10px;margin-bottom:10px;
              border-bottom:3px double #1a1410">
    <div style="font-family:'IM Fell English',Georgia,serif;
                font-size:26px;letter-spacing:1px;
                line-height:1.15">
      <span style="color:#0d0d0a !important;font-weight:900">The Aube Chronicle</span>
    </div>
    <div style="font-family:'Space Mono',monospace;font-size:7px;
                color:#5a4a3a !important;letter-spacing:3px;margin-top:5px;
                text-transform:uppercase">
      Humanity's First Record &nbsp;&middot;&nbsp; Colony Year {year}
    </div>
  </div>

  <!-- Headline -->
  <div style="font-family:'Playfair Display',Georgia,serif;
              font-size:21px;font-weight:900;line-height:1.2;
              color:#0d0d0a !important;text-align:center;
              padding-bottom:12px;margin-bottom:4px;
              border-bottom:1px solid #c9893d">
    {hed}
  </div>

  <!-- Body columns -->
  {two_cols}

  <!-- Optional audio -->
  {audio}

</div>"""


# ── Milestone entry: compact card ─────────────────────────────────────────────


def _render_milestone(entry: dict) -> str:
    etype = entry.get("type", "death")
    meta = _MILESTONE_META.get(etype, ("#0a1020", "#4488ff", "MILESTONE"))
    bg, accent, badge = meta

    year = _year_str(entry.get("year", ""))
    hed = entry.get("headline", "\u2014")
    art1 = entry.get("article1", "")
    audio = _audio_tag(entry.get("audio_path"))

    body = (
        (
            f"<div style=\"font-family:'Source Serif 4',Georgia,serif;"
            f"font-size:11px;line-height:1.65;color:{accent};"
            f'opacity:0.85;margin-top:8px">'
            f"{art1}"
            f"</div>"
        )
        if art1
        else ""
    )

    return f"""
<div style="background:{bg};padding:14px 18px;border-radius:5px;
            margin:7px 0;border-left:4px solid {accent};
            box-shadow:0 2px 12px rgba(0,0,0,0.35)">

  <!-- Badge + year -->
  <div style="font-family:'Space Mono',monospace;font-size:7px;
              letter-spacing:2.5px;text-transform:uppercase;
              color:{accent};opacity:0.8;margin-bottom:8px">
    {badge} &nbsp;&middot;&nbsp; Year {year}
  </div>

  <!-- Headline -->
  <div style="font-family:'Playfair Display',Georgia,serif;
              font-size:15px;font-weight:700;line-height:1.3;color:{accent}">
    {hed}
  </div>

  {body}
  {audio}

</div>"""


# ── Public API ─────────────────────────────────────────────────────────────────


def render_chronicle_entry(entry: dict) -> str:
    """Return the HTML for a single chronicle entry."""
    if not entry:
        return ""
    if entry.get("type", "annual") == "annual":
        return _render_annual(entry)
    return _render_milestone(entry)


def render_all_chronicles(entries: list) -> str:
    """Return a scrollable container with all chronicle entries, newest first."""
    if not entries:
        return (
            '<div style="height:560px;display:flex;align-items:center;'
            "justify-content:center;"
            "font-family:'Space Mono',monospace;font-size:10px;"
            'color:#1a3a4a;letter-spacing:2px;text-align:center">'
            "AWAITING FIRST YEAR END\u2026<br/>"
            '<span style="font-size:8px;opacity:0.5;margin-top:6px;display:block">'
            "52 WEEKS UNTIL FIRST DISPATCH"
            "</span>"
            "</div>"
        )

    html = "".join(render_chronicle_entry(e) for e in reversed(entries))

    return (
        '<div style="height:560px;overflow-y:auto;padding:6px 8px;'
        'scrollbar-width:thin;scrollbar-color:#1f2937 transparent">'
        f"{html}"
        "</div>"
    )
