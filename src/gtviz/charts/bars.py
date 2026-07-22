"""Bar chart panels.

Port of ``parallel_bar_chart`` (baseline "Everyone" panel plus one panel per
demographic split, with +/- point-difference labels vs baseline) -- the
signature chart of Part 6 of the quarterly report. Fixes the original
in-place ``ylabels.reverse()`` mutation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import options
from ..theme import palette

__all__ = ["parallel_bars"]


def parallel_bars(
    df: pd.DataFrame,
    variables: list[str],
    ylabels: list[str],
    splits: list[tuple],
    sub_titles: list[str] | None = None,
    colors: list | None = None,
    weights: str | None = "auto",
    title: str = "",
    baseline_label: str = "Everyone",
    figsize: tuple = (8, 10),
):
    """Baseline vs subgroup horizontal bar panels with difference labels.

    Parameters
    ----------
    df:
        Respondent-level data.
    variables:
        Binary metric columns, top-to-bottom order.
    ylabels:
        Display labels matching ``variables``.
    splits:
        List of ``(column, level)`` pairs; each produces one subgroup panel
        filtered to ``df[column] == level``.
    sub_titles:
        Panel titles for the splits (defaults to ``"col=level"``).
    colors:
        One color per panel (baseline first).
    weights:
        ``"auto"``, column name, or None (unweighted).

    Returns
    -------
    (fig, axes)
    """
    import matplotlib.pyplot as plt

    sub_titles = sub_titles or [f"{c}={v}" for c, v in splits]
    colors = colors or palette["series"]
    wcol = options.weight_col if weights == "auto" else weights

    def pct(sub: pd.DataFrame) -> pd.Series:
        w = sub[wcol] if (wcol and wcol in sub) else pd.Series(1.0, index=sub.index)
        vals = pd.Series(
            {v: np.average(sub[v].fillna(0), weights=w) * 100 for v in variables}
        )
        return vals.iloc[::-1]  # reversed for top-down display

    fig, axes = plt.subplots(nrows=1, ncols=len(splits) + 1, sharey="row", sharex="all",
                             figsize=figsize)
    axes = np.atleast_1d(axes)

    base = pct(df)
    axes[0].set_title(baseline_label, fontsize=12, pad=1)
    axes[0].barh(base.index, base.values, 0.75, color=colors[0], alpha=0.5)
    for p, pr in base.items():
        ha, x = ("right", pr - 1) if pr >= 10 else ("left", pr + 1)
        axes[0].text(s=f"{pr:.0f}", x=x, y=p, va="center", ha=ha, size=10)

    for i, (col, level) in enumerate(splits):
        ax = axes[i + 1]
        vals = pct(df[df[col] == level])
        ax.set_title(sub_titles[i], fontsize=12, pad=1)
        ax.barh(vals.index, vals.values, 0.75, color=colors[(i + 1) % len(colors)], alpha=0.5)
        for p, pr, pb in zip(vals.index, vals.values, base.values):
            diff = round(pr - pb)
            if diff == 0:
                continue
            txt = f"+{diff}" if diff > 0 else str(diff)
            ha, x = ("right", pr - 1) if pr >= 10 else ("left", pr + 1)
            ax.text(s=txt, x=x, y=p, va="center", ha=ha, size=10)

    axes[0].set_yticks(range(len(variables)))
    axes[0].set_yticklabels(list(reversed(ylabels)))  # no in-place mutation
    fig.text(0.5, 0.92, "% of Respondents", ha="center", va="center", fontsize=12)
    if title:
        fig.suptitle(title, fontsize=18, fontweight="bold", y=0.97)
    return fig, axes
