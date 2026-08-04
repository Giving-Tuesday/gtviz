"""Tests for the consolidated ``rolling_summary`` options and ``sparkline_bar_plot``.

Covers: default path is unchanged (pinned to the documented algorithm), the new
``group_col`` panel equals a per-group loop of the default, ``pooled`` matches a
hand-computed rolling ratio and collapses to the default under equal weights,
arbitrary window widths, empty-categorical safety, and that the new chart
returns ``(fig, ax)``.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.axes
import matplotlib.figure
import numpy as np
import pandas as pd
import pytest

import gtviz
from gtviz.stats import rolling_summary, subgroup_summary
from gtviz.stats.summaries import _resolve_weights


def _reference_default(df, columns, time_col="collection_week", window=3, weights="auto",
                       filter=None, normalize=False, rolling=True, as_percent=True):
    """The documented default algorithm, inlined, to pin backward compatibility."""
    data = df if filter is None else df.loc[filter]
    w = _resolve_weights(data, weights)
    if normalize:
        data = data.copy()
        for c in columns:
            m = data[c].max()
            if m:
                data[c] = data[c] / m

    def wmean(group):
        gw = w.loc[group.index]
        return pd.Series({c: np.average(group[c].fillna(0), weights=gw) for c in columns})

    out = data.groupby(time_col)[columns].apply(wmean)
    if rolling:
        out = out.rolling(window=window, min_periods=1).mean()
    return out * 100 if as_percent else out


@pytest.fixture
def df():
    rng = np.random.default_rng(0)
    rows = []
    for wk in range(1, 40):
        for _ in range(int(rng.integers(30, 80))):
            g = rng.choice(["A", "B", "C"])
            rows.append((wk, g, int(rng.random() < 0.5), int(rng.random() < 0.3),
                         float(rng.uniform(0.5, 1.5))))
    out = pd.DataFrame(rows, columns=["collection_week", "grp", "money", "vol", "WEIGHT"])
    gtviz.set_options(weight_col="WEIGHT")
    return out


@pytest.mark.parametrize("window", [1, 3, 8])
@pytest.mark.parametrize("rolling", [True, False])
@pytest.mark.parametrize("as_percent", [True, False])
def test_default_path_unchanged(df, window, rolling, as_percent):
    got = rolling_summary(df, ["money", "vol"], window=window, rolling=rolling, as_percent=as_percent)
    exp = _reference_default(df, ["money", "vol"], window=window, rolling=rolling, as_percent=as_percent)
    pd.testing.assert_frame_equal(got, exp)


def test_group_col_matches_per_group_loop(df):
    got = rolling_summary(df, ["money"], window=4, group_col="grp").reindex(columns=["A", "B", "C"])
    exp = pd.DataFrame(
        {g: rolling_summary(df[df.grp == g], ["money"], window=4)["money"] for g in ["A", "B", "C"]}
    )
    exp.columns.name = "grp"
    pd.testing.assert_frame_equal(got, exp)


def test_group_col_multi_metric_is_multiindex(df):
    out = rolling_summary(df, ["money", "vol"], window=4, group_col="grp")
    assert isinstance(out.columns, pd.MultiIndex)
    assert out.columns.names[0] == "grp"
    assert ("A", "money") in out.columns


def test_pooled_matches_manual_ratio(df):
    got = rolling_summary(df, ["money"], window=4, pooled=True)["money"]
    num = (df["money"] * df["WEIGHT"]).groupby(df["collection_week"]).sum().rolling(4, min_periods=1).sum()
    den = df["WEIGHT"].groupby(df["collection_week"]).sum().rolling(4, min_periods=1).sum()
    pd.testing.assert_series_equal(got, (100 * num / den), check_names=False)


def test_pooled_equals_default_under_equal_weights():
    rows = [(wk, "X", int((wk + i) % 2), 1.0) for wk in range(1, 20) for i in range(40)]
    d = pd.DataFrame(rows, columns=["collection_week", "grp", "money", "WEIGHT"])
    gtviz.set_options(weight_col="WEIGHT")
    a = rolling_summary(d, ["money"], window=3, pooled=True)
    b = rolling_summary(d, ["money"], window=3, pooled=False)
    pd.testing.assert_frame_equal(a, b)


def test_arbitrary_window(df):
    out = rolling_summary(df, ["money"], window=8, group_col="grp")
    assert out.shape[1] == 3


def test_empty_categorical_level_is_skipped(df):
    df = df.copy()
    df["grp"] = pd.Categorical(df["grp"], categories=["A", "B", "C", "D"])  # D unused
    out = rolling_summary(df, ["money"], window=4, group_col="grp")
    assert list(out.columns) == ["A", "B", "C"]  # no ZeroDivisionError from empty 'D'


def test_sparkline_bar_plot_returns_fig_ax(df):
    tbl = rolling_summary(df, ["money"], window=4, group_col="grp")
    ov = subgroup_summary(df, "grp", ["money"], weights="auto", include_all=False, as_percent=True)["money"]
    fig, ax = gtviz.sparkline_bar_plot(tbl, values=ov, title="Money by group")
    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(ax, matplotlib.axes.Axes)


def test_grouped_dot_plot_default_markersize_is_15(df):
    import inspect
    # signature default
    assert inspect.signature(gtviz.grouped_dot_plot).parameters["markersize"].default == 15
    # and it actually reaches the drawn markers
    fig, ax = gtviz.grouped_dot_plot(df, "grp", ["money", "vol"])
    sizes = {ln.get_markersize() for ln in ax.get_lines() if ln.get_marker() not in ("", "None", None)}
    assert sizes == {15}, sizes


def test_other_dot_plots_markersize_unchanged():
    import inspect
    assert inspect.signature(gtviz.dot_plot).parameters["markersize"].default == 10
    assert inspect.signature(gtviz.trend_dot_plot).parameters["markersize"].default == 8


def _legend_ncols(leg):
    return getattr(leg, "_ncols", getattr(leg, "_ncol", None))


def test_stacked_bars_legend_ncol():
    import pandas as pd
    bands = [f"b{i}" for i in range(9)]
    t = pd.DataFrame([[100 / 9] * 9, [100 / 9] * 9], index=["X", "Y"], columns=bands)
    # default: min(len(bands), 5) == 5
    _, ax = gtviz.stacked_bars(t, legend="top")
    assert _legend_ncols(ax.get_legend()) == 5
    # explicit override
    _, ax = gtviz.stacked_bars(t, legend="top", legend_ncol=3)
    assert _legend_ncols(ax.get_legend()) == 3
