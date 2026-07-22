"""GivingPulse dataset pipeline: sklearn-style processing steps.

Dataset-specific transforms (question codes, scoring recipes, reference-file
merges) kept separate from the generalizable viz API. Typical use replaces
the notebook preamble entirely::

    import gtviz

    df, meta = gtviz.pipeline.read_pipeline(year=2025)
    df = gtviz.pipeline.process(
        df,
        typology="/Volumes/.../2023-Typology-(15-county-types).xlsx",
        pew_decoder="/Volumes/.../pew_political_spectrum_questions.csv",
    )

or, sklearn-style, with explicit steps and per-step params::

    from gtviz.pipeline import Pipeline, ScoreBelonging, ScoreCivicIntent, CivicQuartile

    pipe = Pipeline([
        ("belonging", ScoreBelonging(add_flags=False)),
        ("civic", ScoreCivicIntent()),
        ("quartile", CivicQuartile()),
    ], verbose=True)
    pipe.set_params(civic__recency_map={1: 1, 2: 0.5, 3: 0.25, 4: 0})
    df = pipe.transform(df)
"""

from __future__ import annotations

import pandas as pd

from .base import Pipeline, PipelineStep
from .io import read_pipeline
from .steps import (
    AssignActivism,
    AssignCountyTypes,
    AssignPew,
    CivicQuartile,
    ScoreBelonging,
    ScoreCivicIntent,
)

__all__ = [
    "Pipeline", "PipelineStep", "read_pipeline", "process", "default_pipeline",
    "ScoreBelonging", "ScoreCivicIntent", "AssignCountyTypes", "AssignPew",
    "AssignActivism", "CivicQuartile",
]


def default_pipeline(
    typology=None,
    pew_decoder=None,
    pipeline_version: int = 2026,
    verbose: bool = False,
) -> Pipeline:
    """The standard GivingPulse scoring batch, in notebook order:
    activism -> county types -> belonging -> civic intent -> pew -> quartiles.

    Steps needing reference data (``AssignCountyTypes``, ``AssignPew``) are
    included only when their source (path or DataFrame) is provided.
    """
    steps: list[tuple[str, PipelineStep]] = [
        ("activism", AssignActivism(verbose=verbose)),
    ]
    if typology is not None:
        steps.append(("county_types", AssignCountyTypes(typology, verbose=verbose)))
    steps += [
        ("belonging", ScoreBelonging(verbose=verbose)),
        ("civic_intent", ScoreCivicIntent(verbose=verbose)),
    ]
    if pew_decoder is not None:
        steps.append(("pew", AssignPew(pew_decoder, pipeline_version=pipeline_version,
                                       verbose=verbose)))
    steps.append(("civic_quartile", CivicQuartile()))
    return Pipeline(steps, verbose=verbose)


def process(df: pd.DataFrame, steps: list | None = None, **kwargs) -> pd.DataFrame:
    """Run the default (or a custom) pipeline over ``df`` in one call.

    ``kwargs`` pass through to :func:`default_pipeline`
    (``typology=``, ``pew_decoder=``, ``pipeline_version=``, ``verbose=``).
    """
    pipe = Pipeline(steps) if steps is not None else default_pipeline(**kwargs)
    return pipe.transform(df)
