# Changelog

## 0.3.0 (2026-07-22)

- **Renamed package `gpviz` → `gtviz`** (imports, env var `GTVIZ_OUTPUT_DIR`,
  docs URLs, `ax._gtviz_data`).
- **Brand-default restoration**: all chart styling audited line-by-line
  against the production `gp_reports` code and ported verbatim as defaults
  (dot marker/error/grid style, gray-first series palette, frameless
  outside legends, no-box grouped dot plots, n= legend counts, 25-char
  label wrapping, rolling-trend plain lines + (1,1) legend + optional gray
  period shading, split-line palette, 4-point Likert palette + outside
  legend + zero-width label suppression, venn 20pt/pad-30 titles, funnel
  band geometry, donut without autopct, figure.dpi 300).
- `theme.use(profile, font=...)` for the brand font (Neutraface Text);
  new palette tokens `split_series`, `likert4`, `stacked3`.
- New guide: *Design defaults & override policy* documenting every default,
  its override kwarg, and the open default-vs-override decisions.

## 0.2.0 (2026-07-22)

- New `gtviz.pipeline` subpackage: sklearn-style dataset processing for the
  GivingPulse survey. `read_pipeline()` (Delta/Spark loader with
  year/quarter/week filters), `process()` / `default_pipeline()` batch
  runner, and steps `AssignActivism`, `AssignCountyTypes`, `ScoreBelonging`,
  `ScoreCivicIntent`, `AssignPew` (vectorized), `CivicQuartile`.
  Steps implement the sklearn transformer contract (`get_params`,
  `set_params`, `step__param` addressing, usable in `sklearn.pipeline`).
- Reference files (county typology, Pew decoder) are parameters accepting a
  path or DataFrame — no hard-coded `/Volumes/...` paths.
- Dedicated `pipeline.yml` CI: path-filtered triggers, python x pandas
  matrix, sklearn interop check, headless batch smoke run, weekly schedule.

## 0.1.0 (2026-07-22)

Initial public release: full refactor of the `gp_reports` visualization code.

- `charts`: dot_plot, grouped_dot_plot, trend_dot_plot, parallel_bars,
  rolling_trend, split_line_plot, annotated_event_plot, venn,
  venn_from_counts, weighted_heatmap, funnel, funnel_from_columns, donut,
  likert_bars, waffle (extra).
- `tables`: HtmlTable (publication CSS table), compare_periods,
  pivot_change_table.
- `maps`: choropleth_table (absolute/relative), scale_bar.
- `stats`: rolling_summary, period_change, compare_crosstab,
  subgroup_summary, build_filter, chi_squared_matrix, normalize_likert,
  decode_likert, named aggregators, time utilities.
- `io`: multi-format save (png/svg/pdf/jpg/webp/eps), HTML embedding,
  ReportBuilder (standalone HTML + multi-page PDF).
- `theme`: "report" and "publication" profiles, palette tokens.
- CI: lint, test matrix (3.10–3.13) with image artifacts (human review),
  baseline visual regression (headless), gallery build, docs build,
  PyPI trusted-publishing release.
