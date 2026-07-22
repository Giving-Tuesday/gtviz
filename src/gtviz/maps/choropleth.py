"""FIPS / region choropleth color tables.

The original workflow colors an SVG US county map by generating a table of
``region -> hex color`` (``map_table_absolute`` / ``map_table_relative``).
:func:`choropleth_table` merges both: aggregate a value per region, map it
through a colormap either on an absolute (min/max, optionally extended)
scale or via relative quantile cutoffs, and return the color table ready to
join against SVG path ids. Leading-zero FIPS codes are preserved (the
original bug class this code guarded against).
"""

from __future__ import annotations

import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

from ..theme import spectral_cmap

__all__ = ["choropleth_table"]


def _normalize_fips(s: pd.Series) -> pd.Series:
    """Zero-pad FIPS codes to 5 chars as strings (never int-cast)."""
    return s.astype(str).str.split(".").str[0].str.zfill(5)


def choropleth_table(
    df: pd.DataFrame,
    value_col: str,
    region_col: str = "Fips",
    agg: str = "mean",
    mode: str = "absolute",
    cmap=None,
    n_colors: int = 25,
    extend_range: float = 0.3,
    cutoffs: list | None = None,
    fips: bool = True,
    min_count: int = 1,
    missing_color: str = "#FFFFFF",
) -> pd.DataFrame:
    """Aggregate a value per region and assign hex colors.

    Parameters
    ----------
    df:
        Respondent-level data with a region column.
    value_col:
        Numeric column to aggregate.
    region_col:
        Region identifier column (FIPS county codes by default).
    agg:
        Aggregation ("mean", "median", or any pandas agg).
    mode:
        ``"absolute"`` -- linear color scale between (extended) min/max;
        ``"relative"`` -- quantile or explicit ``cutoffs`` binning.
    cmap:
        Matplotlib colormap; defaults to the 25-step Spectral used in the
        original maps.
    extend_range:
        Fraction to extend the value range beyond observed min/max
        (absolute mode; the original ``extend_range_by=0.3``).
    cutoffs:
        Explicit bin edges for relative mode; defaults to quartiles.
    fips:
        Zero-pad the region column to 5-char FIPS strings.
    min_count:
        Regions with fewer responses get ``missing_color``.

    Returns
    -------
    DataFrame with columns ``[region_col, "value", "n", "color"]`` plus
    attrs ``scale_min``/``scale_max`` for building the matching scale bar.
    """
    cmap = cmap or spectral_cmap(n_colors)
    data = df[[region_col, value_col]].dropna(subset=[region_col]).copy()
    if fips:
        data[region_col] = _normalize_fips(data[region_col])

    grouped = data.groupby(region_col)[value_col].agg(["count", agg])
    grouped.columns = ["n", "value"]
    grouped = grouped.reset_index()

    valid = grouped["n"] >= min_count
    vals = grouped.loc[valid, "value"]

    if mode == "absolute":
        span = vals.max() - vals.min()
        vmin = vals.min() - span * extend_range / 2
        vmax = vals.max() + span * extend_range / 2
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        colors = [mcolors.rgb2hex(cmap(norm(v))) for v in grouped["value"]]
    elif mode == "relative":
        edges = cutoffs or list(vals.quantile([0.25, 0.5, 0.75]))
        vmin, vmax = vals.min(), vals.max()
        n_bins = len(edges) + 1
        bin_colors = [mcolors.rgb2hex(cmap(i / max(n_bins - 1, 1))) for i in range(n_bins)]
        colors = [bin_colors[int(np.searchsorted(edges, v))] for v in grouped["value"]]
    else:
        raise ValueError("mode must be 'absolute' or 'relative'")

    grouped["color"] = colors
    grouped.loc[~valid, "color"] = missing_color
    grouped.attrs["scale_min"] = float(vmin)
    grouped.attrs["scale_max"] = float(vmax)
    return grouped
