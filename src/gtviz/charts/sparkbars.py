"""Sparkline bar plot -- a bar chart whose bars are squished sparklines.

Where a normal bar chart draws one bar per category, :func:`sparkline_bar_plot`
draws one small time-series per category in the bar's footprint, so a single
frame shows both the cross-category comparison (shared y-axis) and each
category's variation over time. Built for "a metric by subgroup across weeks"
panels -- e.g. share who gave, by Pew political type, week over week.

Brand defaults: a left-to-right ``RdYlBu_r`` (blue -> yellow -> red) spectrum,
one glyph per category, a thin dashed line at each category's timeframe
average (labelled), min (low) / max (high) / latest markers, no shaded
background, frameless top/right spines, bold left title with gray subtitle.
Pairs with :func:`gtviz.stats.rolling_summary` (``group_col=``), which produces
the ``[period x category]`` table this plots.
"""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .._mpl import brand_title, resolve_ax
from ..theme import palette

__all__ = ["sparkline_bar_plot"]


def _resolve_colors(colors, cmap, n):
    """None -> left-to-right spectrum from ``cmap``; str -> uniform; list -> per glyph."""
    if colors is None:
        return [matplotlib.colors.to_hex(plt.get_cmap(cmap)(i / max(n - 1, 1))) for i in range(n)]
    if isinstance(colors, str):
        return [colors] * n
    return list(colors)[:n]


def _darken(color, f):
    r, g, b = matplotlib.colors.to_rgb(color)
    return (r * f, g * f, b * f)


def sparkline_bar_plot(
    table: pd.DataFrame,
    order: list | None = None,
    labels: dict | None = None,
    values: pd.Series | dict | None = None,
    colors: list | str | None = None,
    cmap: str = "RdYlBu_r",
    linewidth: float | None = None,
    slot_width: float = 0.72,
    show_last: bool = True,
    show_extremes: bool = True,
    show_mean: bool = True,
    zero_base: bool = False,
    value_fmt: str = "{:.0f}",
    ylabel: str = "",
    spectrum: tuple | None = None,
    xlabel: str | None = None,
    n: int | None = None,
    title: str | None = None,
    subtitle: str | None = None,
    ax=None,
    figsize: tuple | None = None,
):
    """Bar-chart-shaped sparklines: one squished time-series per category.

    Parameters
    ----------
    table:
        DataFrame indexed by period (oldest -> newest); one column per category
        (each becomes one glyph). Typically the output of
        :func:`gtviz.stats.rolling_summary` with ``group_col=``.
    order:
        Column order left -> right (defaults to ``table.columns``).
    labels:
        Optional ``{column: display label}`` for the x tick labels.
    values:
        Number printed above each glyph -- pass a Series/dict keyed by column
        (e.g. the pooled timeframe average from ``subgroup_summary``); defaults
        to each glyph's own per-period mean. A thin dashed line marks it.
    colors:
        ``None`` -> left-to-right spectrum from ``cmap``; a single color ->
        uniform; a list -> one per glyph.
    slot_width:
        Fraction of each category slot the glyph occupies (0-1).
    zero_base:
        ``False`` (default) zooms the shared y-axis to the data range so the
        variation reads; ``True`` starts the axis at 0.
    spectrum:
        Optional ``(left_label, right_label)`` annotation appended to the
        x-axis label to name the ordering axis.

    Returns
    -------
    (fig, ax)
    """
    pal = palette
    sub_col = pal.get("subtitle", "#666666")
    if linewidth is None:
        linewidth = plt.rcParams.get("lines.linewidth", 3.0) * 0.5
    cols = [c for c in (order or list(table.columns)) if c in table.columns]
    ncat, nper = len(cols), len(table.index)
    cser = _resolve_colors(colors, cmap, ncat)

    figsize = figsize or (max(7.5, 1.0 * ncat + 1.5), 4.8)
    fig, ax, _ = resolve_ax(ax, figsize=figsize)
    tnorm = np.linspace(-slot_width / 2, slot_width / 2, nper) if nper > 1 else np.array([0.0])
    allvals = []
    for i, c in enumerate(cols):
        y = pd.to_numeric(table[c], errors="coerce").to_numpy()
        finite = y[np.isfinite(y)]
        if not finite.size:
            continue
        allvals.append(finite)
        xi = i + tnorm
        cline, ctext = _darken(cser[i], 0.85), _darken(cser[i], 0.58)
        ax.plot(xi, y, color=cline, linewidth=linewidth, solid_capstyle="round",
                solid_joinstyle="round", zorder=3)
        mval = (float(values.get(c)) if (values is not None and c in values and pd.notna(values.get(c)))
                else float(np.nanmean(y)))
        if show_mean:
            ax.plot([i - slot_width / 2, i + slot_width / 2], [mval, mval], color=cline,
                    lw=0.8, alpha=0.45, ls=(0, (3, 2)), zorder=2)
        if show_extremes:
            ax.plot(xi[np.nanargmin(y)], finite.min(), "o", ms=3, color=pal.get("low", "#fae8eb"),
                    mec="#c0504d", mew=0.6, zorder=4)
            ax.plot(xi[np.nanargmax(y)], finite.max(), "o", ms=3, color=pal.get("high", "#dcfcd9"),
                    mec="#4a7a43", mew=0.6, zorder=4)
        if show_last:
            last = np.where(np.isfinite(y))[0][-1]
            ax.plot(xi[last], y[last], "o", ms=4, color=cline, zorder=5)
        ax.annotate(value_fmt.format(mval), (i, finite.max()), textcoords="offset points",
                    xytext=(0, 6), ha="center", va="bottom", fontsize=8.5,
                    color=ctext, fontweight="bold")

    gmin = min(v.min() for v in allvals)
    gmax = max(v.max() for v in allvals)
    pad = max((gmax - gmin) * 0.12, 0.5)
    ax.set_ylim(0 if zero_base else gmin - pad, gmax + pad + (gmax - gmin) * 0.12)
    ax.set_xlim(-0.6, ncat - 0.4)
    ax.set_xticks(range(ncat))
    ax.set_xticklabels([(labels or {}).get(c, c) for c in cols], fontsize=8)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    xl = xlabel
    if spectrum:
        tail = f"({spectrum[0]}            {spectrum[1]})"
        xl = f"{xlabel}   {tail}" if xlabel else tail
    if xl:
        ax.set_xlabel(xl, fontsize=9, color=sub_col, labelpad=8)

    brand_title(ax, title, subtitle=subtitle, n=n)
    fig.tight_layout()
    return fig, ax
