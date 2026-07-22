"""Named aggregators.

Replaces the anonymous ``round_mean``/``norm_mean*``/``above10000`` lambdas
that were copy-pasted across three notebooks in the original repo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def round_mean(x, decimals: int = 0, exclude: float | None = None) -> float:
    """Rounded mean, optionally excluding a sentinel value (e.g. ``-1``)."""
    x = pd.Series(x)
    if exclude is not None:
        x = x[x != exclude]
    return float(np.round(x.mean(), decimals))


def norm_mean(x, scale_max: float = 5.0) -> float:
    """Mean expressed as percent of a scale maximum (Likert 0-N to 0-100)."""
    return float(pd.Series(x).mean() / scale_max * 100)


def share_above(x, threshold: float) -> float:
    """Percent of values strictly above ``threshold`` (0-100)."""
    x = pd.Series(x).dropna()
    if len(x) == 0:
        return float("nan")
    return float((x > threshold).mean() * 100)


def binned_mean(x, midpoints: dict) -> float:
    """Approximate mean of a binned/categorical variable via bin midpoints.

    Generalizes the original ``avg_don_approx`` / ``avg_age_approx``: map each
    category code to a representative value, then average.

    Parameters
    ----------
    x:
        Series of category codes/labels.
    midpoints:
        Mapping ``{code: representative_value}``. Codes missing from the
        mapping are dropped.
    """
    mapped = pd.Series(x).map(midpoints).dropna()
    return float(mapped.mean()) if len(mapped) else float("nan")


def weighted_mean(values, weights) -> float:
    """Weighted mean handling NaN in values (weights re-normalized)."""
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    mask = ~np.isnan(v)
    if mask.sum() == 0:
        return float("nan")
    return float(np.average(v[mask], weights=w[mask]))
