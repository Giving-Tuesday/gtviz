"""Export figures and tables to PNG, SVG, PDF, and standalone HTML reports.

This module replaces the scattered ``plt.savefig("/Volumes/...")`` calls in
the original codebase with three composable pieces:

- :func:`save` -- write one figure to any combination of formats.
- :func:`figure_to_svg` / :func:`figure_to_png_base64` -- embed a figure in
  web content.
- :class:`ReportBuilder` -- assemble figures, HTML tables, and prose into a
  single self-contained HTML file (all figures inlined as SVG) or a
  multi-page PDF. The HTML output can be dropped into a website or attached
  to an email; the PDF is print-ready.

Examples
--------
>>> import gtviz
>>> fig, ax = gtviz.dot_plot([10, 20], ["a", "b"])
>>> gtviz.io.save(fig, "demo", formats=("png", "svg", "pdf"))  # doctest: +SKIP

>>> report = gtviz.io.ReportBuilder(title="Q2 Generosity Report")
>>> report.add_heading("Key trends")
>>> report.add_figure(fig, caption="Figure 1. Generosity behaviours")
>>> report.to_html("q2_report.html")  # doctest: +SKIP
>>> report.to_pdf("q2_report.pdf")    # doctest: +SKIP
"""

from __future__ import annotations

import base64
import html as _html
import io as _io
from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from .config import options

__all__ = [
    "save",
    "figure_to_svg",
    "figure_to_png_base64",
    "figure_to_html",
    "ReportBuilder",
]


def save(
    fig: Figure,
    name: str,
    formats: tuple[str, ...] = ("png",),
    directory: str | Path | None = None,
    dpi: int | None = None,
    transparent: bool | None = None,
) -> list[Path]:
    """Save one figure to one or more formats.

    Parameters
    ----------
    fig:
        The matplotlib figure to save.
    name:
        Base filename (no extension).
    formats:
        Any of ``"png"``, ``"svg"``, ``"pdf"``, ``"jpg"``, ``"webp"``, ``"eps"``.
    directory:
        Target directory; defaults to :data:`gtviz.config.options.output_dir`.
    dpi, transparent:
        Override the global config for raster formats.

    Returns
    -------
    list of pathlib.Path
        The files written.
    """
    directory = Path(directory) if directory else options.output_dir
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for fmt in formats:
        path = directory / f"{name}.{fmt}"
        fig.savefig(
            path,
            format=fmt,
            dpi=dpi or options.dpi,
            bbox_inches="tight",
            transparent=options.transparent if transparent is None else transparent,
        )
        written.append(path)
    return written


def figure_to_svg(fig: Figure) -> str:
    """Render a figure to an SVG string (for inline embedding in HTML)."""
    buf = _io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    svg = buf.getvalue()
    # strip the XML prolog so the fragment can be inlined
    start = svg.find("<svg")
    return svg[start:]


def figure_to_png_base64(fig: Figure, dpi: int | None = None) -> str:
    """Render a figure to a base64-encoded PNG string."""
    buf = _io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi or options.dpi, bbox_inches="tight")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def figure_to_html(fig: Figure, embed: str = "svg", alt: str = "") -> str:
    """Return an HTML fragment embedding the figure.

    Parameters
    ----------
    embed:
        ``"svg"`` (crisp, scalable, default) or ``"png"`` (base64 ``<img>``).
    """
    if embed == "svg":
        return f'<div class="gtviz-figure">{figure_to_svg(fig)}</div>'
    b64 = figure_to_png_base64(fig)
    return (
        f'<div class="gtviz-figure"><img alt="{_html.escape(alt)}" '
        f'src="data:image/png;base64,{b64}" style="max-width:100%"/></div>'
    )


_REPORT_CSS = """
body { font-family: Helvetica, Arial, sans-serif; max-width: 900px;
       margin: 40px auto; color: #1a1a1a; line-height: 1.5; padding: 0 16px; }
h1 { border-bottom: 2px solid #333; padding-bottom: 8px; }
h2 { margin-top: 40px; }
.gtviz-figure { margin: 24px 0; text-align: center; }
.gtviz-figure svg { max-width: 100%; height: auto; }
.gtviz-caption { font-size: 12px; color: #666; font-style: italic; margin-top: 4px; }
"""


