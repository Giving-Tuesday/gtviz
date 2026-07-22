"""sklearn-style pipeline machinery for GivingPulse dataset processing.

These are **dataset-specific** transforms (question codes, scoring recipes),
deliberately separated from the generalizable viz/stats API. Steps follow
the scikit-learn conventions -- ``get_params``/``set_params``/``transform`` --
so they compose, introspect, and batch-run the same way sklearn pipelines do
(and can even be dropped inside an ``sklearn.pipeline.Pipeline``).
"""

from __future__ import annotations

import inspect
import time

import pandas as pd


class PipelineStep:
    """Base class for dataset transforms.

    Subclasses implement :meth:`transform(df) -> df`. Constructor arguments
    are the step's parameters (sklearn convention: store them verbatim as
    attributes of the same name).
    """

    def get_params(self, deep: bool = True) -> dict:
        """Parameter dict, from the constructor signature (sklearn API)."""
        sig = inspect.signature(type(self).__init__)
        return {name: getattr(self, name) for name in sig.parameters if name != "self"}

    def set_params(self, **params) -> PipelineStep:
        for k, v in params.items():
            if not hasattr(self, k):
                raise ValueError(f"{type(self).__name__} has no parameter {k!r}")
            setattr(self, k, v)
        return self

    def fit(self, df: pd.DataFrame, y=None) -> PipelineStep:  # sklearn compat
        return self

    def fit_transform(self, df: pd.DataFrame, y=None) -> pd.DataFrame:
        return self.fit(df).transform(df)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:  # pragma: no cover
        raise NotImplementedError

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.transform(df)

    def __repr__(self) -> str:
        params = ", ".join(f"{k}={v!r}" for k, v in self.get_params().items()
                           if not isinstance(v, (pd.DataFrame,)))
        return f"{type(self).__name__}({params})"


class Pipeline:
    """Ordered batch of named steps: ``Pipeline([("belonging", ScoreBelonging()), ...])``.

    ``transform`` runs every step in order and returns the final frame.
    Access individual steps via :attr:`named_steps`.

    Examples
    --------
    >>> from gtviz.pipeline import Pipeline, ScoreBelonging, CivicQuartile
    >>> pipe = Pipeline([("belonging", ScoreBelonging()),
    ...                  ("quartile", CivicQuartile(source_col="belonging"))])
    >>> out = pipe.transform(df)                     # doctest: +SKIP
    >>> pipe.named_steps["belonging"].get_params()   # doctest: +SKIP
    """

    def __init__(self, steps: list[tuple[str, PipelineStep]], verbose: bool = False):
        self.steps = steps
        self.verbose = verbose

    @property
    def named_steps(self) -> dict:
        return dict(self.steps)

    def get_params(self, deep: bool = True) -> dict:
        out = {"steps": self.steps, "verbose": self.verbose}
        if deep:
            for name, step in self.steps:
                for k, v in step.get_params().items():
                    out[f"{name}__{k}"] = v
        return out

    def set_params(self, **params) -> Pipeline:
        """Supports sklearn's ``step__param`` addressing."""
        for key, val in params.items():
            if "__" in key:
                name, param = key.split("__", 1)
                self.named_steps[name].set_params(**{param: val})
            else:
                setattr(self, key, val)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df
        for name, step in self.steps:
            t0 = time.perf_counter()
            out = step.transform(out)
            if self.verbose:
                print(f"[gtviz.pipeline] {name}: {time.perf_counter() - t0:.2f}s "
                      f"({len(out)} rows, {len(out.columns)} cols)")
        return out

    fit_transform = transform

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.transform(df)

    def __repr__(self) -> str:
        inner = ",\n  ".join(f"({name!r}, {step!r})" for name, step in self.steps)
        return f"Pipeline([\n  {inner}\n])"
