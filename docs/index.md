# gtviz

**Publication-quality survey data visualization** — dot plots, comparison
tables, venn diagrams, weighted heatmaps, choropleth color tables, and a
complete PNG/SVG/PDF/HTML export pipeline. Refactored from the GivingPulse
quarterly-report codebase into a clean, survey-agnostic library.

```python
import gtviz
gtviz.theme.use("report")

fig, ax = gtviz.dot_plot([62, 48, 31],
                         ["Gave money", "Volunteered", "Gave items"],
                         error=[3, 3, 2], title="Generosity in Q2")
gtviz.io.save(fig, "generosity_q2", formats=("png", "svg", "pdf"))
```

## Why gtviz?

Survey reporting has a repeating shape: weighted respondent-level data in,
publication-ready figures and tables out, every quarter. gtviz packages the
charts a real quarterly research report actually uses — refined across three
years of production reports — behind one consistent API:

- Every chart accepts `ax=` and returns `(fig, ax)` — composable with any
  matplotlib layout, and nothing ever calls `plt.show()` for you.
- Weighted statistics are first-class: pass `weights="auto"` and set your
  weight column once in `gtviz.set_options`.
- Everything exports: PNG/SVG/JPG/PDF per figure, or a whole report to
  standalone HTML (figures inlined as SVG) and multi-page PDF.
- No notebook state, no hard-coded columns, no hidden globals.

```{toctree}
:maxdepth: 2
:caption: Guides

guides/getting_started
guides/charts_tour
guides/tables
guides/exporting
guides/theming
guides/design_defaults
guides/maps
guides/pipeline
guides/ci_images
guides/migration
```

```{toctree}
:maxdepth: 1
:caption: Gallery

gallery
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/charts
api/tables
api/maps
api/stats
api/io
api/theme_config
api/pipeline
```
