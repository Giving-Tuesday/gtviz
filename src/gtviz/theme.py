"""Themes and palettes.

Two named rcParams profiles ported from the original ``report_params.py``:

- ``"report"`` -- the GivingPulse quarterly-report defaults (300 dpi exports,
  14pt fonts, 16pt titles).
- ``"publication"`` -- the spineless, tick-less style used for external
  publications (originally the commented-out "FLORIDA" block).

Palette tokens used across tables and charts are exposed in :data:`palette`.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

#: Named color tokens used across gtviz (charts, HTML tables, maps).
palette = {
    "accent": "#4e79a7",   # bar-fill blue in HTML tables (original CSS)
    "high": "#dcfcd9",     # above-average cell shading
    "low": "#fae8eb",      # below-average cell shading
    "zebra": "#f5f5f5",    # alternate row shading
    "grid": "0.8",         # dotted y-grid + tick color in dot plots
    # dot-plot wrapper series (original order; gray leads for "Everyone")
    "series": ["tab:grey", "tab:blue", "tab:olive", "tab:orange",
               "tab:green", "tab:red", "tab:purple"],
    # split-line series (original; light gray leads for "Everyone")
    "split_series": ["#E5E5E5", "tab:red", "tab:olive", "tab:blue",
                     "tab:green", "tab:purple"],
    # 4-point Likert answer colors, low->high (original show_belonging)
    "likert4": ["tab:red", "tab:orange", "tab:olive", "tab:green"],
    # stacked pew/stress bars (original)
    "stacked3": ["tab:blue", "tab:olive", "tab:red"],
    # 5-band 100%-stacked scale, low->high (report country/civic-intent bands)
    "bands5": ["tab:red", "tab:orange", "tab:olive", "tab:green", "tab:blue"],
    # venn set colors: Money steel-blue, Items turquoise, Volunteering green
    "venn": ["#4e79a7", "#45c5d6", "#a5cc51"],
    # waffle category sequence (report aid-flows order)
    "waffle": ["tab:blue", "tab:red", "tab:purple", "tab:orange", "tab:green",
               "tab:cyan", "tab:brown", "tab:gray", "tab:pink"],
    "subtitle": "#666666",   # gray "n = X respondents" subtitle text
}

_PROFILES = {
    "report": {
        "figure.dpi": 300,   # original report_params.py value
        "savefig.dpi": 300,
        "savefig.transparent": False,
        "font.weight": "normal",
        "axes.labelweight": "normal",
        "font.size": 14,
        "legend.fontsize": 14,
        "axes.titlesize": 16,
        # brand look from the published reports:
        "axes.titlelocation": "left",
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "lines.linewidth": 2.5,
        "legend.frameon": False,
    },
    "publication": {
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "axes.titleweight": "bold",
        "axes.titlepad": 15,
        "axes.titlesize": 16,
        "axes.labelsize": 14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "axes.spines.left": False,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.spines.bottom": False,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "xtick.major.pad": 10,
        "ytick.major.pad": 10,
    },
}


def use(profile: str = "report", font: str | None = None) -> None:
    """Activate a named rcParams profile (``"report"`` or ``"publication"``).

    Parameters
    ----------
    font:
        Brand font family (e.g. ``"Neutraface Text"``, the original
        publication font). The font must already be installed/registered
        with matplotlib; see the theming guide.
    """
    if profile not in _PROFILES:
        raise KeyError(f"Unknown theme {profile!r}; choose from {sorted(_PROFILES)}")
    mpl.rcParams.update(_PROFILES[profile])
    if font:
        mpl.rcParams["font.family"] = font


def spectral_cmap(n_colors: int = 25) -> ListedColormap:
    """The N-step Spectral colormap used by choropleth maps and scale bars."""
    raw = plt.get_cmap("Spectral")
    return ListedColormap(raw(np.linspace(0, 1, n_colors)))
