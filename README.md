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
