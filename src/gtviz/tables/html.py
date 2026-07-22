"""Publication-quality CSS/HTML tables.

Port of ``convert_df_to_html`` from the original ``visualization_functions.py``
into an :class:`HtmlTable` object that renders identically in Databricks,
Jupyter, and plain HTML export (via ``_repr_html_``), and fixes the original
``return_code`` bug (it re-displayed instead of returning the HTML string).

Features preserved: zebra row striping, per-row high/low conditional cell
shading against the row mean, multi-index rollups (level-0 labels are not
repeated), title, footer, and sample-size footer rows.
"""

from __future__ import annotations

import html as _html
from pathlib import Path

import pandas as pd

from ..theme import palette

_TABLE_CSS = """
<style>
    .pub-table-wrapper {{ margin: 30px 0; font-family: Helvetica, Arial, sans-serif; }}
    .pub-table-title {{
        font-size: 14px; font-weight: bold; margin-bottom: 4px;
        color: #1a1a1a; border-bottom: 2px solid #333; padding-bottom: 6px;
    }}
    .pub-table-subtitle {{ font-size: 11px; color: #666; margin-bottom: 10px; font-style: italic; }}
    .pub-table {{
        border-collapse: collapse; width: 100%; font-size: 12px;
        border-top: 2px solid #333; border-bottom: 2px solid #333;
    }}
    .pub-table th {{
        background: #e5e5e5; text-align: center; padding: 8px 12px;
        border-bottom: 1px solid #333; font-weight: bold; font-size: 11px;
    }}
    .pub-table th:first-child {{ text-align: left; }}
    .pub-table td {{ padding: 6px 12px; border-bottom: 1px solid #ddd; text-align: center; }}
    .pub-table td:first-child {{ text-align: left; font-size: 11px; }}
    .pub-table tr:last-child td {{ border-bottom: none; }}
    .pub-table tr:hover {{ background: #fafaf5; }}
    .bar-fill {{
        display: inline-block; height: 12px; border-radius: 2px;
        background: {accent}; vertical-align: middle;
    }}
</style>
"""

_LABEL_CSS = "text-align:left; border-bottom:none; font-weight: bold; font-size: 11px;"


