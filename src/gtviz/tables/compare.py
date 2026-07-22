"""Period comparison tables.

Consolidates ``quarter_year_compare``, ``quarterly_change_formatted_report``,
``quarter_compare``/``year_compare``/``compare_table`` (archive) and
``pivot_attitudes_giving_money`` into two functions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..stats.summaries import _resolve_weights
from ..theme import palette


def compare_periods(
    df_now: pd.DataFrame,
    df_prev: pd.DataFrame,
    columns: list[str],
    df_yoy: pd.DataFrame | None = None,
    labels: dict | None = None,
    weights: str | None = "auto",
    absolute: bool = False,
    style: bool = True,
    period_names: tuple = ("Current", "Last quarter", "Last year"),
    highlight_threshold: float = 3.0,
):
    """QoQ (and optionally YoY) comparison of weighted column means.

    Parameters
    ----------
    df_now, df_prev, df_yoy:
        Respondent-level data for the current period, previous period, and
        (optionally) the same period one year earlier.
    columns:
        Metric columns to compare.
    absolute:
        If True, report absolute point values for all periods; otherwise the
        previous/YoY columns show the change vs current.
    style:
        Return a pandas ``Styler`` with green/red change highlighting; if
        False return the plain DataFrame.
    highlight_threshold:
        Point change where highlighting starts (styled output only).

    Returns
    -------
    DataFrame or pandas Styler.
    """

    def wmeans(df):
        w = _resolve_weights(df, weights)
        return pd.Series({c: np.average(df[c].fillna(0), weights=w) * 100 for c in columns})

    now, prev = wmeans(df_now), wmeans(df_prev)
    data = {period_names[0]: now}
    if absolute:
        data[period_names[1]] = prev
        if df_yoy is not None:
            data[period_names[2]] = wmeans(df_yoy)
    else:
        data[f"vs {period_names[1]}"] = now - prev
        if df_yoy is not None:
            data[f"vs {period_names[2]}"] = now - wmeans(df_yoy)
    out = pd.DataFrame(data).round(1)
    if labels:
        out.index = [labels.get(i, i) for i in out.index]
    if not style:
        return out

    change_cols = [c for c in out.columns if c.startswith("vs ")] if not absolute else []

    def _highlight(v):
        if v > highlight_threshold:
            return f"background-color: {palette['high']}"
        if v < -highlight_threshold:
            return f"background-color: {palette['low']}"
        return ""

    styler = out.style.format("{:.1f}")
    if change_cols:
        styler = styler.map(_highlight, subset=change_cols)
    return styler


def pivot_change_table(
    df_now: pd.DataFrame,
    df_prev: pd.DataFrame,
    index: str,
    values: str,
    index_labels: dict | None = None,
    agg: str = "mean",
    as_percent: bool = True,
) -> pd.DataFrame:
    """Grouped pivot with change column (generalizes the hard-coded
    ``pivot_attitudes_giving_money`` / ``quarterly_change_attitudes``).
    """
    mult = 100 if as_percent else 1
    cur = df_now.groupby(index)[values].agg(agg) * mult
    prev = df_prev.groupby(index)[values].agg(agg) * mult
    out = pd.DataFrame({"current": cur, "previous": prev})
    out["change"] = out["current"] - out["previous"]
    if index_labels:
        out.index = [index_labels.get(i, i) for i in out.index]
    return out.round(1)
