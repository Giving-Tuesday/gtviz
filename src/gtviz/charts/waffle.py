"""Waffle charts (optional extra: ``pip install gtviz[waffle]``).

Thin wrapper over pywaffle, replacing the copy-pasted aid-flow waffle
notebooks.
"""

from __future__ import annotations

__all__ = ["waffle"]


def waffle(
    values: dict,
    rows: int = 10,
    colors: list | None = None,
    title: str | None = None,
    figsize: tuple = (8, 4),
    **kwargs,
):
    """Waffle chart from ``{label: value}``.

    Requires ``pywaffle``; raises a clear ImportError otherwise.

    Returns
    -------
    matplotlib Figure
    """
    try:
        from pywaffle import Waffle
    except ImportError as e:  # pragma: no cover
        raise ImportError("waffle charts require: pip install gtviz[waffle]") from e
    import matplotlib.pyplot as plt

    from ..theme import palette

    fig = plt.figure(
        FigureClass=Waffle,
        rows=rows,
        values=values,
        colors=colors or palette["series"][: len(values)],
        title={"label": title, "loc": "left"} if title else None,
        legend={"loc": "lower left", "bbox_to_anchor": (0, -0.3), "ncol": min(len(values), 3)},
        figsize=figsize,
        **kwargs,
    )
    return fig
