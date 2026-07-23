"""Venn diagrams for overlapping behaviours -- report brand style.

Defaults match the published figures: **area-proportional** circles (not
equal-size), brand set colors (steel blue / turquoise / green), percent-of-
sample region labels, bold left-aligned title with an optional gray
"n = X respondents" subtitle, and optional per-set totals under each set
label (e.g. "Gave Money\\n81%").

Consolidates ``venn_diagram_2``, ``venn_diagram_2_filter``, ``venn_diagram_3``,
``venn_diagram_3_filter`` and ``venn_diagram_volunteer`` into one :func:`venn`
(2 vs 3 sets inferred; ``filter`` replaces the ``_filter`` twins), plus
:func:`venn_from_counts` for pre-aggregated flag tables.
"""

from __future__ import annotations

import pandas as pd
from matplotlib_venn import venn2, venn3

from .._mpl import brand_title, resolve_ax
from ..theme import palette

try:  # matplotlib-venn >= 1.0: unweighted layouts via layout algorithms
    from matplotlib_venn.layout.venn2 import DefaultLayoutAlgorithm as _V2Layout
    from matplotlib_venn.layout.venn3 import DefaultLayoutAlgorithm as _V3Layout

    def _venn2_unweighted(subsets, set_labels, set_colors, alpha, ax):
        return venn2(subsets=subsets, set_labels=set_labels, set_colors=set_colors,
                     alpha=alpha, ax=ax,
                     layout_algorithm=_V2Layout(fixed_subset_sizes=(1, 1, 1)))

    def _venn3_unweighted(subsets, set_labels, set_colors, alpha, ax):
        return venn3(subsets=subsets, set_labels=set_labels, set_colors=set_colors,
                     alpha=alpha, ax=ax,
                     layout_algorithm=_V3Layout(fixed_subset_sizes=(1,) * 7))
except ImportError:  # matplotlib-venn < 1.0
    from matplotlib_venn import venn2_unweighted as _v2u
    from matplotlib_venn import venn3_unweighted as _v3u

    def _venn2_unweighted(subsets, set_labels, set_colors, alpha, ax):
        return _v2u(subsets=subsets, set_labels=set_labels, set_colors=set_colors,
                    alpha=alpha, ax=ax)

    def _venn3_unweighted(subsets, set_labels, set_colors, alpha, ax):
        return _v3u(subsets=subsets, set_labels=set_labels, set_colors=set_colors,
                    alpha=alpha, ax=ax)

__all__ = ["venn", "venn_from_counts"]


def _pct(n: float, total: float) -> str:
    return f"{n / total * 100:.0f}%" if total else "0%"


def _subset_ids(n_sets: int):
    return ["10", "01", "11"] if n_sets == 2 else ["100", "010", "110", "001", "101", "011", "111"]


def _draw(subsets, labels, set_totals, total, weighted, colors, alpha,
          as_percent, set_percentages, title, subtitle, n, ax, figsize):
    fig, ax, _ = resolve_ax(ax, figsize=figsize)
    n_sets = 2 if len(subsets) == 3 else 3
    colors = colors or palette["venn"]
    set_colors = tuple(colors[:n_sets])

    if set_percentages and total:
        labels = [f"{lbl}\n{_pct(st, total)}" for lbl, st in zip(labels, set_totals)]

    if n_sets == 2:
        v = (venn2(subsets=subsets, set_labels=labels, set_colors=set_colors,
                   alpha=alpha, ax=ax) if weighted
             else _venn2_unweighted(subsets, labels, set_colors, alpha, ax))
    else:
        v = (venn3(subsets=subsets, set_labels=labels, set_colors=set_colors,
                   alpha=alpha, ax=ax) if weighted
             else _venn3_unweighted(subsets, labels, set_colors, alpha, ax))

    if as_percent and total:
        for sid, cnt in zip(_subset_ids(n_sets), subsets):
            lbl = v.get_label_by_id(sid)
            if lbl is not None:
                lbl.set_text(_pct(cnt, total))
    brand_title(ax, title, subtitle=subtitle, n=n)
    fig.tight_layout(pad=2)
    return fig, ax


