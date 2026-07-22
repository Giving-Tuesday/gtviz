"""Scale-bar legends for choropleth maps.

Consolidates all four variants (``map_scale_min_max_v1``, the parametrized
``map_scale_min_max``, and the relative ``map_scale``) into one
:func:`scale_bar`. Pass ``cutoffs`` for the relative/binned case.
"""

from __future__ import annotations

import matplotlib.colors as mcolors
import matplotlib.patches as patches

from .._mpl import resolve_ax
from ..theme import spectral_cmap

__all__ = ["scale_bar"]


def scale_bar(
    scale_min: float,
    scale_max: float,
    caption: str = "",
    cmap=None,
    n_colors: int = 25,
    cutoffs: list | None = None,
    fontsize: int = 5,
    flip_label_shades: bool = False,
    ax=None,
):
    """Horizontal color scale bar with per-swatch value labels.

    Parameters
    ----------
    scale_min, scale_max:
        Value range represented by the bar ends (use
        ``choropleth_table(...).attrs`` values to match a map).
    cutoffs:
        If given, draw one swatch per bin labeled with the cutoff values
        (relative mode) instead of a linear ramp.
    flip_label_shades:
        Use white labels on dark swatches.

    Returns
    -------
    (fig, ax)
    """
    fig, ax, _ = resolve_ax(ax, figsize=(8, 0.4))
    ax.set_xlim(0, 101)
    ax.set_ylim(0, 1.1)
    ax.axis("off")

    if cutoffs:
        n = len(cutoffs) + 1
        cmap = cmap or spectral_cmap(n)
        colors = [cmap(i / max(n - 1, 1)) for i in range(n)]
        labels = [f"<{cutoffs[0]:g}"] + [f"{c:g}" for c in cutoffs]
    else:
        cmap = cmap or spectral_cmap(n_colors)
        colors = [cmap(i / (n_colors - 1)) for i in range(n_colors)]
        incr = (scale_max - scale_min) / len(colors)
        labels = [f"{scale_min + incr * (i + 1):.0f}" for i in range(len(colors))]

    x, y = 0.05, 0.05
    width = 100 / len(colors)
    for i, rgba in enumerate(colors):
        hexcode = mcolors.rgb2hex(rgba)
        rect = patches.Rectangle((x, y), width, 1, linewidth=0.2, edgecolor="black", facecolor=hexcode)
        ax.add_patch(rect)
        lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
        txtcolor = "white" if (flip_label_shades and lum < 0.5) else "black"
        ax.text(x + width / 2, y + 0.5, labels[i], ha="center", va="center",
                fontsize=fontsize, color=txtcolor)
        x += width

    if caption:
        ax.text(0, 1.25, caption, fontsize=8)
    return fig, ax
