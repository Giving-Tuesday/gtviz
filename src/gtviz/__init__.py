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
    donut,
    dot_plot,
    funnel,
    funnel_from_columns,
    grouped_dot_plot,
    likert_bars,
    parallel_bars,
    rolling_trend,
    split_line_plot,
    trend_dot_plot,
    venn,
    venn_from_counts,
    weighted_heatmap,
)
from .config import options, set_options
from .maps import choropleth_table, scale_bar
from .tables import HtmlTable, compare_periods, pivot_change_table

__version__ = "0.3.0"

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
    # tables
    "HtmlTable", "compare_periods", "pivot_change_table",
    # maps
    "choropleth_table", "scale_bar",
]
