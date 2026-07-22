"""Tests for gtviz.pipeline — dataset-specific scoring steps.

Uses a synthetic frame with the real question codes so the steps run
end-to-end without any production data or reference files (references are
passed as in-memory DataFrames).
"""

import numpy as np
import pandas as pd
import pytest

from gtviz import pipeline as pl


@pytest.fixture(scope="module")
def gp_frame() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    n = 500
    df = pd.DataFrame(index=range(n))
    # belonging items: text answers
    answers = ["Strongly Agree", "Somewhat Agree", "Somewhat Disagree", "Strongly Disagree"]
    for q in ["Q31_r6_scale", "Q31_r7_scale", "Q31_r8_scale", "Q31_r9_scale"]:
        df[q] = rng.choice(answers, n)
    # civic intent ingredients (numeric scales)
    for q in ["Q30_r7_scale", "Q31_r5_scale", "Q31_r1_scale", "Q31_r2_scale",
              "Q31_r3_scale", "Q31_r4_scale", "Q30_r2_scale", "Q29_scale", "Q51_scale"]:
        df[q] = rng.integers(0, 5, n)
    for i in list(range(1, 13)) + [14]:
        df[f"Q11_r{i}_binary"] = rng.binomial(1, 0.25, n)
    df["giving_flag"] = rng.binomial(1, 0.6, n)
    df["Q19_YES__I_was_an_initiator"] = rng.binomial(1, 0.2, n)
    for c in ["Q21Oct_Gave_items", "Q21Oct_Donated_money",
              "Q21Oct_Volunteered_regularly", "Q21Oct_Advocated_regularly"]:
        df[c] = rng.binomial(1, 0.4, n)
    for c in ["Q20iOct_scale", "Q20iiOct_scale", "Q20iiiOct_scale", "Q20ivOct_scale"]:
        df[c] = rng.integers(1, 5, n)
    # pew battery (2026 coding: 1 agree / 2 not sure / 3 disagree)
    for i in range(1, 9):
        df[f"Q63Oct_r{i}_scale"] = rng.integers(1, 4, n)
    # activism battery: mixed strings/numbers like the raw export
    for i in [1, 2, 3, 4, 5, 6, 7, 9, 10, 11]:
        df[f"Q21B_{i}_binary"] = rng.choice(["0.0", 1, 0, 1], n)
    # geography
    df["state"] = rng.choice(["Colorado", "Texas"], n)
    df["county"] = rng.choice(["Larimer", "Harris"], n)
    return df


@pytest.fixture(scope="module")
def typology_ref() -> pd.DataFrame:
    return pd.DataFrame({
        "County name": ["Larimer County, Colorado", "Harris County, Texas"],
        "2023 Typology": ["College Town", "Big Metro"],
        "Fips": ["08069", "48201"],
    })


@pytest.fixture(scope="module")
def pew_ref() -> pd.DataFrame:
    rng = np.random.default_rng(3)
    types = pl.AssignPew.ORDERED_TYPES
    # percent-agree by question (columns) per type (index), like the real CSV
    return pd.DataFrame(rng.uniform(0, 100, (len(types), 8)),
                        index=types, columns=[f"Q63Oct_r{i}" for i in range(1, 9)])


def test_score_belonging(gp_frame):
    out = pl.ScoreBelonging().transform(gp_frame)
    assert out["belonging"].between(0, 1).all()
    assert set(out["belonging_group"]) <= {"low", "mid", "high"}
    assert "belonging_sum" in out
    # reverse-coded: all-"Strongly Agree" on mixed valence -> mid sum (6/12)
    row = gp_frame.iloc[[0]].copy()
    for q in ["Q31_r6_scale", "Q31_r7_scale", "Q31_r8_scale", "Q31_r9_scale"]:
        row[q] = "Strongly Agree"
    both = pd.concat([row, row]).reset_index(drop=True)
    scored = pl.ScoreBelonging().transform(both)
    assert (scored["belonging_sum"] == 6).all()
    # input not mutated
    assert "belonging" not in gp_frame.columns


def test_score_belonging_no_flags(gp_frame):
    out = pl.ScoreBelonging(add_flags=False).transform(gp_frame)
    assert "belonging" in out and "belonging_group" not in out


def test_score_civic_intent(gp_frame):
    out = pl.ScoreCivicIntent().transform(gp_frame)
    assert out["civic_intent"].between(0, 1).all()
    assert out["civic_intent"].min() == 0 and out["civic_intent"].max() == 1
    for c in ["giving_recency_money", "giving_recency_items",
              "giving_recency_vol", "giving_recency_advo"]:
        assert set(out[c].dropna().unique()) <= {0.0, 0.33, 0.67, 1.0}


def test_civic_intent_custom_recency(gp_frame):
    custom = {1: 1.0, 2: 0.5, 3: 0.25, 4: 0.0}
    out = pl.ScoreCivicIntent(recency_map=custom).transform(gp_frame)
    assert set(out["giving_recency_money"].dropna().unique()) <= set(custom.values())


