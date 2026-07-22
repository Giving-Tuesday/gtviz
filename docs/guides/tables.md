# Publication tables

## The HTML table

`gtviz.HtmlTable` renders a pandas DataFrame as a publication-styled HTML
table — the exact visual language of the printed quarterly report: heavy
top/bottom rules, gray header band, zebra striping, and conditional cell
shading.

```python
import pandas as pd, gtviz

df = pd.DataFrame({"Q1": [50, 40, 12], "Q2": [55, 38, 14]},
                  index=["Gave money", "Volunteered", "Gave items"])

table = gtviz.HtmlTable(
    df,
    title="Generosity by quarter",
    subtitle="Weighted % of respondents",
    sample_sizes=[1200, 1180],       # renders a "Sample size:" footer row
)
table                                 # rich display in Jupyter/Databricks
html = table.to_html()                # standalone HTML fragment (CSS included)
table.save("generosity.html")         # full standalone page
```

### High/low shading

With `high_low_shading=True` (default), numeric cells more than
`high_low_threshold` points **above** their row mean shade green, and cells
that far **below** shade red. This makes wide crosstabs scannable: the eye
lands on the outlier segments. Tune or disable per table:

```python
gtviz.HtmlTable(df, high_low_threshold=10)     # only flag big deviations
gtviz.HtmlTable(df, high_low_shading=False)    # plain
```

### MultiIndex rollups

Row MultiIndexes render with level-0 labels shown once and blanked on
repeats — the "category / item" layout used throughout the report:

```python
idx = pd.MultiIndex.from_tuples(
    [("Giving", "Money"), ("Giving", "Items"), ("Time", "Volunteering")],
    names=["category", "mode"])
gtviz.HtmlTable(pd.DataFrame({"share": [55, 40, 30]}, index=idx))
```

### Everywhere it renders

`HtmlTable` implements `_repr_html_`, so the same object displays in
Jupyter, in Databricks (`displayHTML` no longer needed), embeds into
`gtviz.io.ReportBuilder` reports, and writes standalone files. This fixed a
bug in the original implementation where asking for the HTML string
re-displayed the table instead of returning it.

## Comparison tables

**`compare_periods`** produces the quarter-over-quarter (and optionally
year-over-year) change table:

```python
out = gtviz.compare_periods(
    df_now, df_prev, ["gave_money", "volunteered"],
    df_yoy=df_last_year,
    labels={"gave_money": "Gave money", "volunteered": "Volunteered"},
)
```

By default you get a pandas Styler with changes beyond ±3 points highlighted
green/red; `style=False` returns the plain DataFrame, and `absolute=True`
reports all periods as levels instead of changes.

**`pivot_change_table`** is the grouped variant: current vs previous
aggregated by any index column (attitude scale, demographic, region), with a
change column.

## Building tables from the stats layer

Any `gtviz.stats` output is table-ready:

```python
summary = gtviz.stats.subgroup_summary(df, "age_group",
                                       ["gave_money", "volunteered"])
gtviz.HtmlTable(summary, title="Behaviours by age group")

chi = gtviz.stats.chi_squared_matrix(df, "gave_money",
                                     ["gender", "age_group", "region"])
gtviz.HtmlTable(chi.round(3), title="Association tests",
                high_low_shading=False)
```
