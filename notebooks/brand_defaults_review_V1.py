# Databricks notebook source
# MAGIC %md
# MAGIC # gtviz — Brand Defaults Review (V1)
# MAGIC
# MAGIC Runs **every gtviz chart, table, and export path with zero styling kwargs** so you can judge
# MAGIC whether the brand defaults (audited from `gp_reports`) look right in Databricks, then shows
# MAGIC the override kwarg next to each so tweaks are one edit away.
# MAGIC
# MAGIC Data source is switchable below: synthetic (runs anywhere) or the production pipeline.

# COMMAND ----------

# MAGIC %md ## Setup
# MAGIC If this notebook lives in a Databricks Repo alongside the package, the editable install below
# MAGIC picks up local `src/` changes on re-run — edit a default in `theme.py`, re-run, re-judge.

# COMMAND ----------

# MAGIC %pip install -e "$(dirname "$(dirname "$PWD")")" --quiet
# If the relative install fails (workspace path quirks), use the explicit repo path instead:
# %pip install -e /Workspace/Repos/<you>/gtviz --quiet

# COMMAND ----------

dbutils.library.restartPython()  # noqa: F821

# COMMAND ----------

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import gtviz

print("gtviz", gtviz.__version__)
gtviz.theme.use("report")  # brand rcParams: dpi 300, 14pt fonts, 16pt titles

# COMMAND ----------

# MAGIC %md ## Data source
# MAGIC `USE_PIPELINE = True` reads the production Delta table via `gtviz.pipeline.read_pipeline`
# MAGIC and runs the scoring batch; `False` builds a synthetic frame with the same shape.

# COMMAND ----------

USE_PIPELINE = False  # flip to True on a cluster with prod_curated access
YEAR = 2026

if USE_PIPELINE:
    df, meta = gtviz.pipeline.read_pipeline(year=YEAR)
    df = gtviz.pipeline.process(
        df,
        typology="/Volumes/sandbox_annie/giving_pulse/misc/2023-Typology-(15-county-types).xlsx",
        pew_decoder="/Volumes/sandbox_annie/giving_pulse/pew_decoder/pew_political_spectrum_questions.csv",
        verbose=True,
    )
    # map production columns to the demo names used below as needed
