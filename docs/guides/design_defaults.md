# Design defaults & override policy

gtviz's purpose is to make the **brand defaults win** over matplotlib's:
call a chart function with data only, and you get the report look. Every
styling decision is also a kwarg, so one-off overrides never require
touching library code.

## Source of truth

Defaults were audited line-by-line from the production `gp_reports` code
(`report_params.py`, `visualization_functions.py`, `report_functions.py`).
Where the original had a single consistent value, that value is the
default, verbatim.

| element | brand default | override |
|---|---|---|
| export DPI | 300 | `io.save(..., dpi=)` / `set_options(dpi=)` |
| inline figure DPI | 300 (original) | `theme` profile / rcParams |
| base / legend / title font | 14 / 14 / 16 pt | rcParams after `theme.use()` |
| publication style | spineless, tickless, bold titles, pads 10/15 | `theme.use("publication")` |
| brand font | Neutraface Text (must be installed) | `theme.use(profile, font=...)` |
| dot marker | `"."`, size 10, edge width 0 | `marker=`, `markersize=` |
| dot error style | same-color hlines, no caps | draw your own on the returned `ax` |
| dot value labels | **off** | `datalabels=True` |
| dot grid / ticks | dotted `0.8` y-grid; y-ticks both sides | — |
| grouped-dot series | `tab:grey` (Everyone) → blue, olive, orange, green, red, purple | `colors=` / `theme.palette["series"]` |
| grouped-dot layout | figsize (9,4), no box, legend frameless @ (1, 0.85), xlim (−1,101), "Percent" labelpad 10, n= in legend, 25-char label wrap | `figsize=`, `box=True`, `legend_anchor=`, `xrange=`, `xlabel=`, `show_n=False`, `wrap=` |
| parallel bars | width 0.75, alpha 0.5, panel titles 12pt pad 1, suptitle 18 bold | kwargs |
| rolling trend | figsize (10,6), plain lines (mpl cycle, no markers), legend @ (1,1), no grid | `colors=`, `marker=`, `legend_anchor=`, `grid=True`, `shade=` |
| split lines | figsize (8,6), `#E5E5E5`-first series, o-markers, frameless legend | `colors=` / `theme.palette["split_series"]` |
| Likert bars | 4-pt `tab:red→orange→olive→green`, figsize (12, 0.8+n), white int labels (zero-width suppressed), legend outside upper-right | `colors=` / `palette["likert4"]`, `min_label_width=`, `legend_anchor=` |
| venn | 7×7, equal circles, % of sample labels, title 20pt pad 30, layout pad 5 | `weighted=True`, `as_percent=False` |
| funnel | half-width 11, bands 2.8 gap 0.2, white 10pt labels, title 12pt | kwargs |
| donut | wedge width 0.5, start 90° clockwise, no % labels | `autopct="%1.0f%%"` |
| scale bar | figsize (8, 0.4), 0.2 lw black edges, 5pt labels, Spectral-25 | kwargs |
| HTML table | `#4e79a7` accent, `#dcfcd9`/`#fae8eb` shading @ ±5, `#f5f5f5` zebra | constructor args / `theme.palette` |
| choropleth | Spectral-25, absolute scale extended 30% | `cmap=`, `mode=`, `extend_range=` |

## Open decisions

Where the originals **contradicted each other** or a faithful default has a
known cost, the current default is marked; flip by decision:

1. **Inline `figure.dpi` 300** (original) makes notebook figures very large.
   Alternative: 110 for display with 300 kept for `savefig`/export.
   *Current default: 300 (faithful).*
2. **Legend fontsize**: rcParams say 14; the pew/stress stacked bars and a
   few others locally used 12. *Current default: inherit 14; pass
   `plt.legend(fontsize=12)`-style overrides per chart.*
3. **Heatmap colormap**: the originals used the seaborn default (dark
   "rocket"), which does not ship with matplotlib. *Current default:
   `YlGnBu`; closest built-in to the original is `magma` — one-line change.*
4. **Series palette scope**: dot plots used the tab-color list; split-line
   charts used a different light-gray-first list. Both ship
   (`palette["series"]`, `palette["split_series"]`); consolidating to one
   list is a decision, not a default.

When one of these is decided, change it in `theme.py` (palettes/profiles)
or the function signature default — CI's visual-regression job will show
exactly which charts changed, and `compare_images.py --update` blesses the
new baselines.
