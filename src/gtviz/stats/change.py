"""Period-over-period change computation.

Consolidates ``quarterly_change`` (+ ``_filter``, ``_formatted_report``,
``normalized_quarterly_change``, ``quarterly_change_crosstab``) into
:func:`period_change` and :func:`compare_crosstab`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .summaries import _resolve_weights


def _weighted_means(df, columns, weights):
    w = _resolve_weights(df, weights)
    return pd.Series({c: np.average(df[c].fillna(0), weights=w) * 100 for c in columns})


def period_change(
    df: pd.DataFrame,
    df_prev: pd.DataFrame,
    columns: list[str],
    weights: str | None = "auto",
    filter=None,
    filter_prev=None,
    labels: dict | None = None,
    normalize: bool = False,
) -> pd.DataFrame:
    """Weighted means for two periods plus their difference in points.

    Returns a DataFrame with columns ``current``, ``previous``, ``change``.
    ``labels`` optionally maps column names to display labels for the index.
    """
    cur = df if filter is None else df.loc[filter]
    prev = df_prev if filter_prev is None else df_prev.loc[filter_prev]
    if normalize:
        cur, prev = cur.copy(), prev.copy()
        for c in columns:
            m = max(cur[c].max(), prev[c].max())
            if m:
                cur[c], prev[c] = cur[c] / m, prev[c] / m
    out = pd.DataFrame(
        {
            "current": _weighted_means(cur, columns, weights),
            "previous": _weighted_means(prev, columns, weights),
        }
    )
    out["change"] = out["current"] - out["previous"]
    if labels:
        out.index = [labels.get(c, c) for c in out.index]
    return out.round(1)


def compare_crosstab(
    df: pd.DataFrame,
    df_prev: pd.DataFrame,
    group_col: str,
    value_col: str,
    labels: dict | None = None,
    decimals: int = 1,
) -> pd.DataFrame:
    """Group-level means for two periods with change (port of
    ``quarterly_change_crosstab``)."""
    cur = df.groupby(group_col)[value_col].mean() * 100
    prev = df_prev.groupby(group_col)[value_col].mean() * 100
    out = pd.DataFrame({"current": cur, "previous": prev})
    out["change"] = out["current"] - out["previous"]
    if labels:
        out.index = [labels.get(i, i) for i in out.index]
    return out.round(decimals)
