"""Shared legend-label processing: optional wrapping / truncation.

Kept in one place so every chart exposes the same ``wrap_legend`` /
``truncate_legend`` behavior with identical semantics. Both default off.
"""

from __future__ import annotations

import textwrap


def process_labels(
    labels: list[str],
    wrap: int | None = None,
    truncate: int | None = None,
    ellipsis: str = "\u2026",
) -> list[str]:
    """Return display versions of ``labels``.

    Parameters
    ----------
    wrap:
        Wrap each label to this width (characters) across multiple lines.
        ``None`` (default) leaves labels unwrapped.
    truncate:
        Hard-truncate each label to this many characters, appending an
        ellipsis. ``None`` (default) leaves labels untruncated. Applied
        before wrapping when both are given.
    ellipsis:
        String appended to truncated labels (default "…").
    """
    out = []
    for lbl in labels:
        s = str(lbl)
        if truncate is not None and len(s) > truncate:
            s = s[: max(truncate - len(ellipsis), 0)].rstrip() + ellipsis
        if wrap is not None:
            s = "\n".join(textwrap.wrap(s, wrap)) or s
        out.append(s)
    return out


def apply_legend(ax, wrap=None, truncate=None, **legend_kwargs):
    """Draw a legend on ``ax`` with optional label wrapping/truncation.

    Passes through any matplotlib ``legend`` kwargs (loc, bbox_to_anchor,
    ncol, title, ...). ``frameon`` defaults to the theme (False) unless the
    caller overrides it.
    """
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return None
    if wrap is not None or truncate is not None:
        labels = process_labels(labels, wrap=wrap, truncate=truncate)
    return ax.legend(handles, labels, **legend_kwargs)
