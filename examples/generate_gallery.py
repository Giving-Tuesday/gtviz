#!/usr/bin/env python3
"""Generate the full chart gallery.

Renders one example of every gtviz chart type using synthetic survey data and
writes PNG + SVG to ``docs/_static/gallery/`` (for the docs) — plus a
combined HTML report and PDF demonstrating the export pipeline.

Run: ``python examples/generate_gallery.py``
CI runs this in the ``gallery`` job and uploads the directory as an artifact.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import gtviz  # noqa: E402
from gtviz import io  # noqa: E402

OUT = ROOT / "docs" / "_static" / "gallery"


def synthetic_survey(n: int = 4000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    weeks = rng.integers(1, 27, n)
    df = pd.DataFrame(
        {
            "collection_week": weeks,
            "WEIGHT": rng.uniform(0.5, 1.5, n),
            "gave_money": rng.binomial(1, 0.55, n),
            "volunteered": rng.binomial(1, 0.30, n),
            "gave_items": rng.binomial(1, 0.40, n),
            "solicited": rng.binomial(1, 0.45, n),
            "belonging": rng.integers(1, 6, n),
            "civic_intent": rng.integers(1, 6, n),
            "trust": rng.integers(1, 6, n),
            "age_group": rng.choice(["18-34", "35-54", "55+"], n),
            "region": rng.choice(["Northeast", "South", "Midwest", "West"], n),
            "gender": rng.choice(["Woman", "Man"], n),
            "Fips": rng.choice(["01001", "06037", "08069", "12086", "36061", "48201"], n),
        }
    )
    df["real_date"] = pd.Timestamp("2025-01-06") + pd.to_timedelta((df["collection_week"] - 1) * 7, unit="D")
    return df


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gtviz.theme.use("report")
    df = synthetic_survey()
    figures: list[tuple[str, str]] = []  # (name, caption)

    def emit(fig, name: str, caption: str):
        io.save(fig, name, formats=("png", "svg"), directory=OUT, dpi=110)
        figures.append((name, caption))
        plt.close(fig)

    fig, _ = gtviz.dot_plot([62, 48, 31], ["Gave money", "Volunteered", "Gave items"],
                            error=[3, 3, 2], title="dot_plot")
    emit(fig, "dot_plot", "Basic dot plot with 95% error bars")

    fig, _ = gtviz.grouped_dot_plot(
        df, "age_group", ["gave_money", "volunteered", "gave_items"],
        metric_labels={"gave_money": "Gave money", "volunteered": "Volunteered",
                       "gave_items": "Gave items"},
        error=True, title="grouped_dot_plot")
    emit(fig, "grouped_dot_plot", "Groups compared across metrics")

    sub = df[df["collection_week"].isin([1, 10, 20])].copy()
    sub["quarter"] = sub["collection_week"].map({1: "Q1", 10: "Q2", 20: "Q3"})
    fig, _ = gtviz.trend_dot_plot(sub, "quarter", ["gave_money", "volunteered"],
                                  title="trend_dot_plot", max_percent=80)
    emit(fig, "trend_dot_plot", "Metric movement across periods")

    fig, _ = gtviz.parallel_bars(
        df, ["gave_money", "volunteered", "gave_items", "solicited"],
        ["Gave money", "Volunteered", "Gave items", "Solicited"],
        splits=[("gender", "Woman"), ("age_group", "18-34")],
        sub_titles=["Women", "18-34"], title="parallel_bars")
    emit(fig, "parallel_bars", "Baseline vs subgroups with point-difference labels")

    fig, _ = gtviz.rolling_trend(df, ["gave_money", "volunteered"],
                                 labels={"gave_money": "Gave money", "volunteered": "Volunteered"},
                                 title="rolling_trend")
    emit(fig, "rolling_trend", "3-week rolling weighted trends")

    fig, _ = gtviz.split_line_plot(df, "gave_money", split="age_group", title="split_line_plot")
    emit(fig, "split_line_plot", "One trend line per group level")

    events = {df["real_date"].quantile(0.3): "Crisis A", df["real_date"].quantile(0.7): "Crisis B"}
    fig, _ = gtviz.annotated_event_plot(df, "gave_money", events, title="annotated_event_plot")
    emit(fig, "annotated_event_plot", "Trend with labeled event markers")

    fig, _ = gtviz.venn(df, ["gave_money", "volunteered", "gave_items"],
                        labels=["Money", "Volunteer", "Items"], title="venn")
    emit(fig, "venn", "3-set behaviour overlap (percent of sample)")

    fig, _ = gtviz.weighted_heatmap(df, "region",
                                    ["gave_money", "volunteered", "gave_items", "solicited"],
                                    title="weighted_heatmap")
    emit(fig, "weighted_heatmap", "Weighted means: groups x metrics")

    fig, _ = gtviz.funnel([0.45, 0.30, 0.12], ["Solicited", "Responded", "Recurring"],
                          title="funnel")
    emit(fig, "funnel", "Stage-share funnel")

    fig, _ = gtviz.donut([40, 30, 20, 10], ["Planners", "Spontaneous", "Mixed", "Non-givers"],
                         title="donut")
    emit(fig, "donut", "Ring chart")

    fig, _ = gtviz.likert_bars(
        df, ["belonging", "civic_intent", "trust"],
        item_labels={"belonging": "I feel I belong", "civic_intent": "Civic intent",
                     "trust": "Trust in others"},
        answer_labels=["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"],
        title="likert_bars")
    emit(fig, "likert_bars", "100% stacked Likert distributions")

    tab = gtviz.choropleth_table(df, "gave_money", region_col="Fips")
    fig, _ = gtviz.scale_bar(tab.attrs["scale_min"] * 100, tab.attrs["scale_max"] * 100,
                             caption="% gave money, by county")
    emit(fig, "scale_bar", "Choropleth scale-bar legend")

    # export pipeline demo: standalone HTML report + PDF
    table = gtviz.HtmlTable(
        pd.DataFrame({"Q1": [50, 28], "Q2": [55, 31]}, index=["Gave money", "Volunteered"]),
        title="Table 1. Quarterly comparison", sample_sizes=[1200, 1180])
    report = io.ReportBuilder(title="gtviz sample report")
    report.add_text("All figures below are rendered by gtviz and inlined as SVG.")
    fig, _ = gtviz.dot_plot([62, 48, 31], ["Gave money", "Volunteered", "Gave items"],
                            title="Generosity behaviours")
    report.add_figure(fig, caption="Figure 1. Generosity behaviours")
    report.add_table(table, caption="Weighted percent of respondents")
    report.to_html(OUT / "sample_report.html")
    report.to_pdf(OUT / "sample_report.pdf")
    plt.close("all")

    # gallery index markdown for docs
    lines = ["# Gallery", "",
             "Every chart type, rendered from synthetic survey data by",
             "`examples/generate_gallery.py`.", ""]
    for name, caption in figures:
        lines += [f"## `{name}`", "", caption, "",
                  f"![{name}](_static/gallery/{name}.png)", ""]
    lines += ["## Export pipeline", "",
              "The same run also produces a standalone "
              "[HTML report](_static/gallery/sample_report.html) with figures inlined as SVG, "
              "and a print-ready [PDF](_static/gallery/sample_report.pdf).", ""]
    (ROOT / "docs" / "gallery.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(figures)} gallery figures to {OUT}")


if __name__ == "__main__":
    main()
