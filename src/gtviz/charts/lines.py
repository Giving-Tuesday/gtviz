"""Trend line charts: rolling weekly trends and split lines -- report style.

Brand defaults from the published figures: thick (rc 2.5) plain solid lines
in the tableau (tab10) cycle, **no point markers**, no grid, no top/right
spines (rc), frameless legend inside the plot area, bold left-aligned title
with a gray "Rolling N-week average | n = X respondents" subtitle.

Consolidates ``plot_monetary_giving_rolling_weeks``, the three duplicate
``weekly_trends_plot_news_aware`` definitions, ``civic_gt_awareness_splits``
and ``civic_gt_awareness_split_quartiles``, plus ``crisis_awareness_plot``'s
event-annotation idea.
"""

from __future__ import annotations

import pandas as pd

from .._mpl import brand_title, resolve_ax
from ..stats.summaries import rolling_summary
from ..theme import palette

__all__ = ["rolling_trend", "split_line_plot", "annotated_event_plot"]


def rolling_trend(
    df: pd.DataFrame,
    columns: list[str],
    time_col: str = "collection_week",
    window: int = 3,
    labels: dict | None = None,
    weights: str | None = "auto",
    colors: list | None = None,
    marker: str | None = None,
    linewidth: float | None = None,
    shade: pd.Series | tuple | None = None,
    shade_color: str = "grey",
    shade_alpha: float = 0.2,
    grid: bool = False,
    legend_loc: str | tuple = "best",
    ax=None,
    title: str | None = None,
    subtitle: str | None = None,
    n: int | None = None,
    ylabel: str = "% of respondents",
    xlabel: str | None = None,
    ylim: tuple | None = None,
    figsize: tuple = (10, 6),
):
    """Rolling weighted trend lines, one per metric column (report style).

    Parameters
    ----------
    colors:
        Explicit line colors; default None uses the matplotlib/tableau
        color cycle (the report figures' palette).
    marker:
        Point marker; the report figures draw plain lines (None).
    linewidth:
        Defaults to the theme's 2.5.
    shade:
        Gray background band marking a period: a ``(start, stop)`` tuple in
        ``time_col`` units or a boolean Series indexed like the summary.
    subtitle, n:
        Gray header line under the bold title; ``n=`` renders
        "n = 5,387 respondents". Combine manually via ``subtitle=`` for
        "Rolling four-week average | n = 5,387 respondents".

    Returns
    -------
    (fig, ax); the summarized data is available via ``ax._gtviz_data``.
    """
    labels = labels or {}
    summary = rolling_summary(df, columns, time_col=time_col, window=window, weights=weights)
    fig, ax, _ = resolve_ax(ax, figsize=figsize)

    if shade is not None:
        top = float(summary.max().max()) * 1.05
        if isinstance(shade, tuple):
            ax.axvspan(shade[0], shade[1], color=shade_color, alpha=shade_alpha, zorder=-10)
        else:
            mask = pd.Series(shade).reindex(summary.index).fillna(False).astype(float)
            ax.fill_between(summary.index, 0, mask * top, color=shade_color,
                            alpha=shade_alpha, zorder=-10)

    for i, c in enumerate(columns):
        kwargs = {"label": labels.get(c, c)}
        if colors:
            kwargs["color"] = colors[i % len(colors)]
        if marker:
            kwargs["marker"] = marker
        if linewidth:
            kwargs["linewidth"] = linewidth
        ax.plot(summary.index, summary[c], **kwargs)

    ax.set_ylabel(ylabel)
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if grid:
        ax.grid(axis="y", color=palette["grid"], linestyle=":", zorder=-10)
    if isinstance(legend_loc, tuple):
        ax.legend(bbox_to_anchor=legend_loc)
    else:
        ax.legend(loc=legend_loc)
    if ylim:
        ax.set_ylim(*ylim)
    brand_title(ax, title, subtitle=subtitle, n=n)
    ax._gtviz_data = summary
    fig.tight_layout()
    return fig, ax


