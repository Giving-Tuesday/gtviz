"""Weekly / rolling weighted summaries.

Consolidates ``weekly_summary``, ``weekly_summary_filter``,
``weekly_summary_no_rolling``, and ``normalized_weekly_summary`` from the
original ``report_functions.py`` into one function.

``rolling_summary`` now also covers two things that used to live in caller
notebooks:

* **Per-group panels** (``group_col=``) -- one column per group value for a
  single metric (or a ``(group, metric)`` MultiIndex for several), so callers
  no longer hand-loop the function once per subgroup.
* **Pooled rolling** (``pooled=True``) -- sum the weighted numerator and the
  weight denominator across the window, then divide, instead of averaging the
  per-period means. This down-weights thin periods and is the more robust
  choice for sparse subgroups.

Both are opt-in; the default call is byte-for-byte unchanged.
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


def _summary_core(
    data: pd.DataFrame,
    w: pd.Series,
    columns: list[str],
    time_col: str,
    window: int,
    rolling: bool,
    pooled: bool,
    as_percent: bool,
) -> pd.DataFrame:
    """Per-period weighted summary for a single (already-filtered) population.

    ``pooled=False`` reproduces the historical behaviour exactly: weighted mean
    per period, then a plain rolling mean of those per-period means. With
    ``pooled=True`` the weighted numerator and the weight denominator are summed
    across the window first and then divided, so periods contribute in
    proportion to their (weighted) sample size.
    """
    if pooled:
        num = data[columns].fillna(0).mul(w, axis=0).groupby(data[time_col]).sum()
        den = w.groupby(data[time_col]).sum()
        if rolling:
            num = num.rolling(window=window, min_periods=1).sum()
            den = den.rolling(window=window, min_periods=1).sum()
        out = num.div(den, axis=0)
    else:
        def wmean(group: pd.DataFrame) -> pd.Series:
            gw = w.loc[group.index]
            return pd.Series(
                {c: np.average(group[c].fillna(0), weights=gw) for c in columns}
            )

        out = data.groupby(time_col)[columns].apply(wmean)
        if rolling:
            out = out.rolling(window=window, min_periods=1).mean()
    return out * 100 if as_percent else out


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
    group_col: str | None = None,
    pooled: bool = False,
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
        Rolling window width in periods; ignored if ``rolling=False``. Any
        width >= 1 is accepted (1 is a no-op; e.g. 8 for an 8-week average).
    weights:
        ``"auto"`` (use :data:`gtviz.config.options.weight_col`), a column
        name, an array, or ``None`` for unweighted.
    filter:
        Optional boolean mask applied before summarizing (replaces the old
        ``*_filter`` variants).
    normalize:
        Divide each column by its own maximum first (Likert scales to 0-1).
        Applied to the whole (filtered) frame before any grouping.
    rolling:
        Apply the rolling window. When ``False`` the result is the plain
        per-period weighted mean.
    as_percent:
        Multiply results by 100.
    group_col:
        Optional column to split on. When given, the summary is computed
        independently for each observed group and the results are combined:
        for a single ``columns`` entry the result is ``[period x group]``; for
        several, a ``(group, metric)`` column MultiIndex. Empty categories are
        skipped (``observed=True``), so a categorical with unused levels is
        safe. Leaves the default (``group_col=None``) path untouched.
    pooled:
        Rolling method. ``False`` (default) averages the per-period weighted
        means over the window; ``True`` sums the weighted numerator and the
        weight denominator over the window and divides, weighting periods by
        their sample size (more robust for sparse subgroups). Identical to the
        default when every period has the same weight total.

    Returns
    -------
    DataFrame indexed by period. Columns are the metrics (default), the group
    values (``group_col`` set, single metric), or a ``(group, metric)``
    MultiIndex (``group_col`` set, several metrics).

    Notes
    -----
    Rolling is applied over the *periods present* for each series (a gap in
    ``time_col`` is skipped, not treated as a zero week); reindex ``df`` to a
    complete period grid beforehand if you need strictly calendar-contiguous
    windows.
    """
    data = df if filter is None else df.loc[filter]
    w = _resolve_weights(data, weights)
    if normalize:
        data = data.copy()
        for c in columns:
            m = data[c].max()
            if m:
                data[c] = data[c] / m

    if group_col is None:
        return _summary_core(data, w, columns, time_col, window, rolling, pooled, as_percent)

    frames = {
        g: _summary_core(data.loc[idx], w.loc[idx], columns, time_col,
                         window, rolling, pooled, as_percent)
        for g, idx in data.groupby(group_col, observed=True).groups.items()
    }
    if len(columns) == 1:
        col = columns[0]
        out = pd.DataFrame({g: f[col] for g, f in frames.items()})
        out.columns.name = group_col
    else:
        out = pd.concat(frames, axis=1)
        out.columns = out.columns.set_names([group_col, None])
    return out.sort_index()
