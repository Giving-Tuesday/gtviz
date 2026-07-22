"""Internal matplotlib helpers shared by all chart modules."""

from __future__ import annotations

import matplotlib.pyplot as plt


def resolve_ax(ax=None, figsize=None):
    """Return ``(fig, ax, created)``; create a new figure if ``ax`` is None."""
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        return fig, ax, True
    return ax.figure, ax, False


def finish(fig, save=None, show=False, name=None, formats=("png",)):
    """Common tail for chart functions: optional save + optional show."""
    if save:
        from . import io

        io.save(fig, name or (save if isinstance(save, str) else "figure"), formats=formats)
    if show:
        plt.show()
    return fig
