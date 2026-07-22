# Exporting: PNG, SVG, PDF, and HTML reports

gtviz treats export as a first-class feature because figures are only useful
once they leave Python — into a website, a slide, a PDF report, or a CI
artifact.

## Single figures

```python
fig, ax = gtviz.dot_plot([62, 48], ["Gave money", "Volunteered"])
paths = gtviz.io.save(fig, "behaviours", formats=("png", "svg", "pdf"))
```

`save` writes to `gtviz.options.output_dir` (override with `directory=`),
creates the directory if needed, and returns the written paths. Supported
formats: `png`, `svg`, `pdf`, `jpg`, `webp`, `eps`.

**Which format when?**

- **SVG** for websites and HTML reports — infinitely crisp, small for
  line-based charts, selectable text.
- **PNG** at `dpi=300` (the default) for slides, docs, and anywhere raster
  is required. Use `dpi=110` for quick previews.
- **PDF** for print and vector hand-off to designers.

## Embedding in web pages

```python
frag = gtviz.io.figure_to_html(fig, embed="svg")   # <div>...<svg>...</div>
frag = gtviz.io.figure_to_html(fig, embed="png")   # base64 <img>, mail-safe
```

`figure_to_svg` and `figure_to_png_base64` give you the raw pieces if you're
templating your own pages.

## Whole reports: ReportBuilder

`ReportBuilder` assembles headings, prose, figures, and tables — in order —
into either a **standalone HTML file** (all figures inlined, zero external
assets, safe to email or publish as-is) or a **multi-page PDF**:

```python
report = (gtviz.io.ReportBuilder(title="Q2 Generosity Report")
          .add_heading("Key trends")
          .add_text("Giving held steady; volunteering rose 3 points.")
          .add_figure(trend_fig, caption="Figure 1. Rolling trends")
          .add_table(summary_table, caption="Table 1. By region")
          .add_html("<p>Any raw HTML fragment works too.</p>"))

report.to_html("q2_report.html")   # figures inlined as SVG (or embed="png")
report.to_pdf("q2_report.pdf")     # figures one per page; tables rendered
```

The HTML output is self-contained by design: inlined SVG means no broken
image links when the file is moved, attached, or served from a CDN. For PDF,
figures export at full vector quality; `HtmlTable`/DataFrame content is
rendered onto a matplotlib table page.

## Headless environments

Set the backend before importing pyplot-heavy code (CI, cron, Lambda):

```python
import matplotlib
matplotlib.use("Agg")
```

The test suite and the CI workflows do exactly this — every chart in the
gallery is rendered headlessly.