def venn(
    df: pd.DataFrame,
    columns: list[str],
    labels: list[str] | None = None,
    filter: pd.Series | None = None,
    weighted: bool = True,
    colors: list | None = None,
    alpha: float = 0.6,
    as_percent: bool = True,
    set_percentages: bool = False,
    title: str | None = None,
    subtitle: str | None = None,
    n: int | None = None,
    ax=None,
    figsize: tuple = (7, 7),
):
    """2- or 3-set venn of binary flag columns, report style.

    Parameters
    ----------
    df:
        Respondent-level data with binary (0/1) columns.
    columns:
        Two or three flag columns; set count is inferred.
    labels:
        Circle labels (defaults to the column names).
    filter:
        Optional boolean mask applied first (replaces the old ``_filter``
        function variants).
    weighted:
        Area-proportional circles -- **the report default**. Pass False for
        equal-size circles.
    colors:
        Set colors; default is the brand palette (steel blue, turquoise,
        green).
    as_percent:
        Annotate regions as percent of the (filtered) sample.
    set_percentages:
        Append each set's overall share under its label
        (e.g. ``"Gave Money\\n81%"``).
    n:
        Sample size for the gray "n = X respondents" subtitle; defaults to
        the (filtered) row count when ``subtitle``/``n`` not given -- pass
        ``n=0`` to suppress.

    Returns
    -------
    (fig, ax)
    """
    if len(columns) not in (2, 3):
        raise ValueError("venn supports exactly 2 or 3 columns")
    data = df if filter is None else df.loc[filter]
    labels = list(labels or columns)
    flags = data[columns].fillna(0).astype(int)
    total = len(flags)
    if subtitle is None and n is None:
        n = total
    if n == 0:
        n = None

    if len(columns) == 2:
        a, b = columns
        subsets = (
            int(((flags[a] == 1) & (flags[b] == 0)).sum()),
            int(((flags[a] == 0) & (flags[b] == 1)).sum()),
            int(((flags[a] == 1) & (flags[b] == 1)).sum()),
        )
    else:
        a, b, c = columns
        combos = [(1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
        subsets = tuple(
            int(((flags[a] == fa) & (flags[b] == fb) & (flags[c] == fc)).sum())
            for fa, fb, fc in combos
        )
    set_totals = [int(flags[col].sum()) for col in columns]
    return _draw(subsets, labels, set_totals, total, weighted, colors, alpha,
                 as_percent, set_percentages, title, subtitle, n, ax, figsize)


def venn_from_counts(
    subset_counts: dict,
    labels: list[str],
    weighted: bool = True,
    colors: list | None = None,
    alpha: float = 0.6,
    as_percent: bool = True,
    set_percentages: bool = False,
    title: str | None = None,
    subtitle: str | None = None,
    n: int | None = None,
    ax=None,
    figsize: tuple = (7, 7),
):
    """Venn from pre-aggregated region counts (report style).

    ``subset_counts`` maps flag tuples to counts, e.g.
    ``{(1,0,0): 120, (0,1,0): 80, (1,1,0): 40, ...}`` for three sets
    (the shape of the ``gift_venn`` Delta tables in the original export
    notebook).
    """
    n_sets = len(next(iter(subset_counts)))
    if n_sets == 2:
        combos = [(1, 0), (0, 1), (1, 1)]
    else:
        combos = [(1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
    subsets = tuple(int(subset_counts.get(cmb, 0)) for cmb in combos)
    total = sum(subsets)
    set_totals = [
        sum(cnt for cmb, cnt in subset_counts.items() if cmb[i] == 1)
        for i in range(n_sets)
    ]
    if subtitle is None and n is None:
        n = total
    if n == 0:
        n = None
    return _draw(subsets, list(labels), set_totals, total, weighted, colors, alpha,
                 as_percent, set_percentages, title, subtitle, n, ax, figsize)
