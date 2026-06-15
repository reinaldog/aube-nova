"""
HUD renderer — resource bars, cultural profile, and colonist profile panel.
"""

from __future__ import annotations

from simulation.colonist import Colonist
from simulation.world import WorldState
from ui.portraits import JOB_COLORS, render_portrait

ICONS = {"oxygen": "🫧", "food": "🌱", "energy": "⚡", "credits": "💳"}


def render_hud(state: WorldState) -> str:
    # ── resource bars ──────────────────────────────────────────────────────────
    bars = ""
    for res, val in state.resources.items():
        pct = min(100.0, max(0.0, val))
        if pct > 60:
            color = "#00cc88"
        elif pct > 25:
            color = "#ffd700"
        elif pct > 10:
            color = "#ff8844"
        else:
            color = "#ff3333"
        icon = ICONS.get(res, "")
        pulse = (
            f'<animate attributeName="opacity" values="0.6;1;0.6" dur="0.6s" repeatCount="indefinite"/>'
            if pct < 10
            else ""
        )
        bars += f"""
        <div style="margin:9px 0">
          <div style="display:flex;justify-content:space-between;
                      font-family:'Space Mono',monospace;font-size:10px;
                      color:#8ab4c8;margin-bottom:4px">
            <span>{icon} {res.upper()}</span>
            <span style="color:{color};font-weight:700">{val:.0f}%</span>
          </div>
          <div style="background:#101620;border-radius:3px;height:6px;overflow:hidden">
            <div style="width:{pct}%;height:6px;background:{color};
                        border-radius:3px;transition:width 0.5s ease;
                        box-shadow:0 0 8px {color}66"></div>
          </div>
        </div>"""

    # ── cultural profile ───────────────────────────────────────────────────────
    profile = state.get_cultural_profile()
    profile_html = ""
    if profile:
        profile_html = (
            '<div style="margin-top:14px;border-top:1px solid #1a2030;padding-top:12px">'
            "<div style=\"font-family:'Space Mono',monospace;font-size:8px;color:#8ab4c8;"
            'letter-spacing:2px;margin-bottom:8px">CULTURAL DNA</div>'
        )
        colors = ["#4488ff", "#cc44ff", "#ff8844", "#44cc66", "#ff4466", "#ffe066"]
        max_freq = max(profile.values())
        for i, (trait, freq) in enumerate(profile.items()):
            actual_pct = int(freq * 100)
            # Normalize bar width relative to the most common trait so differences are visible
            bar_w = int((freq / max_freq) * 100) if max_freq > 0 else 0
            bc = colors[i % len(colors)]
            profile_html += f"""
            <div style="margin:4px 0">
              <div style="display:flex;justify-content:space-between;
                          font-family:'Space Mono',monospace;font-size:8px;color:#aac8d8;
                                                    margin-bottom:2px">
                <span>{trait}</span><span>{actual_pct}%</span>
              </div>
              <div style="background:#0c1018;border-radius:1px;height:3px">
                <div style="width:{bar_w}%;height:3px;background:{bc};border-radius:1px;
                            box-shadow:0 0 6px {bc}55"></div>
              </div>
            </div>"""
        profile_html += "</div>"

    # ── optimism banner ────────────────────────────────────────────────────────
    optimism_banner = ""
    if state.optimism_active:
        remaining = getattr(state, "_optimism_ticks_remaining", 0)
        optimism_banner = f"""
        <div style="background:#ffe06618;border:1px solid #ffe066;border-radius:5px;
                    padding:7px 10px;margin-bottom:10px;font-family:'Space Mono',monospace;
                    font-size:9px;color:#ffe066;letter-spacing:1px">
            💡 BREAKTHROUGH ACTIVE · {remaining} weeks remaining
        </div>"""

    # ── breakthroughs summary ──────────────────────────────────────────────────
    bt_html = ""
    if state.breakthroughs:
        bt_html = (
            '<div style="margin-top:12px;border-top:1px solid #1a2030;padding-top:10px">'
            "<div style=\"font-family:'Space Mono',monospace;font-size:8px;color:#8ab4c8;"
            'letter-spacing:2px;margin-bottom:6px">DISCOVERIES</div>'
        )
        for bt in state.breakthroughs:
            bt_html += (
                f"<div style=\"font-family:'Space Mono',monospace;font-size:8px;"
                f"color:#ffe066;margin:3px 0;padding:4px 6px;background:#1a1500;"
                f'border-left:2px solid #ffe066;border-radius:2px">'
                f"⚡ {bt.title}</div>"
            )
        bt_html += "</div>"

    return (
        f'<div style="padding:14px;background:#080d18;border-radius:8px;'
        f'border:1px solid #1a2030;height:100%">'
        f"<div style=\"font-family:'Space Mono',monospace;font-size:8px;color:#8ab4c8;"
        f'letter-spacing:2px;margin-bottom:10px">COLONY STATUS</div>'
        f"{optimism_banner}{bars}{profile_html}{bt_html}"
        f"</div>"
    )


