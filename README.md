# gtviz

[![PyPI version](https://img.shields.io/pypi/v/gtviz.svg)](https://pypi.org/project/gtviz/)
[![Python versions](https://img.shields.io/pypi/pyversions/gtviz.svg)](https://pypi.org/project/gtviz/)
[![CI](https://github.com/Giving-Tuesday/gtviz/actions/workflows/ci.yml/badge.svg)](https://github.com/Giving-Tuesday/gtviz/actions/workflows/ci.yml)
[![Docs](https://readthedocs.org/projects/gtviz/badge/?version=latest)](https://gtviz.readthedocs.io/en/latest/)
[![codecov](https://codecov.io/gh/Giving-Tuesday/gtviz/branch/main/graph/badge.svg)](https://codecov.io/gh/Giving-Tuesday/gtviz)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Publication-quality survey data visualization, refactored from the GivingPulse
quarterly-report codebase into a clean, survey-agnostic library.

## The brand theme: defaults that override matplotlib everywhere

The point of gtviz: **call any chart with data only and get the published
report look.** `gtviz.theme.use("report")` applies the brand rcParams
globally, and every function's styling defaults were audited line-by-line
from the production report code. Highlights (full table:
[Design defaults & override policy](https://gtviz.readthedocs.io/en/latest/guides/design_defaults.html)):

| element | brand default | one-off override |
|---|---|---|
| titles | bold, left-aligned + gray "n = 5,387 respondents" subtitle | `title=`, `subtitle=`, `n=` |
| spines / grid | top+right spines off; no grid on line charts; dotted 0.8-gray lanes on dot plots | `grid=True`, `box=True` |
| lines | width 2.5, tableau (tab10) cycle, **no markers** | `linewidth=`, `marker=`, `colors=` |
| legends | frameless; inside for trends, outside-right for dot/likert, top row for band bars | `legend=`, `legend_loc=` |
| venn | **area-proportional**, steel-blue/turquoise/green sets @ alpha 0.6, % of sample | `weighted=False`, `colors=`, `set_percentages=True` |
| band scale | red → orange → olive → green → blue (`palette["bands5"]`) | `colors=` |
| dot plots | `.` marker size 10, same-color hline errors, grey "Everyone" first, `n=` in legend, 25-char label wrap | `markersize=`, `show_n=False`, `wrap=` |
| benchmarks | gray circle bubbles with colored scores; dotted average lines with captions | `benchmarks=`, `benchmark=` |
| tables | `#4e79a7` accent, ±5pt green/red cell shading, zebra rows | `HtmlTable(...)` args |
| weights | everything weighted via `weights="auto"` (set the column once) | `weights=None` / column name |
| export | 300 dpi; PNG/SVG/PDF/JPG/WebP; HTML reports with inlined SVG | `gtviz.io.save`, `ReportBuilder` |

All palette tokens live in `gtviz.theme.palette` — change a hex once, every
chart and table follows.

## API structure

```
gtviz
├── theme        use("report"|"publication", font=...), palette tokens
├── config       set_options(weight_col=, output_dir=, dpi=)
├── charts
│   ├── dots     dot_plot · grouped_dot_plot · trend_dot_plot
│   ├── bars     parallel_bars (baseline vs subgroups, ± diff labels)
│   ├── lines    rolling_trend · split_line_plot · annotated_event_plot
│   ├── civic    contribution_bars · range_dot_plot (dumbbell + benchmark)
│   │            · arrow_range_plot · nested_bars (layered subsets)
│   ├── stacked  stacked_bars (100% band bars) · banded_shares
│   ├── likert   likert_bars (diverging answer distributions)
│   ├── venn     venn · venn_from_counts
│   ├── heatmap  weighted_heatmap
│   ├── funnel   funnel · funnel_from_columns
│   ├── donut    donut
│   └── waffle   waffle  (extra: pip install gtviz[waffle])
├── tables       HtmlTable (publication CSS) · compare_periods · pivot_change_table
├── maps         choropleth_table (FIPS→hex) · scale_bar
├── stats        rolling_summary · period_change · subgroup_summary ·
│                chi_squared_matrix · build_filter · likert utils · aggs
├── io           save (png/svg/pdf/…) · figure_to_html · ReportBuilder (HTML+PDF)
└── pipeline     read_pipeline (Delta/Spark) · process() · sklearn-style steps
                 (ScoreBelonging · ScoreCivicIntent · AssignPew · AssignActivism ·
                  AssignCountyTypes · CivicQuartile)
```

Every chart accepts `ax=` and returns `(fig, ax)`; nothing calls
`plt.show()` for you.

**Charts:** dot plots (single, grouped, trend), parallel bar panels, rolling trend
lines, venn diagrams (2/3 set, filtered or from pre-aggregated counts), weighted
heatmaps, funnels, donuts, diverging Likert bars.
**Tables:** publication CSS/HTML tables with zebra striping, high/low cell shading,
multi-index rollups; period-over-period comparison tables.
**Maps:** county/FIPS choropleth color tables (for SVG map filling) + scale-bar legends.
**Export:** PNG, SVG, PDF, standalone HTML reports (figures embedded as SVG),
suitable for websites or print reports.

```python
import gtviz
gtviz.theme.use("report")

fig, ax = gtviz.dot_plot([62, 48, 31], ["Gave money", "Volunteered", "Gave items"],
                         error=[3, 3, 2], title="Generosity in Q2")
gtviz.io.save(fig, "generosity_q2", formats=("png", "svg", "pdf"))
```

## Install

```
pip install gtviz            # core
pip install gtviz[waffle]    # + waffle charts
```

## Docs

Full documentation, gallery, and migration guide from the original `gp_reports`
repo: https://gtviz.readthedocs.io

## Development

```
pip install -e .[dev,docs]
pytest                                  # unit tests; writes chart images to tests/output/
python examples/generate_gallery.py    # regenerate gallery images
```

CI runs lint + tests on every push and uploads rendered chart images as build
artifacts for **human review**; a **headless** job compares rendered images
against committed baselines in `tests/baseline/`. See `.github/workflows/`.