class HtmlTable:
    """A publication-styled HTML table built from a pandas DataFrame.

    Parameters
    ----------
    df:
        Input DataFrame. Plain or MultiIndex row indexes are supported; for
        a MultiIndex, repeated level-0 labels are rolled up (blanked) like
        the original report tables.
    title:
        Table title rendered above the table.
    subtitle:
        Small italic line under the title (the TODO from the original code,
        now implemented).
    zebra:
        Alternate light-gray row shading.
    high_low_shading:
        Shade numeric cells green/red when they differ from the row mean by
        more than ``high_low_threshold`` (percentage points).
    high_low_threshold:
        Deviation from the row mean, in points, where shading starts.
    hide_index:
        Omit the index column entirely.
    footer:
        Raw HTML placed in a final ``<tfoot>`` row.
    sample_sizes:
        List of per-column sample sizes; renders a "Sample size:" footer row
        (overrides ``footer``).

    Examples
    --------
    >>> import pandas as pd
    >>> from gtviz.tables import HtmlTable
    >>> t = HtmlTable(pd.DataFrame({"Q1": [50, 40], "Q2": [55, 38]},
    ...               index=["Gave money", "Volunteered"]),
    ...               title="Generosity by quarter", sample_sizes=[1200, 1180])
    >>> html = t.to_html()          # standalone string
    >>> t                            # renders in a notebook  # doctest: +SKIP
    """

    def __init__(
        self,
        df: pd.DataFrame,
        title: str | None = None,
        subtitle: str | None = None,
        zebra: bool = True,
        high_low_shading: bool = True,
        high_low_threshold: float = 5,
        hide_index: bool = False,
        footer: str | None = None,
        sample_sizes: list | None = None,
    ):
        self.df = df
        self.title = title
        self.subtitle = subtitle
        self.zebra = zebra
        self.high_low_shading = high_low_shading
        self.high_low_threshold = high_low_threshold
        self.hide_index = hide_index
        self.footer = footer
        self.sample_sizes = sample_sizes

    # -- rendering ----------------------------------------------------------
    def _header_html(self) -> str:
        df = self.df
        if self.hide_index:
            first = ""
        elif isinstance(df.index, pd.MultiIndex):
            first = "".join(
                f"<th>{str(n or '').title().replace('_', ' ')}</th>" for n in df.index.names
            )
        elif df.index.name is not None:
            first = f"<th>{_html.escape(str(df.index.name))}</th>"
        else:
            first = "<th></th>"
        cols = "".join(
            f'<th style="text-align:left;">{_html.escape(str(c)).title()}</th>' for c in df.columns
        )
        return first + cols

    def _rows_html(self) -> str:
        df = self.df
        rows = []
        last_level0 = None
        for count, (idx, row) in enumerate(df.iterrows()):
            numeric = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in row)
            row_avg = row.mean() if numeric else None
            zebra = "" if (count % 2 == 0 or not self.zebra) else f"background-color: {palette['zebra']};"
            cells = []
            if not self.hide_index:
                if isinstance(idx, tuple):
                    parts = []
                    for level_i, level in enumerate(idx):
                        if level_i == 0 and last_level0 == level:
                            parts.append(f'<td style="{_LABEL_CSS} {zebra}">&nbsp;</td>')
                        else:
                            parts.append(f'<td style="{_LABEL_CSS} {zebra}">{_html.escape(str(level))}</td>')
                    last_level0 = idx[0]
                    cells.append("".join(parts))
                else:
                    cells.append(f'<td style="{_LABEL_CSS} {zebra}">{_html.escape(str(idx))}</td>')
            for cell in row:
                shade = zebra
                if self.high_low_shading and row_avg is not None:
                    diff = cell - row_avg
                    if diff > self.high_low_threshold:
                        shade = f"background-color: {palette['high']};"
                    elif diff < -self.high_low_threshold:
                        shade = f"background-color: {palette['low']};"
                cells.append(f'<td style="text-align:left; border-bottom:none; {shade}">{cell}</td>')
            rows.append(f"<tr>{''.join(cells)}</tr>")
        return "\n".join(rows)

    def _footer_html(self) -> str:
        if self.sample_sizes:
            tds = "".join(f'<td style="text-align:left;">{n}</td>' for n in self.sample_sizes)
            return f'<tfoot><tr><td style="{_LABEL_CSS}">Sample size:</td>{tds}</tr></tfoot>'
        if self.footer:
            return f"<tfoot><tr>{self.footer}</tr></tfoot>"
        return ""

    def to_html(self) -> str:
        """Return the complete HTML fragment (CSS included)."""
        css = _TABLE_CSS.format(accent=palette["accent"])
        title = f'<div class="pub-table-title">{_html.escape(self.title)}</div>' if self.title else ""
        subtitle = (
            f'<div class="pub-table-subtitle">{_html.escape(self.subtitle)}</div>' if self.subtitle else ""
        )
        return (
            f"{css}\n<div class='pub-table-wrapper'>{title}{subtitle}"
            f"<table class='pub-table'><thead><tr>{self._header_html()}</tr></thead>"
            f"<tbody>{self._rows_html()}</tbody>{self._footer_html()}</table></div>"
        )

    def _repr_html_(self) -> str:  # Jupyter / Databricks rich display
        return self.to_html()

    def save(self, path: str | Path) -> Path:
        """Write the table as a standalone ``.html`` file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{self.to_html()}</body></html>"
        path.write_text(doc, encoding="utf-8")
        return path

    def show(self) -> None:
        """Display in an IPython environment (``displayHTML`` equivalent)."""
        from IPython.display import HTML, display  # lazy; optional dependency

        display(HTML(self.to_html()))
