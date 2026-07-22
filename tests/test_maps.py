import matplotlib.pyplot as plt
from conftest import save_test_image

import gtviz


def test_choropleth_table_absolute(survey):
    tab = gtviz.choropleth_table(survey, "gave_money", region_col="Fips")
    assert set(tab.columns) == {"Fips", "n", "value", "color"}
    # FIPS keep leading zeros
    assert all(len(f) == 5 for f in tab["Fips"])
    assert "01001" in set(tab["Fips"])
    assert tab["color"].str.startswith("#").all()
    assert "scale_min" in tab.attrs and "scale_max" in tab.attrs


def test_choropleth_table_relative(survey):
    tab = gtviz.choropleth_table(survey, "belonging", region_col="Fips", mode="relative")
    assert tab["color"].nunique() <= 4 + 1  # quartile bins (+missing)


def test_scale_bar(survey, output_dir):
    tab = gtviz.choropleth_table(survey, "gave_money", region_col="Fips")
    fig, ax = gtviz.scale_bar(tab.attrs["scale_min"] * 100, tab.attrs["scale_max"] * 100,
                              caption="% gave money, by county")
    save_test_image(fig, output_dir, "scale_bar")
    fig, ax = gtviz.scale_bar(0, 100, caption="Relative bins", cutoffs=[25, 50, 75])
    save_test_image(fig, output_dir, "scale_bar_relative")
    plt.close("all")
