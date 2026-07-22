# A tour of the charts

Each chart in gtviz exists because a real quarterly survey report needed it,
repeatedly. This guide walks through when to reach for which, with the
reasoning that shaped each design. All examples render from the synthetic
dataset in `examples/generate_gallery.py`; see the {doc}`../gallery` for the
output images.

## Dot plots — the workhorse

When you need to compare *levels* across categories and the ordering matters
more than the magnitude of bars, dot plots beat bar charts: less ink, easier
scanning, natural room for error bars.

**`dot_plot`** is the primitive: values + labels, optional symmetric error,
optional value annotations.

```python
gtviz.dot_plot([62, 48, 31], ["Gave money", "Volunteered", "Gave items"],
               error=[3, 3, 2], title="Generosity behaviours")
```

**`grouped_dot_plot`** answers "how does each subgroup differ on each
metric?" One colored dot series per group level, one lane per metric, an
optional whole-sample series for anchoring, and normal-approximation 95%
CIs for binary metrics (`error=True`). This one function replaces five
near-identical functions in the original codebase — the difference between
them was only *which* grouping column and *which* label dictionary, so those
became parameters.

**`trend_dot_plot`** answers "how did each metric move across periods?" Same
lane layout, but the colored series are time periods instead of groups.

## Parallel bar panels

**`parallel_bars`** is the signature demographic-splits chart: a baseline
"Everyone" panel followed by one panel per subgroup, where the subgroup
panels are labeled with **point differences vs baseline** (`+7`, `-3`)
rather than raw values. Readers compare against the norm instantly. Splits
are `(column, level)` pairs:

```python
gtviz.parallel_bars(
    df,
    variables=["gave_money", "volunteered", "gave_items", "solicited"],
    ylabels=["Gave money", "Volunteered", "Gave items", "Solicited"],
    splits=[("gender", "Woman"), ("age_group", "18-34")],
    sub_titles=["Women", "18–34"],
)
```

## Trend lines

**`rolling_trend`** plots weighted, rolling-window means per period — the
standard weekly-tracking chart. The summarized frame is attached to the axes
as `ax._gtviz_data` so you can inspect exactly what was plotted, or reuse it
in a table.

**`split_line_plot`** draws one line per group. Three ways to define groups:
a column name (one line per level), a dict of boolean masks (arbitrary
segments), or `by_quartile=True` to split a numeric variable into its own
quartiles — useful for questions like "do high-belonging respondents give
differently over time?"

**`annotated_event_plot`** is a single trend with labeled vertical event
markers — built for crisis-awareness tracking where "what happened when the
line moved" is the whole story.

## Venn diagrams

**`venn`** takes two or three binary flag columns and infers the layout.
Region labels default to *percent of sample* rather than counts, matching
report style. Use `filter=` to scope to a subpopulation and `weighted=True`
for area-proportional circles (default is equal-size, which reads better in
print).

**`venn_from_counts`** exists for the pre-aggregated workflow: when overlap
counts arrive already computed (e.g. from a warehouse query), pass a dict
mapping flag tuples to counts.

## Weighted heatmaps

**`weighted_heatmap`** shows groups x metrics as a colored matrix with
annotations — the fastest way to scan a battery of related questions across
segments. Weighted means computed internally; pure matplotlib (no seaborn
dependency).

## Funnel, donut, Likert, waffle

- **`funnel`** — symmetric stage-share funnel, any number of stages, with an
  automatic 100% "Everyone" band. `funnel_from_columns` computes the stage
  shares from binary columns with weights.
- **`donut`** — clockwise-from-noon ring chart for composition.
- **`likert_bars`** — 100% stacked horizontal answer distributions per item,
  with `reverse_answers=` for negatively-worded items and diverging default
  colors.
- **`waffle`** — optional (`pip install gtviz[waffle]`), for
  parts-of-a-whole stories where icons-per-unit reads better than a pie.

## Composing charts

Everything accepts `ax=`, so multi-panel layouts are ordinary matplotlib:

```python
import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
gtviz.rolling_trend(df, ["gave_money"], ax=ax1, title="Trend")
gtviz.weighted_heatmap(df, "region", ["gave_money", "volunteered"], ax=ax2,
                       title="By region")
```

No gtviz function ever calls `plt.show()`; you decide when (and whether) to
display.
