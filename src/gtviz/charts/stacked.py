"""100% stacked horizontal band bars (report style).

The "How Civic Intent varies by country" figure: one bar per category, each
divided into ordered bands (e.g. score quintiles ``Lowest 0-20`` ...
``80-100 Highest``) that sum to 100%. Distinct from
:func:`gtviz.charts.likert_bars`, which *computes* answer distributions from
respondent-level Likert columns -- :func:`stacked_bars` takes an
already-tabulated categories x bands table (or computes one from a value
column via ``bins=``).

Brand defaults: the red -> orange -> olive -> green -> blue 5-band scale,
horizontal frameless legend across the top, x-axis 0-100, bold left title
with gray subtitle.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .._mpl import brand_title, resolve_ax
from ..theme import palette

__all__ = ["stacked_bars", "banded_shares"]


def banded_shares(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    bins: list[float] = (0, 20, 40, 60, 80, 100),
    band_labels: list[str] | None = None,
    weights: str | None = None,
) -> pd.DataFrame:
    """Tabulate percent of each category falling into each value band.

    Returns a categories x bands DataFrame of percentages summing to 100 per
    row -- the input shape :func:`stacked_bars` plots.
    """
    bins = list(bins)
    if band_labels is None:
        band_labels = [f"{lo:g}-{hi:g}" for lo, hi in zip(bins[:-1], bins[1:])]
        band_labels[0] = f"Lowest {band_labels[0]}"
        band_labels[-1] = f"{band_labels[-1]} Highest"
    cut = pd.cut(df[value_col], bins=bins, labels=band_labels, include_lowest=True)
    w = df[weights] if weights else pd.Series(1.0, index=df.index)
    tab = (
        pd.DataFrame({"cat": df[category_col], "band": cut, "w": w})
        .pivot_table(index="cat", columns="band", values="w", aggfunc="sum", observed=False)
        .fillna(0)
    )
    return (tab.div(tab.sum(axis=1), axis=0) * 100).round(1)


def stacked_bars(
    table: pd.DataFrame,
    colors: list | None = None,
    bar_labels: bool = False,
    min_label_width: float = 5,
    height: float = 0.65,
    legend: str = "top",
    legend_ncol: int | None = None,
    xlabel: str = "Percent of the population in each range",
    title: str | None = None,
    subtitle: str | None = None,
    n: int | None = None,
    ax=None,
    figsize: tuple | None = None,
):
    """100% stacked horizontal bars from a categories x bands table.

    Parameters
    ----------
    table:
        DataFrame indexed by category (rows plot top-to-bottom in index
        order); columns are the bands in stacking order (left to right);
        values are percents (rows should sum to ~100 -- use
        :func:`banded_shares` to build one from respondent-level data).
    colors:
        One color per band; defaults to the 5-band brand scale
        (``theme.palette["bands5"]``) when the table has five columns.
    bar_labels:
        Write each segment's integer percent centered in the segment
        (suppressed under ``min_label_width``).
    legend:
        ``"top"`` (horizontal above the plot, report style), ``"right"``,
        or ``"none"``.
    legend_ncol:
        Number of legend columns. Defaults to ``min(len(bands), 5)`` for the
        top legend and 1 for the right legend.

    Returns
    -------
    (fig, ax)
    """
    bands = list(table.columns)
    cats = list(table.index)
    if colors is None:
        colors = palette["bands5"] if len(bands) == 5 else [
            c for c in palette["bands5"]][:len(bands)] or None
    if colors is None or len(colors) < len(bands):
        colors = list(plt.get_cmap("RdYlGn")(np.linspace(0.08, 0.92, len(bands))))

    fig, ax, _ = resolve_ax(ax, figsize=figsize or (10, 0.55 * len(cats) + 1.8))
    y = np.arange(len(cats))[::-1]
    left = np.zeros(len(cats))
    for bi, band in enumerate(bands):
        vals = table[band].to_numpy(dtype=float)
        bars = ax.barh(y, vals, left=left, height=height,
                       color=colors[bi % len(colors)], label=str(band))
        if bar_labels:
            lbls = [f"{v:.0f}" if v > min_label_width else "" for v in vals]
            ax.bar_label(bars, labels=lbls, label_type="center", color="w", fontsize=9)
        left += vals

    ax.set_yticks(y)
    ax.set_yticklabels(cats)
    ax.set_xlim(0, 100)
    ax.set_xlabel(xlabel)
    top_leg = None
    if legend == "top":
        top_leg = ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02),
                            ncol=legend_ncol or min(len(bands), 5), borderaxespad=0.0)
    elif legend == "right":
        ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left",
                  ncol=legend_ncol or 1, borderaxespad=0.0)
        brand_title(ax, title, subtitle=subtitle, n=n)
    else:
        brand_title(ax, title, subtitle=subtitle, n=n)
    fig.tight_layout()
    if top_leg is not None:
        # Place the title/subtitle ABOVE the (possibly multi-row) top legend, measured
        # after layout, so they never overlap it regardless of legend rows or figure size.
        sub = subtitle or (f"n = {n:,} respondents" if n else None)
        if title or sub:
            fig.canvas.draw()
            y = top_leg.get_window_extent().transformed(fig.transFigure.inverted()).y1
            if sub:
                fig.text(0.5, y + 0.015, sub, ha="center", va="bottom",
                         fontsize=10, color=palette["subtitle"])
                y += 0.05
            if title:
                fig.text(0.5, y + 0.015, title, ha="center", va="bottom",
                         fontweight="bold", fontsize=plt.rcParams.get("axes.titlesize", 14))
    return fig, ax
