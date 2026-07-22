"""Donut (ring) charts. Port of ``donut_chart`` with fig/ax handling."""

from __future__ import annotations

from .._mpl import resolve_ax
from ..theme import palette

__all__ = ["donut"]


def donut(
    values,
    labels,
    title: str | None = None,
    colors: list | None = None,
    width: float = 0.5,
    startangle: int = 90,
    autopct: str | None = None,
    ax=None,
    figsize: tuple = (6, 6),
    **pie_kwargs,
):
    """Ring chart with clockwise segments starting at 12 o'clock.

    Original styling: wedge width 0.5, start angle 90, no percent labels
    (pass ``autopct="%1.0f%%"`` to add them).

    Returns
    -------
    (fig, ax)
    """
    fig, ax, _ = resolve_ax(ax, figsize=figsize)
    ax.pie(
        values,
        labels=labels,
        colors=colors or palette["series"],
        normalize=True,
        startangle=startangle,
        counterclock=False,
        autopct=autopct,
        wedgeprops=dict(width=width),
        **pie_kwargs,
    )
    if title:
        ax.set_title(title)
    return fig, ax