def test_assign_county_types(gp_frame, typology_ref):
    out = pl.AssignCountyTypes(typology_ref).transform(gp_frame)
    assert set(out["county_type"].dropna()) == {"College Town", "Big Metro"}
    # idempotent
    again = pl.AssignCountyTypes(typology_ref).transform(out)
    assert list(again.columns).count("county_type") == 1


def test_assign_county_types_state_prefix(typology_ref):
    df = pd.DataFrame({"state": ["CO-Colorado", "TX-Texas", "NM-New Mexico", "WY-Wyoming"],
                       "county": ["Larimer", "Harris", "Bernalillo", "Teton"]})
    out = pl.AssignCountyTypes(typology_ref).transform(df)
    assert out.loc[0, "county_type"] == "College Town"


def test_assign_pew(gp_frame, pew_ref):
    out = pl.AssignPew(pew_ref).transform(gp_frame)
    assert out["best_pew"].notna().all()
    assert out["best_pew"].cat.ordered
    dist_cols = [c for c in out.columns if c.endswith("_dist")]
    assert len(dist_cols) == 9
    assert any(c.startswith("best_pew_") for c in out.columns)  # one-hot


def test_assign_pew_matches_notebook_metric(pew_ref):
    """Vectorized distances equal the notebook's per-row formula."""
    rng = np.random.default_rng(0)
    df = pd.DataFrame({f"Q63Oct_r{i}_scale": rng.integers(1, 4, 20) for i in range(1, 9)})
    out = pl.AssignPew(pew_ref).transform(df)
    ref = (pew_ref / 100)
    center = {1: 1.0, 2: 0.5, 3: 0.0}
    for i in range(5):  # spot check rows
        resp = np.array([center[df.loc[i, f"Q63Oct_r{j}_scale"]] for j in range(1, 9)])
        for t in ref.index:
            manual = float((((resp - ref.loc[t].values) ** 2 - 1) ** 2).sum() / 8)
            assert np.isclose(out.loc[i, f"{t}_dist"], manual)


def test_assign_activism(gp_frame):
    out = pl.AssignActivism().transform(gp_frame)
    flags = [c for c in out.columns if c.startswith("activism_")]
    assert set(flags) == {"activism_none", "activism_min", "activism_boycott",
                          "activism_inperson", "activism_lead", "activism_any",
                          "activism_moderate"}
    # 'any' must be a superset of 'boycott'
    assert (out["activism_any"] | ~out["activism_boycott"]).all()


def test_civic_quartile():
    df = pd.DataFrame({"civic_intent": [0.1, 0.3, 0.6, 0.9]})
    out = pl.CivicQuartile().transform(df)
    assert list(out["civic_quartile"]) == ["Very low (0-25)", "Low (25-50)",
                                           "Medium (50-75)", "High (75-100)"]


def test_pipeline_batch_and_params(gp_frame, typology_ref, pew_ref):
    pipe = pl.default_pipeline(typology=typology_ref, pew_decoder=pew_ref)
    assert [n for n, _ in pipe.steps] == ["activism", "county_types", "belonging",
                                          "civic_intent", "pew", "civic_quartile"]
    out = pipe.transform(gp_frame)
    for col in ["activism_any", "county_type", "belonging", "civic_intent",
                "best_pew", "civic_quartile"]:
        assert col in out.columns

    # sklearn-style param addressing
    pipe.set_params(civic_intent__recency_map={1: 1.0, 2: 0.5, 3: 0.25, 4: 0.0})
    assert pipe.named_steps["civic_intent"].recency_map[2] == 0.5
    params = pipe.get_params()
    assert "belonging__out_col" in params


def test_process_convenience(gp_frame, typology_ref, pew_ref):
    out = pl.process(gp_frame, typology=typology_ref, pew_decoder=pew_ref)
    assert "civic_quartile" in out.columns
    # subset run without reference files
    out2 = pl.process(gp_frame)
    assert "belonging" in out2 and "county_type" not in out2


def test_step_repr_and_get_params():
    step = pl.ScoreBelonging(add_flags=False)
    assert "add_flags=False" in repr(step)
    assert step.get_params()["out_col"] == "belonging"
    with pytest.raises(ValueError):
        step.set_params(nope=1)


def test_sklearn_compatibility(gp_frame):
    """Steps satisfy the sklearn transformer contract."""
    pytest.importorskip("sklearn")
    from sklearn.pipeline import Pipeline as SkPipeline

    pipe = SkPipeline([("belonging", pl.ScoreBelonging()),
                       ("quartile", pl.CivicQuartile(source_col="belonging",
                                                     out_col="belonging_quartile"))])
    out = pipe.fit_transform(gp_frame)
    assert "belonging_quartile" in out.columns
