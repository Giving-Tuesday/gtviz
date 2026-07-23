"""Weekly / rolling weighted summaries.

Consolidates ``weekly_summary``, ``weekly_summary_filter``,
``weekly_summary_no_rolling``, and ``normalized_weekly_summary`` from the
original ``report_functions.py`` into one function.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import options


def _resolve_weights(df: pd.DataFrame, weights) -> pd.Series:
    if weights is None:
        return pd.Series(1.0, index=df.index)
    if isinstance(weights, str):
        if weights == "auto":
            # "auto" = use the configured weight column when present,
            # otherwise fall back to unweighted (demo/unweighted frames).
            col = options.weight_col
            if col not in df.columns:
                return pd.Series(1.0, index=df.index)
            return df[col]
        return df[weights]  # explicit column name: missing is an error
    return pd.Series(weights, index=df.index)


def rolling_summary(
    df: pd.DataFrame,
    columns: list[str],
    time_col: str = "collection_week",
    window: int = 3,
    weights: str | None = "auto",
    filter: pd.Series | None = None,
    normalize: bool = False,
    rolling: bool = True,
    as_percent: bool = True,
) -> pd.DataFrame:
    """Weighted per-period means with an optional rolling window.

    Parameters
    ----------
    df:
        Respondent-level data.
    columns:
        Metric columns (binary flags or scales).
    time_col:
        Period column to group by (week number, date, etc.).
    window:
        Rolling window width in periods; ignored if ``rolling=False``.
    weights:
        ``"auto"`` (use :data:`gtviz.config.options.weight_col`), a column
        name, an array, or ``None`` for unweighted.
    filter:
        Optional boolean mask applied before summarizing (replaces the old
        ``*_filter`` variants).
    normalize:
        Divide each column by its own maximum first (Likert scales to 0-1).
    as_percent:
        Multiply results by 100.

    Returns
    -------
    DataFrame indexed by period with one column per metric.
    """
    data = df if filter is None else df.loc[filter]
    w = _resolve_weights(data, weights)
    if normalize:
        data = data.copy()
        for c in columns:
            m = data[c].max()
            if m:
                data[c] = data[c] / m

    def wmean(group: pd.DataFrame) -> pd.Series:
        gw = w.loc[group.index]
        return pd.Series(
            {c: np.average(group[c].fillna(0), weights=gw) for c in columns}
        )

    out = data.groupby(time_col)[columns].apply(wmean)
    if rolling:
        out = out.rolling(window=window, min_periods=1).mean()
    return out * 100 if as_percent else out
