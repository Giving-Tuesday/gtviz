"""Waffle charts (optional extra: ``pip install gtviz[waffle]``) -- report
brand style: tab10 category sequence (blue, red, purple, orange, ...),
vertical legend outside the right edge with values in the labels, bold
left-aligned title. Replaces the copy-pasted aid-flow waffle notebooks.
"""

from __future__ import annotations

__all__ = ["waffle"]


def waffle(
    values: dict,
    rows: int = 20,
    block_value: float | None = None,
    colors: list | None = None,
    show_values: bool = True,
    value_format: str = "{k} ({v:g})",
    title: str | None = None,
    figsize: tuple = (12, 5),
    **kwargs,
):
    """Waffle chart from ``{label: value}`` (report style).

    Requires ``pywaffle``; raises a clear ImportError otherwise.

    Parameters
    ----------
    values:
        ``{category: amount}`` in display order.
    rows:
        Grid height in blocks (the aid-flows figure uses ~20).
    block_value:
        Amount represented by one block (e.g. ``2`` for "1 box = $2B" when
        values are in billions); values are divided by it. None auto-scales.
    show_values:
        Append each category's raw value to its legend label via
        ``value_format`` (``{k}`` = label, ``{v}`` = value).
    colors:
        Defaults to the brand tab10 sequence
        (``theme.palette["waffle"]``).

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

    labels = (
        [value_format.format(k=k, v=v) for k, v in values.items()]
        if show_values else list(values.keys())
    )
    plot_values = (
        {k: v / block_value for k, v in values.items()} if block_value else dict(values)
    )
    fig = plt.figure(
        FigureClass=Waffle,
        rows=rows,
        values=plot_values,
        labels=labels,
        colors=(colors or palette["waffle"])[: len(values)],
        title={"label": title, "loc": "left", "fontweight": "bold"} if title else None,
        legend={"loc": "center left", "bbox_to_anchor": (1.02, 0.5), "frameon": False},
        figsize=figsize,
        **kwargs,
    )
    return fig