class ReportBuilder:
    """Assemble figures, tables, and prose into a single HTML or PDF report.

    Content is added in order via :meth:`add_heading`, :meth:`add_text`,
    :meth:`add_figure`, :meth:`add_table`, and :meth:`add_html`, then exported
    with :meth:`to_html` (self-contained: figures inlined as SVG or base64
    PNG) or :meth:`to_pdf` (one figure per page via
    :class:`matplotlib.backends.backend_pdf.PdfPages`; tables are rendered to
    a matplotlib page).
    """

    def __init__(self, title: str = "", embed: str = "svg"):
        self.title = title
        self.embed = embed
        self._items: list[tuple[str, object, dict]] = []

    # -- content -----------------------------------------------------------
    def add_heading(self, text: str, level: int = 2) -> ReportBuilder:
        """Add a section heading (h2 by default)."""
        self._items.append(("heading", text, {"level": level}))
        return self

    def add_text(self, text: str) -> ReportBuilder:
        """Add a paragraph of prose (plain text; escaped)."""
        self._items.append(("text", text, {}))
        return self

    def add_html(self, fragment: str) -> ReportBuilder:
        """Add a raw HTML fragment (not escaped)."""
        self._items.append(("html", fragment, {}))
        return self

    def add_figure(self, fig: Figure, caption: str = "") -> ReportBuilder:
        """Add a matplotlib figure with an optional caption."""
        self._items.append(("figure", fig, {"caption": caption}))
        return self

    def add_table(self, table, caption: str = "") -> ReportBuilder:
        """Add a :class:`gtviz.tables.HtmlTable` or pandas DataFrame/Styler."""
        self._items.append(("table", table, {"caption": caption}))
        return self

    # -- export ------------------------------------------------------------
    def to_html(self, path: str | Path | None = None) -> str:
        """Render the report to a standalone HTML string; optionally write it."""
        parts = [
            "<!DOCTYPE html><html><head><meta charset='utf-8'>",
            f"<title>{_html.escape(self.title)}</title>",
            f"<style>{_REPORT_CSS}</style></head><body>",
        ]
        if self.title:
            parts.append(f"<h1>{_html.escape(self.title)}</h1>")
        for kind, obj, meta in self._items:
            if kind == "heading":
                lvl = meta["level"]
                parts.append(f"<h{lvl}>{_html.escape(str(obj))}</h{lvl}>")
            elif kind == "text":
                parts.append(f"<p>{_html.escape(str(obj))}</p>")
            elif kind == "html":
                parts.append(str(obj))
            elif kind == "figure":
                parts.append(figure_to_html(obj, embed=self.embed, alt=meta["caption"]))
                if meta["caption"]:
                    parts.append(f"<div class='gtviz-caption'>{_html.escape(meta['caption'])}</div>")
            elif kind == "table":
                parts.append(_table_html(obj))
                if meta["caption"]:
                    parts.append(f"<div class='gtviz-caption'>{_html.escape(meta['caption'])}</div>")
        parts.append("</body></html>")
        doc = "\n".join(parts)
        if path:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(doc, encoding="utf-8")
        return doc

    def to_pdf(self, path: str | Path) -> Path:
        """Render the report to a multi-page PDF (figures one per page)."""
        import matplotlib.pyplot as plt

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with PdfPages(path) as pdf:
            if self.title:
                fig = plt.figure(figsize=(8.5, 11))
                fig.text(0.5, 0.6, self.title, ha="center", va="center", fontsize=22, weight="bold")
                pdf.savefig(fig)
                plt.close(fig)
            for kind, obj, meta in self._items:
                if kind == "figure":
                    pdf.savefig(obj, bbox_inches="tight")
                elif kind == "table":
                    fig = _table_to_figure(obj, meta.get("caption", ""))
                    if fig is not None:
                        pdf.savefig(fig, bbox_inches="tight")
                        plt.close(fig)
        return path


def _table_html(table) -> str:
    """Best-effort HTML for HtmlTable, Styler, or DataFrame."""
    if hasattr(table, "to_html"):
        return table.to_html()
    if hasattr(table, "_repr_html_"):
        return table._repr_html_()
    return str(table)


def _table_to_figure(table, caption: str = ""):
    """Render a DataFrame-ish table onto a matplotlib figure for PDF export."""
    import matplotlib.pyplot as plt
    import pandas as pd

    df = getattr(table, "df", None)
    if df is None and isinstance(table, pd.DataFrame):
        df = table
    if df is None and hasattr(table, "data"):  # pandas Styler
        df = table.data
    if df is None:
        return None
    nrows = len(df) + 1
    fig, ax = plt.subplots(figsize=(min(11, 2 + 1.4 * len(df.columns)), 0.5 + 0.35 * nrows))
    ax.axis("off")
    tab = ax.table(
        cellText=df.astype(str).values,
        colLabels=[str(c) for c in df.columns],
        rowLabels=[str(i) for i in df.index],
        loc="center",
    )
    tab.auto_set_font_size(False)
    tab.set_fontsize(9)
    if caption:
        ax.set_title(caption, fontsize=11)
    return fig
