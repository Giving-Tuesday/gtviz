"""gtviz: publication-quality survey data visualization.

Refactored from the GivingPulse quarterly-report codebase (``gp_reports``)
into a clean, survey-agnostic library. See https://gtviz.readthedocs.io.

Quick start
-----------
>>> import gtviz
>>> gtviz.theme.use("report")
>>> fig, ax = gtviz.dot_plot([62, 48, 31],
...                          ["Gave money", "Volunteered", "Gave items"])
>>> gtviz.io.save(fig, "generosity", formats=("png", "svg"))  # doctest: +SKIP
"""

from . import charts, io, maps, pipeline, stats, tables, theme
from .charts import (
    annotated_event_plot,
    arrow_range_plot,
    banded_shares,
    contribution_bars,
    donut,
    dot_plot,
    funnel,
    funnel_from_columns,
    grouped_dot_plot,
    likert_bars,
    nested_bars,
    parallel_bars,
    range_dot_plot,
    rolling_trend,
    split_line_plot,
    sparkline_bar_plot,
    stacked_bars,
    trend_dot_plot,
    venn,
    venn_from_counts,
    weighted_heatmap,
)
from .config import options, set_options
from .maps import choropleth_table, scale_bar
from .tables import HtmlTable, compare_periods, pivot_change_table

__version__ = "0.8.1"

__all__ = [
    "__version__",
    # subpackages
    "charts", "tables", "maps", "stats", "io", "theme", "pipeline",
    # config
    "options", "set_options",
    # charts
    "dot_plot", "grouped_dot_plot", "trend_dot_plot", "parallel_bars",
    "rolling_trend", "split_line_plot", "annotated_event_plot",
    "venn", "venn_from_counts", "weighted_heatmap",
    "funnel", "funnel_from_columns", "donut", "likert_bars",
    "stacked_bars", "banded_shares", "sparkline_bar_plot",
    "contribution_bars", "range_dot_plot", "arrow_range_plot", "nested_bars",
    # tables
    "HtmlTable", "compare_periods", "pivot_change_table",
    # maps
    "choropleth_table", "scale_bar",
]

try:  # optional extra: pip install gtviz[waffle]
    from .charts import waffle  # noqa: E402, F401

    __all__.append("waffle")
except ImportError:  # pragma: no cover
    pass
