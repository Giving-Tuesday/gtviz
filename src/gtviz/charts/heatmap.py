"""Weighted group heatmaps.

Consolidates the three hard-coded ``heatmaps``/``heatmaps_q4`` variants into
one generic weighted-groupby heatmap. Implemented with plain matplotlib (the
originals used seaborn; dropping the dependency).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .._mpl import resolve_ax
from ..config import options

__all__ = ["weighted_heatmap"]


def weighted_heatmap(
    df: pd.DataFrame,
    group_col: str,
    value_cols: list[str],
    weights: str | None = "auto",
    labels: dict | None = None,
    group_labels: dict | None = None,
    as_percent: bool = True,
    annot: bool = True,
    cmap: str = "YlGnBu",
    ax=None,
    title: str | None = None,
):
    """Heatmap of weighted means: rows = groups, columns = metrics.

    Returns
    -------
    (fig, ax); the underlying matrix is at ``ax._gtviz_data``.
    """
    labels = labels or {}
    group_labels = group_labels or {}
    wcol = options.weight_col if weights == "auto" else weights

    def wmean(sub: pd.DataFrame) -> pd.Series:
        w = sub[wcol] if (wcol and wcol in sub) else pd.Series(1.0, index=sub.index)
        return pd.Series({c: np.average(sub[c].fillna(0), weights=w) for c in value_cols})

    mat = df.groupby(group_col).apply(wmean, include_groups=False)
    if as_percent:
        mat = mat * 100

    fig, ax, _ = resolve_ax(ax, figsize=(1.1 * len(value_cols) + 3, 0.6 * len(mat) + 2))
    im = ax.imshow(mat.values, aspect="auto", cmap=cmap)
    ax.set_xticks(range(len(value_cols)))
    ax.set_xticklabels([labels.get(c, c) for c in value_cols], rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(mat)))
    ax.set_yticklabels([group_labels.get(i, i) for i in mat.index], fontsize=9)
    if annot:
        vmid = (np.nanmax(mat.values) + np.nanmin(mat.values)) / 2
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]):
                val = mat.values[i, j]
                ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=8,
                        color="white" if val > vmid else "black")
    fig.colorbar(im, ax=ax, shrink=0.8)
    if title:
        ax.set_title(title)
    ax._gtviz_data = mat
    fig.tight_layout()
    return fig, ax
