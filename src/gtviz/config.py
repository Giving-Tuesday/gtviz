"""Global configuration for gtviz.

All output paths, default weight-column names, and DPI settings live here so
that no chart or table function ever hard-codes an environment-specific path
(the original codebase wrote to Databricks ``/Volumes/...`` paths directly).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Options:
    """Runtime options.

    Attributes
    ----------
    output_dir:
        Directory where :func:`gtviz.io.save` writes files. Defaults to
        ``./gtviz_output`` or the ``GTVIZ_OUTPUT_DIR`` environment variable.
    weight_col:
        Default survey-weight column name used by weighted summaries and
        charts when ``weights="auto"`` is passed.
    dpi:
        Raster export resolution.
    transparent:
        Whether PNG exports have a transparent background.
    """

    output_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("GTVIZ_OUTPUT_DIR", "gtviz_output"))
    )
    weight_col: str = "WEIGHT"
    dpi: int = 300
    transparent: bool = False


options = Options()


def set_options(**kwargs) -> Options:
    """Update global options, e.g. ``gtviz.set_options(output_dir="out", dpi=150)``."""
    for k, v in kwargs.items():
        if not hasattr(options, k):
            raise KeyError(f"Unknown option {k!r}")
        setattr(options, k, Path(v) if k == "output_dir" else v)
    return options
