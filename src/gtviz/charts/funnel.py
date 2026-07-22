"""Funnel chart: proportion of the sample remaining at each stage.

Port of ``funnel_chart`` with the fixed 3-unit y-geometry generalized to any
number of stages.
"""

from __future__ import annotations

import numpy as np

from .._mpl import resolve_ax
from ..theme import palette

__all__ = ["funnel"]


def funnel(
    proportions,
    labels,
    baseline_label: str = "Everyone",
    color: str | None = None,
    title: str | None = None,
    ax=None,
    figsize: tuple = (7, None),
):
    """Symmetric funnel: bar half-width proportional to each stage's share.

    Parameters
    ----------
    proportions:
        Stage shares in 0-1 (a leading 1.0 "Everyone" band is added
        automatically).
    labels:
        Stage labels matching ``proportions``.

    Returns
    -------
    (fig, ax)
    """
    props = [1.0] + list(proportions)
    names = [baseline_label] + list(labels)
    color = color or palette["accent"]
    n = len(props)
    height = figsize[1] or (0.9 * n + 1)
    fig, ax, _ = resolve_ax(ax, figsize=(figsize[0], height))

    width = 11
    band_h, gap = 2.8, 0.2  # original: bands 16..18.8, step 3
    for i, p in enumerate(props):
        y0 = (n - 1 - i) * (band_h + gap)
        ax.fill_betweenx(y=[y0, y0 + band_h], x1=[-width * p] * 2, x2=[width * p] * 2, color=color)
        ax.annotate(f"{p * 100:.0f}%", (0, y0 + band_h / 2), color="white",
                    ha="center", va="center", fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([(n - 1 - i) * (band_h + gap) + band_h / 2 for i in range(n)])
    ax.set_yticklabels(names)
    ax.set_xlim(-width * 1.05, width * 1.05)
    for spine in ("top", "right", "bottom"):
        ax.spines[spine].set_visible(False)
    if title:
        ax.set_title(title, fontsize=12)
    fig.tight_layout()
    return fig, ax


def funnel_from_columns(df, columns, labels=None, weights=None, **kwargs):
    """Convenience: funnel from binary columns (weighted shares)."""
    w = df[weights] if isinstance(weights, str) else (weights if weights is not None else np.ones(len(df)))
    props = [float(np.average(df[c].fillna(0), weights=w)) for c in columns]
    return funnel(props, labels or columns, **kwargs)
