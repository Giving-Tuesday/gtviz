"""Every chart renders and produces a test image (CI artifact)."""

import matplotlib.pyplot as plt
import pytest
from conftest import save_test_image

import gtviz


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


def test_dot_plot(survey, output_dir):
    fig, ax = gtviz.dot_plot(
        [62, 48, 31], ["Gave money", "Volunteered", "Gave items"],
        error=[3, 3, 2], title="Generosity behaviours",
    )
    assert len(ax.lines) >= 1
    save_test_image(fig, output_dir, "dot_plot")


def test_grouped_dot_plot(survey, output_dir):
    fig, ax = gtviz.grouped_dot_plot(
        survey, "age_group", ["gave_money", "volunteered", "gave_items"],
        metric_labels={"gave_money": "Gave money", "volunteered": "Volunteered",
                       "gave_items": "Gave items"},
        error=True, title="Behaviours by age group",
    )
    assert ax.get_legend() is not None
    save_test_image(fig, output_dir, "grouped_dot_plot")


def test_trend_dot_plot(survey, output_dir):
    sub = survey[survey["collection_week"].isin([1, 10, 20])].copy()
    sub["quarter"] = sub["collection_week"].map({1: "Q1", 10: "Q2", 20: "Q3"})
    fig, ax = gtviz.trend_dot_plot(sub, "quarter", ["gave_money", "volunteered"],
                                   title="Trends by quarter", max_percent=80)
    save_test_image(fig, output_dir, "trend_dot_plot")


def test_parallel_bars(survey, output_dir):
    fig, axes = gtviz.parallel_bars(
        survey,
        variables=["gave_money", "volunteered", "gave_items", "solicited"],
        ylabels=["Gave money", "Volunteered", "Gave items", "Solicited"],
        splits=[("gender", "Woman"), ("age_group", "18-34")],
        sub_titles=["Women", "18-34"],
        title="Behaviours by subgroup",
    )
    assert len(axes) == 3
    save_test_image(fig, output_dir, "parallel_bars")


def test_rolling_trend(survey, output_dir):
    fig, ax = gtviz.rolling_trend(
        survey, ["gave_money", "volunteered"],
        labels={"gave_money": "Gave money", "volunteered": "Volunteered"},
        title="Rolling 3-week trends",
    )
    assert hasattr(ax, "_gtviz_data")
    assert not ax._gtviz_data.empty
    save_test_image(fig, output_dir, "rolling_trend")


def test_split_line_plot(survey, output_dir):
    fig, ax = gtviz.split_line_plot(survey, "gave_money", split="age_group",
                                    title="Giving by age over time")
    save_test_image(fig, output_dir, "split_line_plot")


def test_split_line_plot_quartiles(survey, output_dir):
    fig, ax = gtviz.split_line_plot(survey, "belonging", split=None, by_quartile=True,
                                    title="Belonging quartiles over time")
    save_test_image(fig, output_dir, "split_line_quartiles")


def test_annotated_event_plot(survey, output_dir):
    events = {survey["real_date"].quantile(0.3): "Crisis A",
              survey["real_date"].quantile(0.7): "Crisis B"}
    fig, ax = gtviz.annotated_event_plot(survey, "gave_money", events,
                                         title="Giving with crisis events")
    save_test_image(fig, output_dir, "annotated_event_plot")


def test_venn2_and_venn3(survey, output_dir):
    fig, ax = gtviz.venn(survey, ["gave_money", "volunteered"],
                         labels=["Gave money", "Volunteered"], title="2-set overlap")
    save_test_image(fig, output_dir, "venn2")
    fig, ax = gtviz.venn(survey, ["gave_money", "volunteered", "gave_items"],
                         labels=["Money", "Volunteer", "Items"], title="3-set overlap")
    save_test_image(fig, output_dir, "venn3")


def test_venn_from_counts(output_dir):
    counts = {(1, 0, 0): 120, (0, 1, 0): 80, (1, 1, 0): 40,
              (0, 0, 1): 60, (1, 0, 1): 30, (0, 1, 1): 20, (1, 1, 1): 50}
    fig, ax = gtviz.venn_from_counts(counts, ["A", "B", "C"], title="From counts")
    save_test_image(fig, output_dir, "venn_from_counts")


def test_venn_rejects_bad_columns(survey):
    with pytest.raises(ValueError):
        gtviz.venn(survey, ["gave_money"])


def test_weighted_heatmap(survey, output_dir):
    fig, ax = gtviz.weighted_heatmap(
        survey, "region", ["gave_money", "volunteered", "gave_items", "solicited"],
        title="Behaviours by region",
    )
    assert ax._gtviz_data.shape == (4, 4)
    save_test_image(fig, output_dir, "weighted_heatmap")


def test_funnel(survey, output_dir):
    fig, ax = gtviz.funnel([0.45, 0.30, 0.12], ["Solicited", "Responded", "Recurring"],
                           title="Solicitation funnel")
    save_test_image(fig, output_dir, "funnel")


def test_funnel_from_columns(survey, output_dir):
    fig, ax = gtviz.funnel_from_columns(survey, ["solicited", "gave_money"],
                                        labels=["Solicited", "Gave money"],
                                        weights="WEIGHT")
    save_test_image(fig, output_dir, "funnel_from_columns")


