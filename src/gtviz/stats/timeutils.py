"""Survey-week and quarter date utilities.

Parametrized ports of ``add_realdate`` / ``date_from_qtaweek`` /
``trim_rolling_weeks`` -- the collection start date is now an argument
instead of the hard-coded ``2022-09-12``.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd


def add_realdate(
    df: pd.DataFrame,
    week_col: str = "collection_week",
    start_date: str = "2022-09-12",
    out_col: str = "real_date",
) -> pd.DataFrame:
    """Add a calendar date column derived from an integer week counter.

    ``real_date = start_date + 7 days * (week - 1)``. Returns a copy.
    """
    out = df.copy()
    start = pd.Timestamp(start_date)
    out[out_col] = start + pd.to_timedelta((out[week_col].astype(int) - 1) * 7, unit="D")
    return out


def quarter_bounds(year: int) -> dict[int, tuple[dt.datetime, dt.datetime]]:
    """Start/end datetimes for each quarter of ``year``."""
    return {
        1: (dt.datetime(year, 1, 1), dt.datetime(year, 3, 31)),
        2: (dt.datetime(year, 4, 1), dt.datetime(year, 6, 30)),
        3: (dt.datetime(year, 7, 1), dt.datetime(year, 9, 30)),
        4: (dt.datetime(year, 10, 1), dt.datetime(year, 12, 31)),
    }


def trim_rolling_weeks(
    df: pd.DataFrame,
    year: int,
    date_col: str = "collection_week",
    min_responses: int = 1100,
) -> pd.DataFrame:
    """Trim leading rolling-average weeks by selecting the first quarter of
    ``year`` with at least ``min_responses`` rows (else the latest partial).

    The original report dataframes carried three extra trailing weeks for
    rolling metrics; quarterly metrics need them removed.
    """
    last = df.iloc[0:0]
    for start, end in quarter_bounds(year).values():
        q = df.loc[df[date_col].between(start, end)]
        if len(q) > min_responses:
            return q.copy()
        if len(q):
            last = q
    return last.copy()