def render_colonist_profile(
    colonist: Colonist | None,
    cultural_profile: dict | None = None,
) -> str:
    """Full profile panel shown in the right column when a colonist is selected."""
    if colonist is None:
        return ""

    _, accent, _ = JOB_COLORS.get(colonist.job, ("#0a0a1a", "#00ff9d", "COL"))
    portrait_large = render_portrait(colonist, selected=True)

    # health / morale bars
    hpct = max(0, min(100, colonist.health))
    mpct = max(0, min(100, colonist.morale))
    hc = "#00cc88" if hpct > 60 else "#ffd700" if hpct > 30 else "#ff4444"
    mc = "#cc44ff" if mpct > 60 else "#ffd700" if mpct > 30 else "#ff8844"

    def mini_bar(val: float, color: str) -> str:
        return (
            f'<div style="background:#101620;border-radius:2px;height:5px;margin-top:3px">'
            f'<div style="width:{val:.0f}%;height:5px;background:{color};border-radius:2px;'
            f'box-shadow:0 0 6px {color}66"></div>'
            f"</div>"
        )

    # Trait badges
    trait_badges = ""
    trait_colors = {
        "cooperative": "#4488ff",
        "scientific": "#00ccff",
        "risk-averse": "#44cc66",
        "resourceful": "#88ff44",
        "stubborn": "#ff8844",
        "empathetic": "#ff66aa",
        "ambitious": "#cc44ff",
        "pragmatic": "#ffcc44",
        "rebellious": "#ff4444",
        "loyal": "#44aaff",
        "inventive": "#00ff9d",
        "fearful": "#ff6633",
        "optimistic": "#ffe066",
    }
    for trait in colonist.traits:
        tc = trait_colors.get(trait, "#667788")
        trait_badges += (
            f'<span style="display:inline-block;padding:2px 7px;margin:2px;'
            f"font-family:'Space Mono',monospace;font-size:8px;color:{tc};"
            f'background:{tc}22;border:1px solid {tc}44;border-radius:10px">'
            f"{trait}</span>"
        )

    # Memories
    mem_html = ""
    if colonist.memory:
        mem_html = (
            '<div style="margin-top:10px">'
            "<div style=\"font-family:'Space Mono',monospace;font-size:8px;"
            'color:#8ab4c8;letter-spacing:1px;margin-bottom:5px">MEMORIES</div>'
        )
        for m in colonist.memory[:4]:
            mem_html += (
                f"<div style=\"font-family:'Space Mono',monospace;font-size:8px;"
                f'color:#8aacbc;margin:2px 0;padding:3px 6px;border-left:1px solid #1a2a3a">• {m}</div>'
            )
        mem_html += "</div>"

    # Notable actions
    na_html = ""
    if colonist.notable_actions:
        na_html = (
            '<div style="margin-top:10px">'
            "<div style=\"font-family:'Space Mono',monospace;font-size:8px;"
            'color:#8ab4c8;letter-spacing:1px;margin-bottom:5px">NOTABLE ACTIONS</div>'
        )
        for na in colonist.notable_actions[:4]:
            na_html += (
                f"<div style=\"font-family:'Space Mono',monospace;font-size:8px;"
                f"color:#ffe088;margin:2px 0;padding:3px 6px;"
                f'border-left:2px solid #ffe06644">★ {na}</div>'
            )
        na_html += "</div>"

    gen_label = (
        "ORIGINAL SETTLER"
        if colonist.generation == 0
        else f"GENERATION {colonist.generation}"
    )
    status_label = "DECEASED" if not colonist.alive else "ACTIVE"
    status_color = "#ff4444" if not colonist.alive else "#00cc88"

    # Cultural DNA section — colony-wide bars with this colonist's traits highlighted
    dna_html = ""
    if cultural_profile:
        dna_colors = ["#4488ff", "#cc44ff", "#ff8844", "#44cc66", "#ff4466", "#ffe066"]
        dna_rows = ""
        max_dna_freq = max(cultural_profile.values()) if cultural_profile else 1.0
        for i, (trait, freq) in enumerate(cultural_profile.items()):
            actual_pct = int(freq * 100)
            w = int((freq / max_dna_freq) * 100) if max_dna_freq > 0 else 0
            bc = dna_colors[i % len(dna_colors)]
            has_trait = trait in colonist.traits
            label_style = (
                f"color:{bc};font-weight:700" if has_trait else "color:#7a9ab0"
            )
            bar_style = (
                f"background:{bc};box-shadow:0 0 6px {bc}88"
                if has_trait
                else f"background:{bc}44"
            )
            marker = " ◄" if has_trait else ""
            dna_rows += (
                f'<div style="margin:4px 0">'
                f'<div style="display:flex;justify-content:space-between;'
                f"font-family:'Space Mono',monospace;font-size:8px;{label_style};"
                f'margin-bottom:2px">'
                f"<span>{trait}{marker}</span><span>{actual_pct}%</span>"
                f"</div>"
                f'<div style="background:#0c1018;border-radius:1px;height:3px">'
                f'<div style="width:{w}%;height:3px;{bar_style};border-radius:1px"></div>'
                f"</div>"
                f"</div>"
            )
        dna_html = (
            '<div style="margin-top:12px;border-top:1px solid #1a2030;padding-top:10px">'
            "<div style=\"font-family:'Space Mono',monospace;font-size:8px;color:#8ab4c8;"
            'letter-spacing:2px;margin-bottom:8px">COLONY CULTURAL DNA</div>'
            f"<div style=\"font-family:'Space Mono',monospace;font-size:7px;color:#6a8a9a;"
            f'margin-bottom:6px;letter-spacing:0.5px">'
            f"&#9668; = this colonist's traits</div>" + dna_rows + "</div>"
        )

    return (
        f'<div style="padding:14px;background:#080d18;border-radius:8px;'
        f'border:1px solid #1a2030;overflow-y:auto;max-height:520px">'
        # header row
        f'<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:12px">'
        f'<div style="flex-shrink:0">{portrait_large}</div>'
        f'<div style="flex:1">'
        f"<div style=\"font-family:'Space Mono',monospace;font-size:15px;"
        f'font-weight:700;color:{accent};margin-bottom:4px">{colonist.name}</div>'
        f"<div style=\"font-family:'Space Mono',monospace;font-size:8px;"
        f'color:#7a9ab8;margin-bottom:2px">{colonist.job.upper()} · AGE {colonist.age}</div>'
        f"<div style=\"font-family:'Space Mono',monospace;font-size:8px;"
        f'color:#6a8a9a;margin-bottom:8px">{gen_label} · '
        f'<span style="color:{status_color}">{status_label}</span></div>'
        # health bar
        f"<div style=\"font-family:'Space Mono',monospace;font-size:7px;color:#8ab4c8;"
        f'display:flex;justify-content:space-between">HEALTH<span style="color:{hc}">{hpct:.0f}%</span></div>'
        f"{mini_bar(hpct, hc)}"
        # morale bar
        f"<div style=\"font-family:'Space Mono',monospace;font-size:7px;color:#8ab4c8;"
        f'display:flex;justify-content:space-between;margin-top:6px">MORALE<span style="color:{mc}">{mpct:.0f}%</span></div>'
        f"{mini_bar(mpct, mc)}"
        f"</div>"  # close info div
        f"</div>"  # close header row
        # traits
        f'<div style="margin-bottom:8px">{trait_badges}</div>'
        f"{mem_html}{na_html}{dna_html}"
        f"</div>"
    )


