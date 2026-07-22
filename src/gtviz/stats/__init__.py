"""Statistical support layer: summaries, period change, crosstabs, Likert utilities."""

from .aggs import binned_mean, norm_mean, round_mean, share_above
from .change import compare_crosstab, period_change
from .crosstabs import build_filter, chi_squared_matrix, subgroup_summary
from .likert import decode_likert, normalize_likert
from .summaries import rolling_summary
from .timeutils import add_realdate, trim_rolling_weeks

__all__ = [
    "rolling_summary", "period_change", "compare_crosstab",
    "chi_squared_matrix", "subgroup_summary", "build_filter",
    "normalize_likert", "decode_likert",
    "round_mean", "norm_mean", "share_above", "binned_mean",
    "add_realdate", "trim_rolling_weeks",
]
