import pandas as pd

import gtviz


def test_html_table_basic(output_dir):
    df = pd.DataFrame({"Q1": [50, 40, 12], "Q2": [55, 38, 14]},
                      index=["Gave money", "Volunteered", "Gave items"])
    t = gtviz.HtmlTable(df, title="Generosity by quarter", subtitle="Weighted %",
                        sample_sizes=[1200, 1180])
    html = t.to_html()
    assert "pub-table" in html and "Generosity by quarter" in html
    assert "Sample size:" in html
    assert t._repr_html_() == html  # fixed return_code bug: real string return
    path = t.save(output_dir / "html_table.html")
    assert path.exists()


def test_html_table_multiindex():
    idx = pd.MultiIndex.from_tuples(
        [("Giving", "Money"), ("Giving", "Items"), ("Time", "Volunteering")],
        names=["category", "mode"],
    )
    df = pd.DataFrame({"share": [55, 40, 30]}, index=idx)
    html = gtviz.HtmlTable(df).to_html()
    # level-0 rollup: 'Giving' appears once as a data cell, blank on repeat
    assert html.count(">Giving<") == 1


def test_html_table_high_low_shading():
    df = pd.DataFrame({"a": [10, 50], "b": [30, 50], "c": [50, 50]}, index=["r1", "r2"])
    html = gtviz.HtmlTable(df, high_low_threshold=5).to_html()
    assert "#dcfcd9" in html and "#fae8eb" in html  # r1 has high & low cells
    html2 = gtviz.HtmlTable(df, high_low_shading=False).to_html()
    assert "#dcfcd9" not in html2


def test_compare_periods(survey):
    now = survey[survey["collection_week"] > 13]
    prev = survey[survey["collection_week"] <= 13]
    out = gtviz.compare_periods(now, prev, ["gave_money", "volunteered"], style=False)
    assert list(out.columns) == ["Current", "vs Last quarter"]
    styled = gtviz.compare_periods(now, prev, ["gave_money", "volunteered"])
    assert hasattr(styled, "to_html")


def test_compare_periods_absolute_yoy(survey):
    now = survey[survey["collection_week"] > 20]
    prev = survey[survey["collection_week"].between(10, 20)]
    yoy = survey[survey["collection_week"] < 10]
    out = gtviz.compare_periods(now, prev, ["gave_money"], df_yoy=yoy, absolute=True, style=False)
    assert out.shape == (1, 3)


def test_pivot_change_table(survey):
    now = survey[survey["collection_week"] > 13]
    prev = survey[survey["collection_week"] <= 13]
    out = gtviz.pivot_change_table(now, prev, index="age_group", values="gave_money")
    assert set(out.columns) == {"current", "previous", "change"}
    assert len(out) == 3
