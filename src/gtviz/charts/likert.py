"""Diverging Likert distribution bars.

Port of ``show_belonging``: stacked horizontal distribution of Likert answers
per item.

Original styling: 4-point answer palette ``tab:red -> tab:orange ->
tab:olive -> tab:green`` (low to high), figure ``(12, 0.8 + n_items)``,
white centered integer bar labels with zero-width sections suppressed, and
a frameless legend anchored outside the upper-right corner.
``reverse_answers`` flips both the stacking order and the colors, matching
the original's handling of negatively-worded items; ``highlight_agree``
recolors the agree end red ("red-is-bad" mode).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .._mpl import resolve_ax
from ..theme import palette

__all__ = ["likert_bars"]


def likert_bars(
    df: pd.DataFrame,
    items: list[str],
    item_labels: dict | None = None,
    answer_labels: list[str] | None = None,
    reverse_answers: bool = False,
    highlight_agree: bool = False,
    colors: list | None = None,
    min_label_width: float = 0,
    legend_anchor: tuple = (0.99, 1),
    ax=None,
    title: str | None = None,
    figsize: tuple | None = None,
):
    """100% stacked horizontal bars of answer shares for each Likert item.

    Parameters
    ----------
    items:
        Coded Likert columns (integer answer codes).
    answer_labels:
        Legend labels for the answer codes, low to high.
    reverse_answers:
        Flip answer order *and* colors (for negatively-worded items).
    highlight_agree:
        Recolor the agree end red (original "red agree" mode).
    min_label_width:
        Suppress bar labels for segments at or below this percent width
        (original suppresses only zero-width segments).

    Returns
    -------
    (fig, ax)
    """
    item_labels = item_labels or {}
    fig, ax, _ = resolve_ax(ax, figsize=figsize or (12, 0.8 + len(items)))

    cats = sorted(pd.unique(df[items].values.ravel()))
    cats = [c for c in cats if pd.notna(c)]
    ncat = len(cats)

    if colors is None:
        if ncat <= 4:
            colors = list(palette["likert4"][:ncat])
        else:
            import matplotlib.pyplot as plt

            colors = list(plt.get_cmap("RdYlGn")(np.linspace(0.08, 0.92, ncat)))
    if reverse_answers:
        cats = cats[::-1]
        colors = list(reversed(colors))
    if highlight_agree:
        colors = list(colors)
        colors[-1] = "tab:red"

    y = np.arange(len(items))[::-1]
    left = np.zeros(len(items))
    for ci, cat in enumerate(cats):
        shares = np.array([float((df[it] == cat).mean()) * 100 for it in items])
        lbl = answer_labels[ci] if answer_labels and ci < len(answer_labels) else str(cat)
        bars = ax.barh(y, shares, left=left, color=colors[ci % len(colors)], label=lbl, height=0.65)
        bar_labels = [f"{int(round(s))}" if s > min_label_width else "" for s in shares]
        ax.bar_label(bars, labels=bar_labels, label_type="center", color="w")
        left += shares

    ax.set_yticks(y)
    ax.set_yticklabels([item_labels.get(i, i) for i in items])
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of respondents")
    ax.legend(bbox_to_anchor=legend_anchor, loc="upper left", borderaxespad=0.0)
    if title:
        ax.set_title(title)
    fig.tight_layout()
    return fig, ax
