"""Global configuration for gtviz.

All output paths, default weight-column names, DPI, and **reference-file
locations** live here so that no chart, table, or pipeline step ever
hard-codes an environment-specific path (the original codebase wrote to
Databricks ``/Volumes/...`` paths directly).

Reference files (Pew decoder, county typology) resolve in this order:

1. an explicit argument passed to the step (path or DataFrame);
2. ``gtviz.set_options(pew_decoder=...)`` set at runtime;
3. the corresponding environment variable
   (``GTVIZ_PEW_DECODER`` / ``GTVIZ_COUNTY_TYPOLOGY``);
4. otherwise ``None`` -- the step raises a clear, actionable error.

This keeps the package itself free of any specific link while letting an
org point every notebook at shared files by setting one env var on the
cluster, and letting anyone repoint to an updated file with a single
``set_options`` call.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_path(var: str) -> Path | None:
    val = os.environ.get(var)
    return Path(val) if val else None


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
    pew_decoder:
        Location of the Pew political-typology reference CSV used by
        :class:`gtviz.pipeline.AssignPew`. Defaults to the
        ``GTVIZ_PEW_DECODER`` env var if set, else ``None``.
    county_typology:
        Location of the county-typology reference file used by
        :class:`gtviz.pipeline.AssignCountyTypes`. Defaults to the
        ``GTVIZ_COUNTY_TYPOLOGY`` env var if set, else ``None``.
    """

    output_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("GTVIZ_OUTPUT_DIR", "gtviz_output"))
    )
    weight_col: str = "WEIGHT"
    dpi: int = 300
    transparent: bool = False
    pew_decoder: Path | None = field(default_factory=lambda: _env_path("GTVIZ_PEW_DECODER"))
    county_typology: Path | None = field(default_factory=lambda: _env_path("GTVIZ_COUNTY_TYPOLOGY"))


options = Options()

_PATH_OPTS = {"output_dir", "pew_decoder", "county_typology"}


def set_options(**kwargs) -> Options:
    """Update global options.

    Examples
    --------
    >>> import gtviz
    >>> gtviz.set_options(dpi=150, output_dir="out")               # doctest: +SKIP
    >>> gtviz.set_options(pew_decoder="/Volumes/.../decoder.csv")  # doctest: +SKIP
    """
    for k, v in kwargs.items():
        if not hasattr(options, k):
            raise KeyError(f"Unknown option {k!r}")
        setattr(options, k, (Path(v) if v is not None else None) if k in _PATH_OPTS else v)
    return options


def resolve_reference(explicit, option_name: str, env_var: str, what: str):
    """Resolve a reference-file location from (in order) an explicit value,
    the matching config option, or its environment variable.

    Returns the explicit value unchanged when it is not a path (e.g. an
    already-loaded DataFrame). Raises :class:`FileNotFoundError` with an
    actionable message when nothing resolves or the resolved path is absent.
    """
    from pathlib import Path as _P

    # Non-path explicit (e.g. a DataFrame) passes straight through.
    if explicit is not None and not isinstance(explicit, (str, _P)):
        return explicit

    target = explicit if explicit is not None else getattr(options, option_name)
    if target is None:
        raise FileNotFoundError(
            f"No {what} configured. Provide one of:\n"
            f"  - pass it directly to the step,\n"
            f"  - gtviz.set_options({option_name}='/path/to/file'),\n"
            f"  - set the {env_var} environment variable,\n"
            f"  - or pass an already-loaded DataFrame."
        )
    target = _P(target)
    if not target.exists():
        raise FileNotFoundError(
            f"{what} not found at {target}. Update it via "
            f"gtviz.set_options({option_name}='...') or the {env_var} env var."
        )
    return target