def split_line_plot(
    df: pd.DataFrame,
    value_col: str,
    split: dict | str | None,
    time_col: str = "collection_week",
    metric: str = "mean",
    by_quartile: bool = False,
    labels: dict | None = None,
    colors: list | None = None,
    marker: str | None = None,
    linewidth: float | None = None,
    grid: bool = False,
    legend_loc: str | tuple = "best",
    ax=None,
    title: str | None = None,
    subtitle: str | None = None,
    n: int | None = None,
    figsize: tuple = (10, 6),
):
    """Trend of one metric split by group (or by its own quartiles).

    Merges ``civic_gt_awareness_splits`` and ``..._split_quartiles``:

    - ``split`` a column name: one line per level of that column.
    - ``split`` a dict ``{label: boolean mask}``: one line per mask.
    - ``by_quartile=True``: one line per quartile of ``value_col``.

    Report style: thick plain lines in the tableau cycle, no markers, no
    grid, frameless inside legend. Pass
    ``colors=gtviz.theme.palette["split_series"]`` for the legacy
    light-gray-Everyone-first palette.
    """
    labels = labels or {}
    fig, ax, _ = resolve_ax(ax, figsize=figsize)

    if by_quartile:
        q = pd.qcut(df[value_col], 4, labels=["Q1 (low)", "Q2", "Q3", "Q4 (high)"], duplicates="drop")
        groups = {str(lv): (q == lv) for lv in q.cat.categories}
    elif isinstance(split, str):
        groups = {str(lv): (df[split] == lv) for lv in df[split].dropna().unique()}
    else:
        groups = split

    for i, (name, mask) in enumerate(groups.items()):
        series = df.loc[mask].groupby(time_col)[value_col].agg(metric)
        kwargs = {"label": labels.get(name, name)}
        if colors:
            kwargs["color"] = colors[i % len(colors)]
        if marker:
            kwargs["marker"] = marker
        if linewidth:
            kwargs["linewidth"] = linewidth
        ax.plot(series.index, series.values, **kwargs)
    if isinstance(legend_loc, tuple):
        ax.legend(bbox_to_anchor=legend_loc)
    else:
        ax.legend(loc=legend_loc)
    if grid:
        ax.grid(axis="y", color=palette["grid"], linestyle=":", zorder=-10)
    ax.set_xlabel(time_col.replace("_", " ").title())
    ax.set_ylabel(value_col)
    brand_title(ax, title, subtitle=subtitle, n=n)
    fig.tight_layout()
    return fig, ax


def annotated_event_plot(
    df: pd.DataFrame,
    value_col: str,
    events: dict,
    time_col: str = "real_date",
    window: int = 3,
    grid: bool = False,
    ax=None,
    title: str | None = None,
    subtitle: str | None = None,
    n: int | None = None,
    color: str | None = None,
    figsize: tuple = (10, 6),
):
    """Single rolling trend line with labeled vertical event markers
    (generalizes ``crisis_awareness_plot``).

    Parameters
    ----------
    events:
        Mapping ``{x_position: "label"}`` -- vertical dashed lines with
        rotated annotations (e.g. crisis onsets).
    """
    series = df.groupby(time_col)[value_col].mean().rolling(window, min_periods=1).mean() * 100
    fig, ax, _ = resolve_ax(ax, figsize=figsize)
    ax.plot(series.index, series.values, color=color)
    top = series.max()
    for x, label in events.items():
        ax.axvline(x, color="0.4", linestyle="--", linewidth=1)
        ax.annotate(label, (x, top), rotation=90, fontsize=9, va="top", ha="right", color="0.3")
    ax.set_ylabel(f"% {value_col}")
    if grid:
        ax.grid(axis="y", color=palette["grid"], linestyle=":", zorder=-10)
    brand_title(ax, title, subtitle=subtitle, n=n)
    fig.tight_layout()
    return fig, ax
