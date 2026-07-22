# Getting started

## Installation

```bash
pip install gtviz              # core: matplotlib, pandas, numpy, scipy, matplotlib-venn
pip install gtviz[waffle]      # add waffle charts (pywaffle)
pip install gtviz[dev,docs]    # contributors
```

Python 3.10+ is required. gtviz works identically in Jupyter, Databricks
notebooks, plain scripts, and headless CI (set the `Agg` matplotlib backend
in the latter).

## The mental model

gtviz has three layers, and knowing which layer you're calling makes
everything predictable:

1. **`gtviz.stats`** turns respondent-level survey data into small summary
   frames — weighted rolling means, period-over-period changes, subgroup
   crosstabs, chi-squared matrices. These functions return plain pandas
   objects and draw nothing.
2. **`gtviz.charts` / `gtviz.tables` / `gtviz.maps`** turn either raw data
   *or* those summaries into visuals. Chart functions return `(fig, ax)`.
   Table functions return objects that render as rich HTML in notebooks.
3. **`gtviz.io`** gets the visuals out of Python: individual files
   (PNG/SVG/PDF/JPG), inline HTML fragments, or complete assembled reports.

You can work at any layer. Quick chart from raw data? Call the chart
function directly. Custom aggregation first? Use `stats`, then hand the
result to a chart with your own `ax`.

## Your data's shape

gtviz expects **respondent-level** DataFrames — one row per survey response —
with columns like:

| column | meaning |
|---|---|
| `collection_week` (or any period column) | integer week / date / quarter label |
| `WEIGHT` | survey weight (name configurable) |
| binary flags (`gave_money`, ...) | 0/1 behaviours |
| Likert columns (`belonging`, ...) | small-integer scales |
| demographics (`age_group`, `region`, ...) | categorical splits |

Set your conventions once:

```python
import gtviz

gtviz.set_options(
    weight_col="WEIGHT",        # used whenever a function gets weights="auto"
    output_dir="report_output", # where gtviz.io.save writes
    dpi=300,
)
gtviz.theme.use("report")       # or "publication"
```

## First chart, first table, first export

```python
import pandas as pd
import gtviz

df = pd.read_parquet("survey_q2.parquet")

# 1. A chart straight from respondent-level data
fig, ax = gtviz.grouped_dot_plot(
    df,
    group_col="age_group",
    metric_cols=["gave_money", "volunteered", "gave_items"],
    metric_labels={"gave_money": "Gave money",
                   "volunteered": "Volunteered",
                   "gave_items": "Gave items"},
    error=True,
    title="Generosity behaviours by age group",
)
gtviz.io.save(fig, "behaviours_by_age", formats=("png", "svg"))

# 2. A publication table
summary = gtviz.stats.subgroup_summary(df, "region", ["gave_money", "volunteered"])
table = gtviz.HtmlTable(summary, title="Behaviours by region",
                        subtitle="Weighted % of respondents")
table            # renders in a notebook
table.save("behaviours_by_region.html")

# 3. A one-file report combining both
report = (gtviz.io.ReportBuilder(title="Q2 snapshot")
          .add_figure(fig, caption="Figure 1")
          .add_table(table, caption="Table 1"))
report.to_html("q2_snapshot.html")   # standalone, figures inlined as SVG
report.to_pdf("q2_snapshot.pdf")
```

## Weights, everywhere

Any function with a `weights` parameter accepts:

- `"auto"` *(default)* — use `gtviz.options.weight_col` if present;
- a column name — use that column;
- `None` — unweighted;
- an array-like — explicit weights.

This mirrors how production survey reporting actually works: everything is
weighted, always, and you should only have to say so once.

## Where to next

- {doc}`charts_tour` — every chart type with the situation it's built for.
- {doc}`tables` — the publication HTML table and comparison tables.
- {doc}`exporting` — PNG/SVG/PDF/HTML pipelines for websites and reports.
- {doc}`migration` — coming from the original `gp_reports` codebase.
