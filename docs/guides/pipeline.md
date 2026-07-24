# The GivingPulse processing pipeline

`gtviz.pipeline` holds the **dataset-specific** processing that used to live
at the top of every analysis notebook: loading from the production Delta
tables and running the standard scoring batch (activism flags, county
typology, belonging, civic intent, Pew typology, quartiles). It is
deliberately separated from the generalizable viz/stats API — question
codes and scoring recipes belong here, nothing else in gtviz knows about
`Q31_r6_scale`.

## Replacing the notebook preamble

Before:

```python
source = 'prod_curated.giving_pulse.cleaned_survey_results'
df = spark.read.format("delta").table(source).toPandas()
df = df[pd.to_datetime(df['endtime']).dt.year == 2025]
meta = spark.read.table(meta_source).toPandas()
df = activism_report(df)
df = assign_county_types(df)
df['belonging'] = score_belonging(df)
df = score_civic_intent(df)
df = assign_pew(df)
df['civic_quartile'] = df.apply(civic_quartiler, axis=1)
```

After:

```python
import gtviz

df, meta = gtviz.pipeline.read_pipeline(year=2025)
df = gtviz.pipeline.process(
    df,
    typology="/Volumes/sandbox_annie/giving_pulse/misc/2023-Typology-(15-county-types).xlsx",
    pew_decoder="/Volumes/sandbox_annie/giving_pulse/pew_decoder/pew_political_spectrum_questions.csv",
)
```

`read_pipeline` finds the active Databricks Spark session automatically and
accepts `year=`, `quarter=`, `start=`/`end=`, `weeks=`, and `columns=`
filters. Reference files are **parameters, not hard-coded paths**, and every
reference argument accepts a path *or* an in-memory DataFrame — which is how
the test suite runs the whole pipeline with zero production access.

## Working with metadata

`read_pipeline` returns the **full** metadata frame unchanged. The GivingPulse
metadata repeats each question across its answer options, where the trailing
number of ``col_name`` should match the leading digit of ``encoded``.
``filter_meta`` narrows to the self-consistent rows (and optionally one
question family):

```python
df, meta = gtviz.pipeline.read_pipeline(year=2026)
eth = gtviz.pipeline.filter_meta(meta, contains="ethnie")   # ethnie_* coded rows
codebook = gtviz.pipeline.filter_meta(meta)                 # all families, matched coding
```

`meta` itself is never mutated, so the complete metadata stays available.

## sklearn-style composition

Steps follow the scikit-learn transformer contract
(`get_params` / `set_params` / `fit` / `transform`), so you can build custom
batches, address parameters with `step__param` syntax, and even mount steps
inside an `sklearn.pipeline.Pipeline`:

```python
from gtviz.pipeline import (Pipeline, ScoreBelonging, ScoreCivicIntent,
                            AssignPew, CivicQuartile)

pipe = Pipeline([
    ("belonging",  ScoreBelonging(add_flags=False)),
    ("civic",      ScoreCivicIntent()),
    ("pew",        AssignPew(pew_decoder, pipeline_version=2026)),
    ("quartile",   CivicQuartile()),
], verbose=True)

pipe.set_params(civic__recency_map={1: 1, 2: 0.5, 3: 0.25, 4: 0})
df = pipe.transform(df)
pipe.named_steps["pew"].get_params()
```

`verbose=True` prints per-step timing and shape — the batch equivalent of
watching notebook cells run.

## The steps

| step | adds | notes |
|---|---|---|
| `AssignActivism` | `activism_none/min/boycott/inperson/lead/any/moderate` | OR-combinations of the Q21B battery; levels are a parameter |
| `AssignCountyTypes` | `county_type`, `Fips` | merge on (county, state); handles the abbreviated-state YTD format; idempotent |
| `ScoreBelonging` | `belonging` (0-1) + optional group/flag columns | valence-aware reverse coding of the four Q31 items |
| `ScoreCivicIntent` | `civic_intent` (0-1), `giving_recency_*` | full composite; recency mapping is a parameter (2026-confirmed default) |
| `AssignPew` | `best_pew` (ordered categorical), `*_dist`, one-hots | **vectorized** — the notebook's per-respondent loop is now one matrix op with identical distances |
| `CivicQuartile` | `civic_quartile` | fixed 0.25 bands |

All steps return a copy; your input frame is never mutated. `verbose=True`
on any step restores the notebook's diagnostic prints.

## Version drift

Survey waves change codings. Where that happened, it's a parameter:
`AssignPew(pipeline_version=2026)` handles the 2026 answer-code reversal;
`ScoreCivicIntent(recency_map=...)` and `ScoreBelonging(answer_map=...)`
override mappings without touching library code. When a new wave changes a
recipe, change the default in one place and the dedicated pipeline CI
(below) verifies against both pandas 2 and 3.

## Dedicated CI

`.github/workflows/pipeline.yml` runs separately from the chart CI:

- triggers **only on pipeline-path changes** (`src/gtviz/pipeline/**`), so
  chart PRs don't re-run survey logic and vice versa;
- tests across a python x pandas matrix, plus an sklearn interop check;
- a `batch-smoke` job runs the complete `process()` batch headlessly over
  synthetic data with in-memory reference tables;
- a weekly scheduled run catches dependency drift between quarterly report
  cycles.
