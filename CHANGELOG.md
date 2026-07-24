# Changelog

## 0.6.0 (2026-07-23)

- Reference files resolve without hard-coded paths: `AssignPew` /
  `AssignCountyTypes` now default `decoder=`/`typology=` to `None` and
  resolve from `gtviz.set_options(pew_decoder=, county_typology=)` or the
  `GTVIZ_PEW_DECODER` / `GTVIZ_COUNTY_TYPOLOGY` env vars, with an actionable
  `FileNotFoundError` when nothing is configured or the file is missing.
- `AssignPew`: robust orientation + type labeling. The decoder is oriented
  by shape (works for the production questions x types layout with
  question-text row labels), and assigned type names are carried from the
  decoder's own columns regardless of their order -- fixes a broadcast error
  and silent type-mislabeling on real reference files.
- `default_pipeline` includes the county/pew steps whenever a reference is
  configured (explicitly or via options/env); pass `typology=False` /
  `pew_decoder=False` to force-skip.
- New tests: transposed + reordered decoder regression, and
  config/env/error resolution paths.

## 0.5.0 (2026-07-23)

**Civic-intent chart family** (the report figures 2.2/2.4/3.x/A.1/A.2/A.5):

- `contribution_bars`: horizontal tab:blue bars with signed white in-bar
  labels ("+27"); optional gray benchmark bubbles beside each bar.
- `range_dot_plot`: dumbbell ranges with low/high endpoint scores in gray
  bubbles (red/green text), gap labeled mid-line, dotted benchmark line
  with caption, optional right-margin labels.
- `arrow_range_plot`: directional arrow ranges per series (linewidth 3),
  decreases rendered tab:red, dotted per-series average lines.
- `nested_bars`: layered subset bars (gray total, cyan subset, blue core).
- `likert_bars`: spines removed, legend moved fully outside (frameless,
  no overlap).
- Gallery: four new figures. **Baselines changed — re-run "Bless baselines".**

## 0.4.0 (2026-07-23)

**Brand-style release: chart output now matches the published report figures.**

- Theme "report" profile: bold left-aligned titles, no top/right spines,
  2.5 line width, frameless legends; new `brand_title` gray
  "n = X respondents" subtitle supported via `subtitle=`/`n=` on charts.
- `venn`: **area-proportional by default** with brand set colors (steel
  blue / turquoise / green, alpha 0.6), automatic n-subtitle, optional
  per-set totals under labels (`set_percentages=True`).
- `rolling_trend` / `split_line_plot`: thick plain tableau-cycle lines, no
  markers, frameless inside legend (report figures); legacy gray-first
  palette available via `palette["split_series"]`.
- New `stacked_bars` + `banded_shares`: 100% stacked horizontal band bars
  (the civic-intent-by-country figure) with the red→orange→olive→green→blue
  scale and top legend.
- `likert_bars`: 5-answer default now the brand band scale; `legend=`
  placement options.
- `waffle`: brand tab10 sequence, right-side legend with values in labels,
  `block_value=` ("1 box = $2B") scaling; re-exported at top level;
  rendered in the docs gallery (pywaffle added to docs extra).
- Fix: `weights="auto"` now falls back to unweighted when the configured
  weight column is absent instead of raising KeyError.
- Gallery regenerated with the brand looks. **Baselines changed — re-run the
  "Bless baselines" workflow after merging.**

## 0.3.3 (2026-07-23)

- PyPI packaging: trimmed sdist (excludes baseline/gallery images — 580K to
  72K), corrected `[project.urls]` to the `Giving-Tuesday` org, added
  Homepage/Changelog/Issues links for the PyPI sidebar.
- Hardened `release.yml`: separate build/verify job (`twine check` +
  tag-equals-version guard), Test PyPI dry-run via `workflow_dispatch`, and
  trusted-publishing `pypi` job on `v*` tags.
- README badges: PyPI version + Python versions, CI status, Read the Docs,
  Codecov coverage, Ruff, license.
- CI uploads coverage to Codecov from the 3.12 leg.
- New guide: *Publishing* (one-time PyPI/RTD/Codecov setup + release
  checklist).

## 0.3.2 (2026-07-23)

- New `tools/generate_report.py` + `report` job in CI: aggregates JUnit test
  results, coverage XML, ruff JSON, and visual-regression output into one
  Markdown quality report (pass rate, failures by type/file, least-covered
  modules, lint by rule). Published to the GitHub run summary and uploaded
  as the `quality-report` artifact (90-day retention).
- CI now emits machine-readable report inputs (`--junitxml`,
  `--cov-report=xml`, ruff `--output-format=json`) per matrix leg;
  `test` matrix uses `fail-fast: false` so one Python version failing no
  longer cancels the others.
- Visual-regression threshold raised to 3.0% (cross-runner font tolerance).

## 0.3.1 (2026-07-22)

- Add `jinja2` as a core dependency (required by the pandas Styler used in
  `compare_periods(style=True)`; previously only present via dev extras, so
  clean installs failed).
- Fix pandas downcasting `FutureWarning` in pipeline scoring steps by making
  numeric conversions explicit (`.replace(...).infer_objects()`), and drop
  the deprecated `copy=` keyword so the code is clean on both pandas 2.x and
  3.x.
- Tests now mirror the production runtime instead of suppressing signals:
  `future.no_silent_downcasting` is enabled on pandas 2.x, and pytest treats
  warnings as errors (third-party-only deprecations allowlisted). Verified
  green under pandas 2.3 and 3.0.

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