def render_llm_stats() -> str:
    """Panel showing live LLM / model usage statistics."""
    from llm.stats import get_stats

    s = get_stats()

    # Status indicator
    if not s.has_token:
        status_color = "#ff4444"
        status_text = "NO TOKEN"
        status_dot = "#ff4444"
    elif s.error_calls > 0 and s.successful_calls == 0:
        status_color = "#ff8844"
        status_text = "ERRORS"
        status_dot = "#ff8844"
    elif s.successful_calls > 0:
        status_color = "#00cc88"
        status_text = "LIVE"
        status_dot = "#00cc88"
    else:
        status_color = "#ffd700"
        status_text = "STANDBY"
        status_dot = "#ffd700"

    def stat_row(label: str, value: str, color: str = "#8ab4c8") -> str:
        return (
            f'<div style="display:flex;justify-content:space-between;'
            f"font-family:'Space Mono',monospace;font-size:9px;"
            f'margin:5px 0;align-items:center">'
            f'<span style="color:#7a9ab0;letter-spacing:0.5px">{label}</span>'
            f'<span style="color:{color};font-weight:700">{value}</span>'
            f"</div>"
        )

    def mini_divider() -> str:
        return '<div style="border-top:1px solid #0d1620;margin:8px 0"></div>'

    success_rate = f"{s.success_rate_pct:.0f}%" if s.total_calls > 0 else "\u2014"
    avg_lat = f"{s.avg_latency_ms:.0f} ms" if s.avg_latency_ms > 0 else "\u2014"
    last_lat = f"{s.last_latency_ms:.0f} ms" if s.last_latency_ms > 0 else "\u2014"
    total_tok = f"{s.total_tokens:,}" if s.total_tokens > 0 else "0"
    prompt_tok = f"{s.total_prompt_tokens:,}" if s.total_prompt_tokens > 0 else "0"
    compl_tok = (
        f"{s.total_completion_tokens:,}" if s.total_completion_tokens > 0 else "0"
    )
    uptime = f"{s.session_minutes:.1f} min"

    fallback_color = "#ff8844" if s.fallback_calls > 0 else "#445566"

    return (
        f'<div style="padding:14px;background:#080d18;border-radius:8px;'
        f'border:1px solid #1a2030">'
        # header row
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">'
        f"<div style=\"font-family:'Space Mono',monospace;font-size:8px;color:#7a9ab0;"
        f'letter-spacing:2px">MODEL STATUS</div>'
        f'<div style="display:flex;align-items:center;gap:6px">'
        f'<div style="width:7px;height:7px;border-radius:50%;background:{status_dot};'
        f'box-shadow:0 0 8px {status_dot}88">'
        f'<animate xmlns="http://www.w3.org/1999/xhtml" attributeName="opacity" '
        f'values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/>'
        f"</div>"
        f"<span style=\"font-family:'Space Mono',monospace;font-size:8px;"
        f'color:{status_color};font-weight:700;letter-spacing:1px">{status_text}</span>'
        f"</div>"
        f"</div>"
        # model badge
        f'<div style="background:#0c1420;border:1px solid #1a3050;border-radius:5px;'
        f'padding:8px 10px;margin-bottom:10px">'
        f"<div style=\"font-family:'Space Mono',monospace;font-size:10px;"
        f'color:#4488ff;font-weight:700;letter-spacing:0.5px">{s.model_short}</div>'
        f"<div style=\"font-family:'Space Mono',monospace;font-size:7px;"
        f'color:#5a7a9a;margin-top:2px;letter-spacing:0.5px">{s.provider}</div>'
        f"</div>"
        # call stats
        + stat_row("TOTAL CALLS", str(s.total_calls))
        + stat_row("\u2713 SUCCESSFUL", str(s.successful_calls), "#00cc88")
        + stat_row("\u26a0 FALLBACK", str(s.fallback_calls), fallback_color)
        + stat_row(
            "\u2717 ERRORS",
            str(s.error_calls),
            "#ff4444" if s.error_calls > 0 else "#445566",
        )
        + stat_row(
            "SUCCESS RATE",
            success_rate,
            "#00cc88" if s.success_rate_pct > 70 else "#ffd700",
        )
        + mini_divider()
        # token stats
        + f"<div style=\"font-family:'Space Mono',monospace;font-size:8px;color:#7a9ab0;"
        + f'letter-spacing:2px;margin-bottom:6px">TOKEN USAGE</div>'
        + stat_row("TOTAL", total_tok, "#cc44ff")
        + stat_row("\u21b3 PROMPT", prompt_tok, "#8866cc")
        + stat_row("\u21b3 COMPLETION", compl_tok, "#aa55ee")
        + mini_divider()
        # latency
        + stat_row("LAST LATENCY", last_lat, "#4488ff")
        + stat_row("AVG LATENCY", avg_lat, "#4488ff")
        + mini_divider()
        + stat_row("SESSION", uptime, "#667788")
        + f"</div>"
    )
