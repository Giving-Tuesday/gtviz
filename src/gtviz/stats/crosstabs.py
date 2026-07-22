"""Crosstabs, subgroup summaries, filters, and chi-squared testing."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from .summaries import _resolve_weights


def build_filter(df: pd.DataFrame, spec: dict) -> pd.Series:
    """Build a boolean mask from ``{column: value_or_list}`` (port of
    ``demographic_filter``). Lists mean "isin"; scalars mean equality."""
    mask = pd.Series(True, index=df.index)
    for col, val in spec.items():
        mask &= df[col].isin(val) if isinstance(val, (list, tuple, set)) else (df[col] == val)
    return mask


def subgroup_summary(
    df: pd.DataFrame,
    split_col: str,
    columns: list[str],
    weights: str | None = "auto",
    include_all: bool = True,
    as_percent: bool = True,
) -> pd.DataFrame:
    """Weighted means of ``columns`` per level of ``split_col``
    (port of ``demo_subgroup_summary``). Adds an ``Everyone`` row when
    ``include_all``.
    """
    mult = 100 if as_percent else 1

    def wmean(sub: pd.DataFrame) -> pd.Series:
        w = _resolve_weights(sub, weights)
        return pd.Series({c: np.average(sub[c].fillna(0), weights=w) * mult for c in columns})

    out = df.groupby(split_col).apply(wmean, include_groups=False)
    if include_all:
        out.loc["Everyone"] = wmean(df)
    return out.round(1)


def chi_squared_matrix(
    df: pd.DataFrame,
    var: str,
    others: list[str],
    alpha: float = 0.05,
    labels: dict | None = None,
    full: bool = False,
) -> pd.DataFrame:
    """Chi-squared independence tests of ``var`` against each of ``others``
    (port of ``chi_squared_tests``).

    Returns one row per tested variable with ``chi2``, ``p``, ``dof``, and
    ``significant`` (p < alpha). With ``full=True`` also includes expected-vs-
    observed max deviation.
    """
    rows = []
    for other in others:
        tab = pd.crosstab(df[var], df[other])
        if tab.size == 0 or min(tab.shape) < 2:
            rows.append({"variable": other, "chi2": np.nan, "p": np.nan, "dof": 0, "significant": False})
            continue
        chi2, p, dof, expected = chi2_contingency(tab)
        row = {"variable": other, "chi2": round(chi2, 2), "p": round(p, 4), "dof": dof,
               "significant": p < alpha}
        if full:
            row["max_abs_dev"] = float(np.abs(tab.values - expected).max())
        rows.append(row)
    out = pd.DataFrame(rows).set_index("variable")
    if labels:
        out.index = [labels.get(i, i) for i in out.index]
    return out
