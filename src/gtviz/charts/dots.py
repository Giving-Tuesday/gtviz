"""Dot plots: the richest chart family in the original repo.

Consolidates the generic ``dot_plot`` primitive plus its five near-clone
wrappers (``depolarization_groups_dot_plot``,
``depolarization_vs_civic_intent_dot_plot``,
``civic_intent_vs_depolarization_dot_plot``, ``civic_intent_belonging_dot_plot``,
``depolarization_vs_QCountry_plot``) into :func:`dot_plot` and
:func:`grouped_dot_plot`, and the quarterly-trend variants
(``trends_dot_plot``, ``draft_grouped_trends_dot_plot``) into
:func:`trend_dot_plot`.

Styling defaults are ported verbatim from the originals: ``.`` marker at
size 10 with zero edge width, error intervals drawn as same-color hlines
(no caps), dotted ``0.8``-gray y-grid, y-ticks on both sides, and -- for the
grouped report wrappers -- a frameless legend outside the right edge, no
axes box, gray-first series colors with "Everyone" leading, ``n=`` counts in
legend labels, and 25-character label wrapping.
"""

from __future__ import annotations

import textwrap

import numpy as np
import pandas as pd

from .._mpl import resolve_ax
from ..theme import palette
from ._legend import apply_legend

__all__ = ["dot_plot", "grouped_dot_plot", "trend_dot_plot"]


def _wrap(labels, width):
    if not width:
        return list(labels)
    return ["\n".join(textwrap.wrap(str(el), width)) for el in labels]


def dot_plot(
    values,
    labels,
    error=None,
    datalabels: bool = False,
    ax=None,
    xrange: tuple = (0, 100),
    color: str | None = None,
    marker: str = ".",
    markersize: int = 10,
    title: str | None = None,
    xlabel: str = "",
    label: str | None = None,
    wrap: int | None = None,
    figsize: tuple | None = None,
):
    """Horizontal dot plot (faithful port of the ``dot_plot`` primitive).

    Parameters
    ----------
    values:
        Sequence of numeric values (typically 0-100 percents).
    labels:
        Category labels, same length as ``values``.
    error:
        Optional symmetric error (half-width); drawn as same-color
        horizontal interval lines, matching the original ``ax.hlines`` style.
    datalabels:
        Annotate each dot with its value. **Off by default** -- the original
        report dot plots never annotate values.
    marker, markersize:
        Original defaults: ``"."`` at size 10, zero marker edge width.
    label:
        Legend label for this series (for multi-series composition on a
        shared ``ax``).
    wrap:
        Wrap category labels at this many characters (report wrappers use 25).

    Returns
    -------
    (fig, ax)
    """
    fig, ax, _ = resolve_ax(ax, figsize=figsize or (9, 4))
    values = np.asarray(values, dtype=float)
    n = len(labels)
    y = np.arange(n)[::-1]

    line = ax.plot(values, y, marker=marker, linestyle="", markersize=markersize,
                   markeredgewidth=0, color=color, label=label, zorder=3)
    if error is not None:
        error = np.asarray(error, dtype=float)
        ax.hlines(y, values - error, values + error, color=line[0].get_color(), zorder=2)
    if datalabels:
        for v, yy in zip(values, y):
            ax.annotate(f"{v:.0f}", (v, yy), textcoords="offset points", xytext=(0, 9),
                        ha="center", fontsize=10)

    ax.yaxis.set_ticks(range(n))
    ax.yaxis.set_ticklabels(_wrap(labels, wrap)[::-1])
    ax.set_ylim(-1, n)
    ax.set_xlim(*xrange)
    ax.tick_params(axis="y", which="major", right="on", left="on", color=palette["grid"])
    ax.grid(axis="y", which="major", color=palette["grid"], zorder=-10, linestyle=":")
    # dot plots read as a scale: keep the bottom axis even under the sparse theme
    ax.spines["bottom"].set_visible(True)
    ax.set_xlabel(xlabel)
    if title:
        ax.set_title(title)
    return fig, ax