def test_donut(output_dir):
    fig, ax = gtviz.donut([40, 30, 20, 10], ["Planners", "Spontaneous", "Mixed", "Non-givers"],
                          title="Giver types")
    save_test_image(fig, output_dir, "donut")


def test_likert_bars(survey, output_dir):
    fig, ax = gtviz.likert_bars(
        survey, ["belonging", "civic_intent", "trust"],
        item_labels={"belonging": "I feel I belong", "civic_intent": "Civic intent",
                     "trust": "Trust in others"},
        answer_labels=["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"],
        title="Attitudes",
    )
    save_test_image(fig, output_dir, "likert_bars")


def test_stacked_bars_and_banded_shares(survey, output_dir):
    survey = survey.copy()
    survey["civic_score"] = survey["civic_intent"] * 20  # 0-100 scale
    tab = gtviz.banded_shares(survey, "region", "civic_score")
    assert tab.shape[1] == 5
    assert abs(tab.sum(axis=1) - 100).max() < 0.5
    fig, ax = gtviz.stacked_bars(tab, title="How Civic Intent varies by region",
                                 n=len(survey))
    from conftest import save_test_image
    save_test_image(fig, output_dir, "stacked_bars")


def test_stacked_bars_labels_and_legend_right(survey, output_dir):
    import pandas as pd
    tab = pd.DataFrame({"Low": [30, 10], "Mid": [40, 50], "High": [30, 40]},
                       index=["Canada", "Kenya"])
    fig, ax = gtviz.stacked_bars(tab, bar_labels=True, legend="right",
                                 title="Three bands")
    assert ax.get_xlim() == (0.0, 100.0)


def test_venn_weighted_default_and_set_percentages(survey, output_dir):
    fig, ax = gtviz.venn(survey, ["gave_money", "volunteered", "gave_items"],
                         labels=["Gave Money", "Volunteered", "Gave Items"],
                         set_percentages=True,
                         title="Giving breakdown by gift type")
    from conftest import save_test_image
    save_test_image(fig, output_dir, "venn_weighted_brand")


def test_contribution_bars_with_benchmarks(output_dir):
    from conftest import save_test_image
    fig, ax = gtviz.contribution_bars(
        [5, 16], ["Aware, inspired somewhat", "Aware, inspired a lot"],
        benchmarks=[68, 79], title="Increase in civic intent")
    save_test_image(fig, output_dir, "contribution_bars")
    fig, ax = gtviz.contribution_bars([27, 10, 22], ["Kindness", "Give more", "Help others"])
    assert len(ax.patches) == 3


def test_range_dot_plot(output_dir):
    import pandas as pd
    from conftest import save_test_image
    df = pd.DataFrame({"low": [60, 54, 48], "high": [84, 74, 73]},
                      index=["Initiated helping", "Local generosity", "Acted generously"])
    fig, ax = gtviz.range_dot_plot(df, "low", "high", benchmark=62,
                                   right_labels=["8%", "40%", "56%"],
                                   title="Components of civil intent")
    save_test_image(fig, output_dir, "range_dot_plot")


def test_arrow_range_plot(output_dir):
    import pandas as pd
    from conftest import save_test_image
    df = pd.DataFrame({"b0": [47, 48, 50], "b1": [52, 60, 46],
                       "c0": [57, 60, 62], "c1": [66, 76, 55]},
                      index=["Aware of disaster", "Responded generously", "Not solicited"])
    fig, ax = gtviz.arrow_range_plot(
        df, {"Belonging": ("b0", "b1", "tab:green"), "Civic": ("c0", "c1", "tab:blue")},
        averages={"Belonging\naverage": (49, "tab:green"), "Civic Intent\naverage": (62, "tab:blue")},
        title="Civic intent vs belonging")
    save_test_image(fig, output_dir, "arrow_range_plot")


def test_nested_bars(output_dir):
    import pandas as pd
    from conftest import save_test_image
    tab = pd.DataFrame({"Aware": [33, 8, 16, 26, 35, 58],
                        "Aware and inspired": [19, 0, 3, 13, 20, 45],
                        "Very inspired": [8, 0, 1, 2, 7, 28]},
                       index=["Everyone", "0-20", "20-40", "40-60", "60-80", "80-100"])
    fig, ax = gtviz.nested_bars(tab, ylabel="Percent aware/inspired", xlabel="Civic Intent",
                                title="GivingTuesday awareness by civic intent")
    assert len(ax.patches) == 18
    save_test_image(fig, output_dir, "nested_bars")


def test_legend_wrap_and_truncate(survey, output_dir):
    long = {"gave_money": "I personally gave money to a nonprofit organization",
            "volunteered": "I volunteered my time for a cause or community group"}
    fig, ax = gtviz.rolling_trend(survey, ["gave_money", "volunteered"], labels=long,
                                  legend_truncate=20)
    texts = [t.get_text() for t in ax.get_legend().get_texts()]
    assert all(len(t) <= 21 for t in texts) and any("\u2026" in t for t in texts)
    fig, ax = gtviz.rolling_trend(survey, ["gave_money", "volunteered"], labels=long,
                                  legend_wrap=15)
    assert any("\n" in t.get_text() for t in ax.get_legend().get_texts())
