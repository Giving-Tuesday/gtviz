# Migrating from `gp_reports`

gtviz consolidates ~70 functions from the original repo into ~25 canonical
APIs. This page maps every old call to its replacement.

## General changes

- **No Spark, no globals.** Functions take DataFrames; nothing reads
  `DATA`/`DATA_LAST_Q` module state. Load your data, pass it in.
- **Nothing calls `plt.show()`.** Charts return `(fig, ax)`; display or save
  explicitly.
- **Weights are explicit.** `weights="auto"` uses
  `gtviz.options.weight_col` (default `"WEIGHT"`), matching old behavior.
- **Label dictionaries are arguments.** Question-text mappings that were
  hard-coded now pass via `labels=` / `metric_labels=` / `group_labels=`.
- **Output paths are configured, not hard-coded.**
  `gtviz.set_options(output_dir=...)` replaces `/Volumes/...` literals.

## Function mapping

| old (`gp_reports`) | new (`gtviz`) |
|---|---|
| `convert_df_to_html(df, title, ...)` | `HtmlTable(df, title=...)` — `.to_html()` now truly returns the string |
| `quarter_year_compare(...)` | `compare_periods(df_now, df_prev, cols, df_yoy=...)` |
| `quarterly_change_crosstab(...)` | `stats.compare_crosstab(...)` |
| `pivot_attitudes_giving_money(...)` | `pivot_change_table(..., index=..., values=...)` |
| `dot_plot(...)` | `dot_plot(...)` (same idea, `ax=`/return added) |
| `depolarization_groups_dot_plot` and 4 sibling clones | `grouped_dot_plot(df, group_col, metric_cols, ...)` |
| `trends_dot_plot`, `draft_grouped_trends_dot_plot` | `trend_dot_plot(...)` |
| `parallel_bar_chart(...)` | `parallel_bars(...)` — no longer mutates your `ylabels` list |
| `plot_monetary_giving_rolling_weeks`, `weekly_trends_plot_news_aware` | `rolling_trend(df, columns, ...)` |
| `civic_gt_awareness_splits` / `..._split_quartiles` | `split_line_plot(..., by_quartile=True/False)` |
| `crisis_awareness_plot` | `annotated_event_plot(df, value_col, events)` |
| `venn_diagram_2/_3` | `venn(df, [col1, col2(, col3)])` |
| `venn_diagram_2_filter/_3_filter` | `venn(..., filter=mask)` |
| `0_mode_viz_export` inline venns | `venn_from_counts({(1,0,0): n, ...}, labels)` |
| `heatmaps`, `heatmaps_q4` | `weighted_heatmap(df, group_col, value_cols)` |
| `funnel_chart(...)` | `funnel(proportions, labels)` or `funnel_from_columns(df, cols)` |
| `donut_chart(...)` | `donut(values, labels)` |
| `show_belonging(...)` | `likert_bars(df, items, ...)` |
| `map_table_absolute(...)` | `choropleth_table(df, value_col, mode="absolute")` |
| `map_table_relative(...)` | `choropleth_table(..., mode="relative")` |
| `map_scale_min_max`, `map_scale` | `scale_bar(vmin, vmax, cutoffs=None/...)` |
| `weekly_summary` (+ `_filter`, `_no_rolling`, `normalized_`) | `stats.rolling_summary(df, cols, filter=, rolling=, normalize=)` |
| `quarterly_change` (+ variants) | `stats.period_change(df, df_prev, cols, ...)` |
| `demo_subgroup_summary` | `stats.subgroup_summary(df, split_col, cols)` |
| `demographic_filter` | `stats.build_filter(df, {"col": value_or_list})` |
| `chi_squared_tests` | `stats.chi_squared_matrix(df, var, others)` |
| `normalize_likert`, `decode_likert`, `decode_demog`, `decode_q50` | `stats.normalize_likert`, `stats.decode_likert(df, col, labels)` |
| `avg_don_approx`, `avg_age_approx` | `stats.binned_mean(series, midpoints)` |
| `round_mean` / `norm_mean*` / `above10000` lambdas | `stats.round_mean`, `stats.norm_mean`, `stats.share_above` |
| `add_realdate`, `trim_rolling_weeks` | `stats.add_realdate(df, start_date=...)`, `stats.trim_rolling_weeks(df, year)` — start date is now a parameter |
| `report_params.py` rcParams block | `theme.use("report")` |
| "FLORIDA" commented style | `theme.use("publication")` |
| scattered `plt.savefig(...)` | `io.save(fig, name, formats=(...))` |

## Dataset processing → `gtviz.pipeline`

Domain scoring and segmentation moved into the sklearn-style
`gtviz.pipeline` subpackage (see {doc}`pipeline`), keeping the viz API
survey-agnostic while standardizing the notebook preamble:

| old (notebook) | new (`gtviz.pipeline`) |
|---|---|
| Spark read + endtime year filter boilerplate | `read_pipeline(year=...)` |
| `activism_report(df)` | `AssignActivism()` |
| `assign_county_types(df)` (hard-coded xlsx path) | `AssignCountyTypes(typology=path_or_df)` |
| `score_belonging(df)` (+ inline histogram) | `ScoreBelonging()` — plotting removed from scoring |
| `score_civic_intent(df)` | `ScoreCivicIntent()` — vectorized |
| `assign_pew(df)` (tqdm row loop, hard-coded csv) | `AssignPew(decoder=path_or_df)` — vectorized, ~1000x faster |
| `civic_quartiler` row apply | `CivicQuartile()` |
| the whole sequence | `process(df, typology=..., pew_decoder=...)` |

Still not ported: survey *cleaning* (`data/cleaning_pipeline.py`) and
clustering — those remain upstream of the curated Delta table this package
reads from.

## Bugs fixed during the port

- `convert_df_to_html(return_code=True)` re-displayed instead of returning
  HTML — `HtmlTable.to_html()` returns the string.
- `parallel_bar_chart` reversed the caller's `ylabels` list in place.
- FIPS codes could lose leading zeros via int-casting in map functions.
- `SettingWithCopyWarning` patterns in the map table builders.
- Three colliding definitions of `weekly_trends_plot_news_aware` and four of
  `crisis_awareness_plot` — one canonical version each.