def grouped_dot_plot(
    df: pd.DataFrame,
    group_col: str,
    metric_cols: list[str],
    metric_labels: dict | None = None,
    group_labels: dict | None = None,
    include_all: bool = True,
    all_label: str = "Everyone",
    agg: str = "mean",
    as_percent: bool = True,
    colors: list | None = None,
    markersize: int = 8,
    error: bool = False,
    show_n: bool = True,
    wrap: int | None = 25,
    box: bool = False,
    ax=None,
    xrange: tuple = (-1, 101),
    title: str | None = None,
    xlabel: str = "Percent",
    legend_anchor: tuple = (1, 0.85),
    legend_wrap: int | None = None,
    legend_truncate: int | None = None,
    figsize: tuple = (9, 4),
):
    """One dot series per group across a set of metrics.

    Generalizes the five depolarization/civic-intent dot plot clones with the
    original report styling: gray "Everyone" series first, marker size 8,
    frameless legend anchored outside the right edge with ``n=`` counts,
    x-axis ``(-1, 101)``, "Percent" x-label (labelpad 10), category labels
    wrapped at 25 characters, and no axes box.

    Parameters
    ----------
    show_n:
        Append ``(n=...)`` to legend labels (report style).
    wrap:
        Wrap metric labels at this many characters (None disables).
    box:
        Draw the axes box/spines (original wrappers turn it off).
    legend_anchor:
        ``bbox_to_anchor`` for the frameless legend.

    Returns
    -------
    (fig, ax)
    """
    metric_labels = metric_labels or {}
    group_labels = group_labels or {}
    groups = list(df[group_col].dropna().unique())
    series = colors or palette["series"]

    fig, ax, _ = resolve_ax(ax, figsize=figsize)

    def stats_for(sub: pd.DataFrame):
        vals = sub[metric_cols].agg(agg) * (100 if as_percent else 1)
        if error:
            n = len(sub)
            p = vals / 100
            err = 1.96 * np.sqrt(np.clip(p * (1 - p), 0, None) / max(n, 1)) * 100
            return vals.values, err.values
        return vals.values, None

    plotted = []
    if include_all:
        plotted.append((all_label, len(df), *stats_for(df)))
    for g in groups:
        sub = df[df[group_col] == g]
        plotted.append((group_labels.get(g, g), len(sub), *stats_for(sub)))

    labels = _wrap([metric_labels.get(c, c) for c in metric_cols], wrap)
    for i, (name, n, vals, err) in enumerate(plotted):
        legend_label = f"{name} (n={n})" if show_n else str(name)
        dot_plot(vals, labels, error=err, ax=ax, xrange=xrange,
                 color=series[i % len(series)], markersize=markersize,
                 label=legend_label)

    ax.set_xlabel(xlabel, labelpad=10)
    apply_legend(ax, wrap=legend_wrap, truncate=legend_truncate, bbox_to_anchor=legend_anchor)
    if not box:
        for spine in ax.spines.values():
            spine.set_visible(False)
    if title:
        fig.suptitle(title)
    return fig, ax


def trend_dot_plot(
    df: pd.DataFrame,
    time_col: str,
    metric_cols: list[str],
    metric_labels: dict | None = None,
    agg: str = "mean",
    as_percent: bool = True,
    label_points: bool = True,
    shade_periods: bool = False,
    max_percent: float = 60,
    colors: list | None = None,
    markersize: int = 8,
    show_n: bool = False,
    wrap: int | None = 25,
    box: bool = False,
    ax=None,
    title: str | None = None,
    xlabel: str = "Percent",
    legend_anchor: tuple = (1, 0.85),
    legend_wrap: int | None = None,
    legend_truncate: int | None = None,
    figsize: tuple = (9, 4),
):
    """Metrics-by-period dot columns (port of ``trends_dot_plot``).

    Each metric gets a horizontal lane; each period a colored dot in that
    lane, showing movement over time. Shares the report dot-plot styling
    (frameless outside legend, no box, wrapped labels).
    """
    metric_labels = metric_labels or {}
    periods = sorted(df[time_col].dropna().unique())
    series = colors or palette["series"][1:]  # skip the gray "Everyone" slot
    fig, ax, _ = resolve_ax(ax, figsize=figsize)
    y = np.arange(len(metric_cols))[::-1]
    labels = _wrap([metric_labels.get(c, c) for c in metric_cols], wrap)

    for pi, period in enumerate(periods):
        sub = df[df[time_col] == period]
        vals = sub[metric_cols].agg(agg).values * (100 if as_percent else 1)
        color = series[pi % len(series)]
        name = f"{period} (n={len(sub)})" if show_n else str(period)
        ax.plot(vals, y, marker=".", linestyle="", markersize=markersize,
                markeredgewidth=0, color=color, label=name, zorder=3)
        if label_points:
            for v, yy in zip(vals, y):
                ax.annotate(f"{v:.0f}", (v, yy), textcoords="offset points", xytext=(0, 8),
                            ha="center", fontsize=8, color=color)

    if shade_periods:
        for i in range(0, len(metric_cols), 2):
            ax.axhspan(y[i] - 0.5, y[i] + 0.5, color="0.93", zorder=-20)

    ax.yaxis.set_ticks(range(len(metric_cols)))
    ax.yaxis.set_ticklabels(labels[::-1])
    ax.set_ylim(-1, len(metric_cols))
    ax.set_xlim(0, max_percent)
    ax.tick_params(axis="y", which="major", right="on", left="on", color=palette["grid"])
    ax.grid(axis="y", color=palette["grid"], linestyle=":", zorder=-10)
    ax.set_xlabel(xlabel, labelpad=10)
    apply_legend(ax, wrap=legend_wrap, truncate=legend_truncate, bbox_to_anchor=legend_anchor, title=time_col)
    if not box:
        for spine in ax.spines.values():
            spine.set_visible(False)
    if title:
        fig.suptitle(title)
    return fig, ax