else:
    rng = np.random.default_rng(42)
    n = 4000
    df = pd.DataFrame(
        {
            "collection_week": rng.integers(1, 27, n),
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
    df["real_date"] = pd.Timestamp(f"{YEAR}-01-05") + pd.to_timedelta((df["collection_week"] - 1) * 7, "D")

BEHAVIOURS = ["gave_money", "volunteered", "gave_items"]
BEHAVIOUR_LABELS = {"gave_money": "Gave money", "volunteered": "Volunteered", "gave_items": "Gave items"}
print(len(df), "rows")

# COMMAND ----------

# MAGIC %md ## 1. Dot plots
# MAGIC Brand defaults under review: `.` marker size 10, same-color hline error intervals,
# MAGIC dotted 0.8-gray y-grid, ticks both sides, **no value labels**.

# COMMAND ----------

fig, ax = gtviz.dot_plot([62, 48, 31], list(BEHAVIOUR_LABELS.values()), error=[3, 3, 2],
                         title="dot_plot — defaults")
plt.show()
# overrides: marker="o", markersize=8, datalabels=True, wrap=25

# COMMAND ----------

# grouped: grey-first series, no box, frameless legend @ (1, 0.85), n= counts, 25-char wrap
fig, ax = gtviz.grouped_dot_plot(df, "age_group", BEHAVIOURS, metric_labels=BEHAVIOUR_LABELS,
                                 error=True, title="grouped_dot_plot — defaults")
plt.show()
# overrides: box=True, show_n=False, legend_anchor=(1, 1), colors=[...], xrange=(0, 100)

# COMMAND ----------

sub = df[df["collection_week"].isin([1, 10, 20])].copy()
sub["quarter"] = sub["collection_week"].map({1: "Q1", 10: "Q2", 20: "Q3"})
fig, ax = gtviz.trend_dot_plot(sub, "quarter", ["gave_money", "volunteered"],
                               metric_labels=BEHAVIOUR_LABELS, max_percent=80,
                               title="trend_dot_plot — defaults")
plt.show()

# COMMAND ----------

# MAGIC %md ## 2. Parallel bars — width 0.75, alpha 0.5, ± point-difference labels vs baseline

# COMMAND ----------

fig, axes = gtviz.parallel_bars(
    df, BEHAVIOURS + ["solicited"],
    list(BEHAVIOUR_LABELS.values()) + ["Solicited"],
    splits=[("gender", "Woman"), ("age_group", "18-34")],
    sub_titles=["Women", "18-34"],
    title="parallel_bars — defaults",
)
plt.show()

# COMMAND ----------

# MAGIC %md ## 3. Trend lines
# MAGIC Under review: plain solid lines (mpl cycle, **no markers**), legend @ (1,1), **no grid**,
# MAGIC optional gray current-period shading.

# COMMAND ----------

fig, ax = gtviz.rolling_trend(df, BEHAVIOURS, labels=BEHAVIOUR_LABELS,
                              shade=(20, 26),  # gray "current period" band, original style
                              title="rolling_trend — defaults + shade")
plt.show()
# overrides: marker="o", grid=True, colors=[...], legend_anchor="best"

# COMMAND ----------

fig, ax = gtviz.split_line_plot(df, "gave_money", split="age_group",
                                title="split_line_plot — defaults")
plt.show()
# palette under review: light-gray-first split_series; override colors=[...]

# COMMAND ----------

events = {df["real_date"].quantile(0.3): "Crisis A", df["real_date"].quantile(0.7): "Crisis B"}
fig, ax = gtviz.annotated_event_plot(df, "gave_money", events, title="annotated_event_plot — defaults")
plt.show()

# COMMAND ----------

# MAGIC %md ## 4. Venn — equal circles, % of sample, title 20pt pad 30

# COMMAND ----------

fig, ax = gtviz.venn(df, BEHAVIOURS, labels=list(BEHAVIOUR_LABELS.values()),
                     title="venn — defaults")
plt.show()
# overrides: weighted=True (area-proportional), as_percent=False, filter=mask

# COMMAND ----------

# MAGIC %md ## 5. Heatmap — **open decision #3**: YlGnBu vs magma (original used seaborn's dark default)

# COMMAND ----------

fig, ax = gtviz.weighted_heatmap(df, "region", BEHAVIOURS + ["solicited"],
                                 title="weighted_heatmap — YlGnBu (current default)")
plt.show()
fig, ax = gtviz.weighted_heatmap(df, "region", BEHAVIOURS + ["solicited"], cmap="magma",
                                 title="weighted_heatmap — magma (closest to original)")
plt.show()

# COMMAND ----------

# MAGIC %md ## 6. Funnel / donut / Likert

# COMMAND ----------

fig, ax = gtviz.funnel([0.45, 0.30, 0.12], ["Solicited", "Responded", "Recurring"],
                       title="funnel — defaults (2.8 bands, 0.2 gaps)")
plt.show()

# COMMAND ----------

fig, ax = gtviz.donut([40, 30, 20, 10], ["Planners", "Spontaneous", "Mixed", "Non-givers"],
                      title="donut — defaults (no % labels)")
plt.show()
fig, ax = gtviz.donut([40, 30, 20, 10], ["Planners", "Spontaneous", "Mixed", "Non-givers"],
                      autopct="%1.0f%%", title="donut — autopct override")
plt.show()

# COMMAND ----------

fig, ax = gtviz.likert_bars(
    df, ["belonging", "civic_intent", "trust"],
    item_labels={"belonging": "I feel I belong", "civic_intent": "Civic intent", "trust": "Trust in others"},
    answer_labels=["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"],
    title="likert_bars — defaults",
)
plt.show()
# 5-point falls back to RdYlGn ramp; 4-point batteries get the brand tab:red→green palette.
# overrides: reverse_answers=True, highlight_agree=True, colors=[...]

# COMMAND ----------

# MAGIC %md ## 7. Maps — color table + matching scale bar

# COMMAND ----------

tab = gtviz.choropleth_table(df, "gave_money", region_col="Fips")
display(tab)  # noqa: F821  — region → hex, ready to fill the SVG county map
fig, ax = gtviz.scale_bar(tab.attrs["scale_min"] * 100, tab.attrs["scale_max"] * 100,
                          caption="% gave money, by county")
plt.show()

# COMMAND ----------

# MAGIC %md ## 8. Tables — brand CSS (accent #4e79a7, ±5pt high/low shading, zebra)

# COMMAND ----------

summary = gtviz.stats.subgroup_summary(df, "region", BEHAVIOURS)
table = gtviz.HtmlTable(summary, title="Behaviours by region", subtitle="Weighted % of respondents")
displayHTML(table.to_html())  # noqa: F821

# COMMAND ----------

now, prev = df[df["collection_week"] > 13], df[df["collection_week"] <= 13]
styled = gtviz.compare_periods(now, prev, BEHAVIOURS, labels=BEHAVIOUR_LABELS)
displayHTML(styled.to_html())  # noqa: F821

# COMMAND ----------

# MAGIC %md ## 9. Export pipeline — write PNG/SVG/PDF + a standalone HTML report to a Volume

# COMMAND ----------

EXPORT_DIR = f"/Volumes/sandbox_marc/givingpulse/viz_export/{YEAR}_gtviz_review/"  # adjust
gtviz.set_options(output_dir=EXPORT_DIR)

fig, ax = gtviz.grouped_dot_plot(df, "age_group", BEHAVIOURS, metric_labels=BEHAVIOUR_LABELS,
                                 title="Generosity behaviours by age group")
paths = gtviz.io.save(fig, "behaviours_by_age", formats=("png", "svg", "pdf"))
print(paths)

report = (gtviz.io.ReportBuilder(title=f"gtviz brand review — {YEAR}")
          .add_heading("Charts render with brand defaults")
          .add_figure(fig, caption="Figure 1. grouped_dot_plot, zero styling kwargs")
          .add_table(table, caption="Table 1. subgroup_summary via HtmlTable"))
html_doc = report.to_html(f"{EXPORT_DIR}/brand_review.html")
report.to_pdf(f"{EXPORT_DIR}/brand_review.pdf")
displayHTML(html_doc)  # noqa: F821

# COMMAND ----------

# MAGIC %md ## 10. Adjusting a default
# MAGIC Edit `src/gtviz/theme.py` (palettes / dpi / profiles) or a function-signature default in the repo,
# MAGIC re-run the `%pip install -e` cell + restart, and re-run this notebook. Once a default is settled,
# MAGIC commit it — CI's visual-regression job flags every chart the change touched, and
# MAGIC `python tools/compare_images.py --update` blesses the new baselines.
# MAGIC
# MAGIC Open decisions live in `docs/guides/design_defaults.md`.
