"""Civic-intent report charts: contribution bars, benchmark bubbles,
dumbbell ranges, arrow ranges, and nested (subset) bars.

Faithful ports of the civic/civil-intent figures: horizontal tab:blue bars
with signed white value labels ("+27"), optional gray benchmark bubbles
beside each bar, dumbbell range plots with red/green endpoint scores in gray
bubbles plus a dotted benchmark line, directional arrow ranges (tab:red when
decreasing, linewidth 3), and layered subset bars (gray total, cyan subset,
blue sub-subset).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .._mpl import brand_title, resolve_ax

__all__ = ["contribution_bars", "range_dot_plot", "arrow_range_plot", "nested_bars"]

_BUBBLE = dict(boxstyle="circle,pad=0.32", fc="#d4d4d4", ec="none")


def contribution_bars(
    values, labels, benchmarks=None, signed: bool = True,
    color: str = "tab:blue", benchmark_color: str = "tab:blue",
    xrange: tuple = (0, 30), wrap: int = 42, height: float = 0.55,
    title=None, subtitle=None, n=None, ax=None, figsize=None,
):
    """Horizontal bars with signed white value labels inside the bar end
    (Figure 2.2 style); optional gray benchmark bubbles after each bar
    (Figure 2.4 style).

    Parameters
    ----------
    values: bar lengths (e.g. score contributions in points).
    benchmarks: optional per-bar score shown in a gray circle to the right.
    signed: label bars as "+27" / "-4" rather than "27".
    """
    import textwrap

    values = np.asarray(values, dtype=float)
    y = np.arange(len(labels))[::-1]
    fig, ax, _ = resolve_ax(ax, figsize=figsize or (11, 0.6 * len(labels) + 1.5))
    bars = ax.barh(y, values, height=height, color=color)
    fmt = (lambda v: f"{v:+.0f}") if signed else (lambda v: f"{v:.0f}")
    ax.bar_label(bars, labels=[fmt(v) for v in values], label_type="edge",
                 padding=-34, color="w")
    if benchmarks is not None:
        pad = (xrange[1] - xrange[0]) * 0.09
        for v, yy, b in zip(values, y, benchmarks):
            ax.annotate(f"{b:.0f}", (v + pad, yy), ha="center", va="center",
                        color=benchmark_color, fontweight="bold", bbox=_BUBBLE)
    ax.set_yticks(y)
    ax.set_yticklabels(["\n".join(textwrap.wrap(str(t), wrap)) for t in labels])
    ax.set_xlim(*xrange)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(axis="x", length=2)
    brand_title(ax, title, subtitle=subtitle, n=n)
    fig.tight_layout()
    return fig, ax


def range_dot_plot(
    df: pd.DataFrame, low_col: str, high_col: str, label_col=None,
    right_labels: list | None = None, benchmark: float | None = None,
    benchmark_label: str = "Civil Intent\naverage",
    low_color: str = "tab:red", high_color: str = "tab:green",
    line_color: str = "tab:blue", wrap: int = 46,
    title=None, subtitle=None, n=None, ax=None, figsize=None,
):
    """Dumbbell range plot (Figure A.1): a line from each item's low score to
    its high score, endpoint values in gray bubbles (low red, high green),
    the gap labeled mid-line, an optional dotted benchmark line, and optional
    right-margin labels (e.g. "% who affirmed").

    ``df`` rows plot top-to-bottom; ``label_col`` defaults to the index.
    """
    import textwrap

    labels = list(df[label_col]) if label_col else list(df.index)
    lo, hi = df[low_col].to_numpy(float), df[high_col].to_numpy(float)
    y = np.arange(len(labels))[::-1]
    fig, ax, _ = resolve_ax(ax, figsize=figsize or (11, 0.6 * len(labels) + 1.8))
    for yy, a, b in zip(y, lo, hi):
        ax.plot([a, b], [yy, yy], color=line_color, linewidth=3, zorder=1)
        ax.annotate(f"{b - a:.0f}", ((a + b) / 2, yy), ha="center", va="center",
                    color=line_color, fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"), zorder=2)
        ax.annotate(f"{a:.0f}", (a, yy), ha="center", va="center", color=low_color,
                    fontweight="bold", bbox=_BUBBLE, zorder=3)
        ax.annotate(f"{b:.0f}", (b, yy), ha="center", va="center", color=high_color,
                    fontweight="bold", bbox=_BUBBLE, zorder=3)
    if benchmark is not None:
        ax.axvline(benchmark, ymax=0.94, ls=":", linewidth=1, color=line_color)
        ax.text(benchmark, len(labels) - 0.45, benchmark_label, color=line_color,
                ha="center", fontsize=10)
    if right_labels is not None:
        for yy, r in zip(y, right_labels):
            ax.annotate(str(r), xy=(1.02, 0), xycoords=("axes fraction", "data"),
                        ha="left", va="center", color="#666666",
                        xytext=(0, 0), textcoords="offset points",
                        annotation_clip=False)
            # place at correct y via data coords
        for txt, yy in zip(ax.texts[-len(right_labels):], y):
            txt.set_position((1.02, yy))
    ax.set_yticks(y)
    ax.set_yticklabels(["\n".join(textwrap.wrap(str(t), wrap)) for t in labels])
    ax.set_ylim(-1, len(labels))
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(axis="both", length=2)
    brand_title(ax, title, subtitle=subtitle, n=n)
    fig.tight_layout()
    return fig, ax


def arrow_range_plot(
    df: pd.DataFrame, series: dict, label_col=None,
    averages: dict | None = None, negative_color: str = "tab:red",
    wrap: int = 46, title=None, subtitle=None, n=None, ax=None, figsize=None,
):
    """Directional arrow ranges (Figure A.2): per item, one arrow per series
    from a start to an end value -- pointing right for increases, left (and
    ``tab:red``) for decreases. Optional dotted average lines with labels.

    Parameters
    ----------
    series:
        ``{"Belonging": (start_col, end_col, "tab:green"), ...}``.
    averages:
        ``{"Belonging\\naverage": (value, "tab:green"), ...}`` dotted
        vertical reference lines.
    """
    import textwrap

    labels = list(df[label_col]) if label_col else list(df.index)
    y = np.arange(len(labels))[::-1]
    fig, ax, _ = resolve_ax(ax, figsize=figsize or (12, 2 + 0.6 * len(labels)))
    for _name, (c0, c1, color) in series.items():
        a, b = df[c0].to_numpy(float), df[c1].to_numpy(float)
        for yy, x0, x1 in zip(y, a, b):
            col = negative_color if x1 < x0 else color
            ax.annotate("", xy=(x1, yy), xytext=(x0, yy),
                        arrowprops=dict(arrowstyle="-|>", color=col, linewidth=3,
                                        mutation_scale=18))
    if averages:
        top = len(labels) - 0.3
        for lbl, (val, color) in averages.items():
            ax.axvline(val, ymax=0.94, ls=":", linewidth=1, color=color)
            ax.text(val, top, lbl, color=color, ha="center", fontsize=10)
    ax.set_yticks(y)
    ax.set_yticklabels(["\n".join(textwrap.wrap(str(t), wrap)) for t in labels])
    ax.set_ylim(-1, len(labels) + 0.3)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(axis="both", length=2)
    brand_title(ax, title, subtitle=subtitle, n=n)
    fig.tight_layout()
    return fig, ax


def nested_bars(
    table: pd.DataFrame, colors: list | None = None,
    width: float = 0.75, ylabel: str = "", xlabel: str = "",
    legend_loc: str = "upper left",
    title=None, subtitle=None, n=None, ax=None, figsize=(9, 6),
):
    """Layered subset bars (Figure A.5): each column of ``table`` is a
    progressively smaller subset drawn in front of the previous one at the
    same x -- gray total, cyan subset, blue sub-subset by default.

    ``table``: index = categories (x axis), columns = layers outer-to-inner,
    values = percents/levels.
    """
    layers = list(table.columns)
    colors = colors or ["#cccccc", "#29b8cf", "#1f77b4"]
    x = np.arange(len(table))
    fig, ax, _ = resolve_ax(ax, figsize=figsize)
    for li, layer in enumerate(layers):
        ax.bar(x, table[layer].to_numpy(float), width=width,
               color=colors[li % len(colors)], label=str(layer), zorder=li + 1)
    ax.set_xticks(x)
    ax.set_xticklabels(table.index)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.legend(loc=legend_loc)
    brand_title(ax, title, subtitle=subtitle, n=n)
    fig.tight_layout()
    return fig, ax
