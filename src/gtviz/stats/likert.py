"""Likert scale utilities: normalization and label decoding."""

from __future__ import annotations

import pandas as pd


def normalize_likert(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    scale_max: float | None = None,
) -> pd.DataFrame:
    """Normalize Likert columns to 0-1 (each column divided by its max, or a
    provided ``scale_max``). Returns a copy with the same column names.
    """
    out = df.copy()
    columns = columns or list(out.columns)
    for c in columns:
        m = scale_max if scale_max is not None else out[c].max()
        out[c] = out[c] / m if m else out[c]
    return out


def decode_likert(
    df: pd.DataFrame,
    column: str,
    labels: dict,
    split_by: str | None = None,
    normalize: bool = True,
) -> pd.DataFrame:
    """Distribution of a coded Likert column with human-readable labels.

    Port of the notebook ``decode_likert``/``decode_demog`` helpers: value
    counts (optionally split by a grouping column), relabeled via ``labels``.

    Returns
    -------
    DataFrame with labeled index; columns are groups if ``split_by`` given,
    else a single ``share``/``count`` column.
    """
    if split_by:
        out = pd.crosstab(df[column], df[split_by], normalize="columns" if normalize else False)
    else:
        vc = df[column].value_counts(normalize=normalize).sort_index()
        out = vc.to_frame("share" if normalize else "count")
    out.index = [labels.get(i, i) for i in out.index]
    return (out * 100).round(1) if normalize else out
