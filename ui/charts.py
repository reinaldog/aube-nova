"""
Analytics charts for Aube Nova using matplotlib.
All charts use the design tokens: dusk (#232B3D), paper (#EFE8D8), ochre (#C9893D),
rust (#A8503A), moss (#6E8C6A).
"""

import matplotlib

matplotlib.use("Agg")
from collections import Counter

import matplotlib.pyplot as plt

RESOURCE_COLORS = {
    "oxygen": "#6E8C6A",
    "food": "#C9893D",
    "energy": "#A8503A",
    "credits": "#8C8475",
}

BG = "#232B3D"
TEXT = "#EFE8D8"
GEN_COLORS = ["#C9893D", "#6E8C6A", "#A8503A", "#8C8475", "#7C6FA0"]


def _apply_dark_style(fig, ax):
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.tick_params(colors=TEXT, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#3A4A5E")
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)


def plot_resource_history(state) -> plt.Figure | None:
    if not state.resource_history:
        return None
    fig, ax = plt.subplots(figsize=(8, 3))
    _apply_dark_style(fig, ax)
    ticks = [r["tick"] for r in state.resource_history]
    for resource, color in RESOURCE_COLORS.items():
        values = [r[resource] for r in state.resource_history]
        ax.plot(ticks, values, label=resource, color=color, linewidth=1.5)
    for event in state.event_timeline:
        if event["type"] == "crisis":
            ax.axvline(
                event["tick"], color="#A8503A", linestyle="--", alpha=0.4, linewidth=0.8
            )
        elif event["type"] == "breakthrough":
            ax.axvline(
                event["tick"], color="#6E8C6A", linestyle="--", alpha=0.4, linewidth=0.8
            )
    ax.set_xlabel("Week", color=TEXT, fontsize=8)
    ax.set_ylabel("Level (%)", color=TEXT, fontsize=8)
    ax.legend(facecolor=BG, labelcolor=TEXT, fontsize=7, framealpha=0.7)
    ax.set_ylim(0, 150)
    fig.tight_layout()
    return fig


def plot_population_history(state) -> plt.Figure | None:
    if not state.population_history:
        return None
    fig, ax = plt.subplots(figsize=(8, 3))
    _apply_dark_style(fig, ax)
    years = [p["year"] for p in state.population_history]
    all_gens = sorted(
        set(gen for p in state.population_history for gen in p["by_generation"])
    )
    bottoms = [0] * len(years)
    for i, gen in enumerate(all_gens):
        values = [p["by_generation"].get(gen, 0) for p in state.population_history]
        ax.bar(
            years,
            values,
            bottom=bottoms,
            label=f"Gen {gen}",
            color=GEN_COLORS[i % len(GEN_COLORS)],
            alpha=0.85,
        )
        bottoms = [b + v for b, v in zip(bottoms, values)]
    ax.set_xlabel("Year", color=TEXT, fontsize=8)
    ax.set_ylabel("Population", color=TEXT, fontsize=8)
    ax.legend(facecolor=BG, labelcolor=TEXT, fontsize=7, framealpha=0.7)
    fig.tight_layout()
    return fig


def plot_cultural_drift(state) -> plt.Figure | None:
    if not state.cultural_profile_history:
        return None
    fig, ax = plt.subplots(figsize=(8, 3))
    _apply_dark_style(fig, ax)
    years = [c["year"] for c in state.cultural_profile_history]
    all_traits = sorted(
        set(trait for c in state.cultural_profile_history for trait in c["profile"])
    )
    palette = [
        "#C9893D",
        "#6E8C6A",
        "#A8503A",
        "#8C8475",
        "#7C6FA0",
        "#5B8FAB",
        "#D4A96A",
    ]
    for i, trait in enumerate(all_traits):
        values = [c["profile"].get(trait, 0) for c in state.cultural_profile_history]
        ax.plot(
            years, values, label=trait, linewidth=1.5, color=palette[i % len(palette)]
        )
    ax.set_xlabel("Year", color=TEXT, fontsize=8)
    ax.set_ylabel("Frequency", color=TEXT, fontsize=8)
    ax.legend(facecolor=BG, labelcolor=TEXT, fontsize=7, framealpha=0.7)
    fig.tight_layout()
    return fig
