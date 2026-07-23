"""Chart functions. All return ``(fig, ax)`` and never call ``plt.show()``."""

from .bars import parallel_bars
from .civic import arrow_range_plot, contribution_bars, nested_bars, range_dot_plot
from .donut import donut
from .dots import dot_plot, grouped_dot_plot, trend_dot_plot
from .funnel import funnel, funnel_from_columns
from .heatmap import weighted_heatmap
from .likert import likert_bars
from .lines import annotated_event_plot, rolling_trend, split_line_plot
from .stacked import banded_shares, stacked_bars
from .venn import venn, venn_from_counts

__all__ = [
    "dot_plot", "grouped_dot_plot", "trend_dot_plot",
    "parallel_bars", "rolling_trend", "split_line_plot", "annotated_event_plot",
    "venn", "venn_from_counts", "weighted_heatmap",
    "funnel", "funnel_from_columns", "donut", "likert_bars",
    "stacked_bars", "banded_shares",
    "contribution_bars", "range_dot_plot", "arrow_range_plot", "nested_bars",
]

try:  # optional extra
    from .waffle import waffle  # noqa: F401

    __all__.append("waffle")
except Exception:  # pragma: no cover
    pass
