"""Load GivingPulse survey data from the production Delta pipeline.

Replaces the copy-pasted notebook preamble::

    source = 'prod_curated.giving_pulse.cleaned_survey_results'
    df = spark.read.format("delta").table(source).toPandas()
    df = df[pd.to_datetime(df['endtime']).dt.year == 2025]
    meta = spark.read.table(meta_source).toPandas()

with::

    df, meta = gtviz.pipeline.read_pipeline(year=2025)
"""

from __future__ import annotations

import pandas as pd

DEFAULT_SOURCE = "prod_curated.giving_pulse.cleaned_survey_results"
DEFAULT_META_SOURCE = "prod_curated.giving_pulse.survey_metadata"


def _get_spark(spark=None):
    if spark is not None:
        return spark
    try:  # Databricks / active session
        from pyspark.sql import SparkSession

        s = SparkSession.getActiveSession()
        if s is None:
            raise RuntimeError
        return s
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "No active Spark session. Run inside Databricks or pass spark=."
        ) from e


def read_pipeline(
    source: str = DEFAULT_SOURCE,
    meta_source: str | None = DEFAULT_META_SOURCE,
    year: int | None = None,
    quarter: int | None = None,
    start: str | None = None,
    end: str | None = None,
    weeks: list[int] | None = None,
    columns: list[str] | None = None,
    endtime_col: str = "endtime",
    spark=None,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Read the cleaned survey table (and metadata) into pandas.

    Parameters
    ----------
    year, quarter:
        Filter by calendar year / quarter of ``endtime``.
    start, end:
        Explicit inclusive date bounds (any pandas-parsable strings);
        override year/quarter.
    weeks:
        Filter to specific ``collection_week`` values.
    columns:
        Subset of columns to keep (post-filter).
    spark:
        Spark session; discovered from the active Databricks session when
        omitted.

    Returns
    -------
    (df, meta) -- ``meta`` is None when ``meta_source`` is None.

    Examples
    --------
    >>> df, meta = read_pipeline(year=2025)                    # doctest: +SKIP
    >>> df, _ = read_pipeline(year=2026, quarter=1,
    ...                       meta_source=None)                # doctest: +SKIP
    """
    s = _get_spark(spark)
    df = s.read.format("delta").table(source).toPandas()

    if endtime_col in df.columns:
        et = pd.to_datetime(df[endtime_col])
        if start or end:
            if start:
                df = df[et >= pd.Timestamp(start)]
            if end:
                df = df[et <= pd.Timestamp(end)]
        else:
            if year is not None:
                df = df[et.dt.year == year]
            if quarter is not None:
                df = df[et.dt.quarter == quarter]
    if weeks is not None and "collection_week" in df.columns:
        df = df[df["collection_week"].isin(weeks)]
    if columns is not None:
        df = df[columns]
    df = df.reset_index(drop=True)

    meta = None
    if meta_source:
        meta = s.read.table(meta_source).toPandas()
    return df, meta


def filter_meta(
    meta: pd.DataFrame,
    contains: str | None = None,
    col_name_col: str = "col_name",
    encoded_col: str = "encoded",
    match_code: bool = True,
) -> pd.DataFrame:
    """Filter a survey-metadata frame to rows whose coding is self-consistent.

    GivingPulse metadata repeats each question across its answer options, and
    the trailing number on ``col_name`` (e.g. ``ethnie_1``) is meant to line
    up with the leading digit of the ``encoded`` value for that option. Rows
    where they disagree are stray / mis-joined coding. This helper keeps only
    the matching rows, and optionally narrows to one question family first.

    Replaces the notebook one-liner::

        meta[meta.col_name.str.contains('ethnie')
             & (meta.col_name.str[-1] == meta.encoded.astype(str).str[0])]

    Parameters
    ----------
    meta:
        The metadata frame from :func:`read_pipeline` (full, unfiltered).
    contains:
        If given, first restrict to ``col_name`` containing this substring
        (e.g. ``"ethnie"``). ``None`` keeps all question families.
    col_name_col, encoded_col:
        Column names, in case the schema differs.
    match_code:
        Keep only rows where the last char of ``col_name`` equals the first
        char of ``str(encoded)`` (the self-consistency check). Set False to
        only apply the ``contains`` filter.

    Returns
    -------
    A filtered **copy**; the input ``meta`` is unchanged, so
    :func:`read_pipeline` still returns the complete metadata.

    Examples
    --------
    >>> df, meta = read_pipeline(year=2026)              # doctest: +SKIP
    >>> eth = filter_meta(meta, contains="ethnie")       # doctest: +SKIP
    """
    out = meta
    if contains is not None:
        out = out[out[col_name_col].str.contains(contains, na=False)]
    if match_code:
        last = out[col_name_col].astype(str).str[-1]
        first = out[encoded_col].astype(str).str[0]
        out = out[last == first]
    return out.copy()
