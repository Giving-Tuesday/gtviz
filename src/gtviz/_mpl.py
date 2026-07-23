"""Internal matplotlib helpers shared by all chart modules."""

from __future__ import annotations

import matplotlib.pyplot as plt


def resolve_ax(ax=None, figsize=None):
    """Return ``(fig, ax, created)``; create a new figure if ``ax`` is None."""
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        return fig, ax, True
    return ax.figure, ax, False


def brand_title(ax, title=None, subtitle=None, n=None):
    """Report-style header: bold left-aligned title with an optional gray
    subtitle line (pass ``subtitle=`` text or ``n=`` for
    "n = 5,387 respondents")."""
    sub = subtitle or (f"n = {n:,} respondents" if n else None)
    if title:
        ax.set_title(title, loc="left", fontweight="bold",
                     pad=26 if sub else 10)
    if sub:
        ax.text(0, 1.03, sub, transform=ax.transAxes, fontsize=10,
                color="#666666", ha="left", va="bottom")
    return ax


def finish(fig, save=None, show=False, name=None, formats=("png",)):
    """Common tail for chart functions: optional save + optional show."""
    if save:
        from . import io

        io.save(fig, name or (save if isinstance(save, str) else "figure"), formats=formats)
    if show:
        plt.show()
    return fig
