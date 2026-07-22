"""Venn diagrams for overlapping behaviours.

Consolidates ``venn_diagram_2``, ``venn_diagram_2_filter``, ``venn_diagram_3``,
``venn_diagram_3_filter`` and ``venn_diagram_volunteer`` into one :func:`venn`
(2 vs 3 sets inferred from the number of columns; ``filter`` replaces the
``_filter`` twins), plus :func:`venn_from_counts` for pre-aggregated flag
tables (the ``0_mode_viz_export`` Delta-table workflow).
"""

from __future__ import annotations

import pandas as pd
from matplotlib_venn import venn2, venn3

try:  # matplotlib-venn >= 1.0: unweighted layouts via layout algorithms
    from matplotlib_venn.layout.venn2 import DefaultLayoutAlgorithm as _V2Layout
    from matplotlib_venn.layout.venn3 import DefaultLayoutAlgorithm as _V3Layout

    def _venn2_unweighted(subsets, set_labels, ax):
        return venn2(subsets=subsets, set_labels=set_labels, ax=ax,
                     layout_algorithm=_V2Layout(fixed_subset_sizes=(1, 1, 1)))

    def _venn3_unweighted(subsets, set_labels, ax):
        return venn3(subsets=subsets, set_labels=set_labels, ax=ax,
                     layout_algorithm=_V3Layout(fixed_subset_sizes=(1,) * 7))
except ImportError:  # matplotlib-venn < 1.0
    from matplotlib_venn import venn2_unweighted as _v2u
    from matplotlib_venn import venn3_unweighted as _v3u

    def _venn2_unweighted(subsets, set_labels, ax):
        return _v2u(subsets=subsets, set_labels=set_labels, ax=ax)

    def _venn3_unweighted(subsets, set_labels, ax):
        return _v3u(subsets=subsets, set_labels=set_labels, ax=ax)

from .._mpl import resolve_ax

__all__ = ["venn", "venn_from_counts"]


def _pct(n: float, total: float) -> str:
    return f"{n / total * 100:.0f}%" if total else "0%"


def venn(
    df: pd.DataFrame,
    columns: list[str],
    labels: list[str] | None = None,
    filter: pd.Series | None = None,
    weighted: bool = False,
    as_percent: bool = True,
    title: str | None = None,
    ax=None,
    figsize: tuple = (7, 7),
):
    """2- or 3-set venn of binary flag columns.

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
        Area-proportional circles (True) or equal-size (False, the report
        default).
    as_percent:
        Annotate regions as percent of the filtered sample instead of counts.

    Returns
    -------
    (fig, ax)
    """
    if len(columns) not in (2, 3):
        raise ValueError("venn supports exactly 2 or 3 columns")
    data = df if filter is None else df.loc[filter]
    labels = labels or columns
    flags = data[columns].fillna(0).astype(int)
    total = len(flags)

    fig, ax, _ = resolve_ax(ax, figsize=figsize)
    if len(columns) == 2:
        a, b = columns
        subsets = (
            int(((flags[a] == 1) & (flags[b] == 0)).sum()),
            int(((flags[a] == 0) & (flags[b] == 1)).sum()),
            int(((flags[a] == 1) & (flags[b] == 1)).sum()),
        )
        v = (venn2(subsets=subsets, set_labels=labels, ax=ax) if weighted
             else _venn2_unweighted(subsets, labels, ax))
    else:
        a, b, c = columns
        combos = [(1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
        subsets = tuple(
            int(((flags[a] == fa) & (flags[b] == fb) & (flags[c] == fc)).sum())
            for fa, fb, fc in combos
        )
        v = (venn3(subsets=subsets, set_labels=labels, ax=ax) if weighted
             else _venn3_unweighted(subsets, labels, ax))

    if as_percent and total:
        for sid, n in zip(_subset_ids(len(columns)), subsets):
            lbl = v.get_label_by_id(sid)
            if lbl is not None:
                lbl.set_text(_pct(n, total))
    if title:
        ax.set_title(title, fontsize=20, pad=30)
    fig.tight_layout(pad=5)
    return fig, ax


def _subset_ids(n_sets: int):
    return ["10", "01", "11"] if n_sets == 2 else ["100", "010", "110", "001", "101", "011", "111"]


def venn_from_counts(
    subset_counts: dict,
    labels: list[str],
    title: str | None = None,
    weighted: bool = False,
    as_percent: bool = True,
    ax=None,
    figsize: tuple = (7, 7),
):
    """Venn from pre-aggregated region counts.

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
    fig, ax, _ = resolve_ax(ax, figsize=figsize)
    if n_sets == 2:
        v = (venn2(subsets=subsets, set_labels=labels, ax=ax) if weighted
             else _venn2_unweighted(subsets, labels, ax))
    else:
        v = (venn3(subsets=subsets, set_labels=labels, ax=ax) if weighted
             else _venn3_unweighted(subsets, labels, ax))
    if as_percent and total:
        for sid, n in zip(_subset_ids(n_sets), subsets):
            lbl = v.get_label_by_id(sid)
            if lbl is not None:
                lbl.set_text(_pct(n, total))
    if title:
        ax.set_title(title, fontsize=20, pad=30)
    fig.tight_layout(pad=5)
    return fig, ax
