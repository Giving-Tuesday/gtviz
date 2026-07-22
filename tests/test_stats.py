import numpy as np
import pandas as pd

from gtviz import stats


def test_rolling_summary_shapes(survey):
    out = stats.rolling_summary(survey, ["gave_money", "volunteered"])
    assert list(out.columns) == ["gave_money", "volunteered"]
    assert out.index.name == "collection_week"
    assert (out.values <= 100).all() and (out.values >= 0).all()


def test_rolling_summary_filter_and_no_rolling(survey):
    filt = survey["gender"] == "Woman"
    out = stats.rolling_summary(survey, ["gave_money"], filter=filt, rolling=False)
    raw = survey[filt].groupby("collection_week").apply(
        lambda g: np.average(g["gave_money"], weights=g["WEIGHT"]) * 100,
        include_groups=False,
    )
    assert np.allclose(out["gave_money"].values, raw.values)


def test_period_change(survey):
    now = survey[survey["collection_week"] > 13]
    prev = survey[survey["collection_week"] <= 13]
    out = stats.period_change(now, prev, ["gave_money"], labels={"gave_money": "Gave money"})
    assert out.index[0] == "Gave money"
    assert np.isclose(out.loc["Gave money", "change"],
                      out.loc["Gave money", "current"] - out.loc["Gave money", "previous"])


def test_subgroup_summary(survey):
    out = stats.subgroup_summary(survey, "age_group", ["gave_money"])
    assert "Everyone" in out.index
    assert len(out) == 4


def test_build_filter(survey):
    mask = stats.build_filter(survey, {"gender": "Woman", "age_group": ["18-34", "35-54"]})
    sub = survey[mask]
    assert set(sub["gender"]) == {"Woman"}
    assert set(sub["age_group"]) <= {"18-34", "35-54"}


def test_chi_squared_matrix(survey):
    out = stats.chi_squared_matrix(survey, "gave_money", ["gender", "age_group", "region"])
    assert set(out.columns) >= {"chi2", "p", "significant"}
    assert len(out) == 3


def test_normalize_and_decode_likert(survey):
    norm = stats.normalize_likert(survey, ["belonging"])
    assert norm["belonging"].max() == 1.0
    dec = stats.decode_likert(survey, "belonging", labels={i: f"L{i}" for i in range(1, 6)})
    assert dec.index[0] == "L1"
    assert abs(dec["share"].sum() - 100) < 0.5


def test_aggs():
    assert stats.round_mean([1, 2, 3, -1], exclude=-1) == 2
    assert stats.norm_mean([5, 5], scale_max=5) == 100
    assert stats.share_above([1, 2, 3, 4], 2) == 50
    assert stats.binned_mean(pd.Series(["a", "b"]), {"a": 10, "b": 30}) == 20


def test_timeutils(survey):
    out = stats.add_realdate(survey, start_date="2025-01-06")
    assert out["real_date"].min() == pd.Timestamp("2025-01-06")
    dated = out.rename(columns={"real_date": "collection_date"})
    trimmed = stats.trim_rolling_weeks(dated, 2025, date_col="collection_date")
    assert len(trimmed) > 0
