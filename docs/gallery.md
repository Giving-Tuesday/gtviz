# Gallery

Every chart type, rendered from synthetic survey data by
`examples/generate_gallery.py`.

## `dot_plot`

Basic dot plot with 95% error bars

![dot_plot](_static/gallery/dot_plot.png)

## `grouped_dot_plot`

Groups compared across metrics

![grouped_dot_plot](_static/gallery/grouped_dot_plot.png)

## `trend_dot_plot`

Metric movement across periods

![trend_dot_plot](_static/gallery/trend_dot_plot.png)

## `parallel_bars`

Baseline vs subgroups with point-difference labels

![parallel_bars](_static/gallery/parallel_bars.png)

## `rolling_trend`

Thick tableau-palette lines, no markers/grid, bold left title with gray subtitle

![rolling_trend](_static/gallery/rolling_trend.png)

## `split_line_plot`

One trend line per group level

![split_line_plot](_static/gallery/split_line_plot.png)

## `annotated_event_plot`

Trend with labeled event markers

![annotated_event_plot](_static/gallery/annotated_event_plot.png)

## `venn`

Area-proportional 3-set overlap, brand set colors, n-subtitle (percent of sample per region)

![venn](_static/gallery/venn.png)

## `venn_set_percentages`

Per-set totals under each label

![venn_set_percentages](_static/gallery/venn_set_percentages.png)

## `weighted_heatmap`

Weighted means: groups x metrics

![weighted_heatmap](_static/gallery/weighted_heatmap.png)

## `funnel`

Stage-share funnel

![funnel](_static/gallery/funnel.png)

## `donut`

Ring chart

![donut](_static/gallery/donut.png)

## `likert_bars`

100% stacked Likert distributions

![likert_bars](_static/gallery/likert_bars.png)

## `stacked_bars`

100% stacked band bars: red-to-blue 5-band scale, horizontal legend on top

![stacked_bars](_static/gallery/stacked_bars.png)

## `waffle`

Aid-flows waffle: tab10 sequence, right legend with values

![waffle](_static/gallery/waffle.png)

## `contribution_bars`

Signed white labels in-bar; gray benchmark bubbles

![contribution_bars](_static/gallery/contribution_bars.png)

## `range_dot_plot`

Dumbbell ranges: red/green endpoint scores in gray bubbles, gap labeled, dotted benchmark

![range_dot_plot](_static/gallery/range_dot_plot.png)

## `arrow_range_plot`

Directional arrows; decreases turn red

![arrow_range_plot](_static/gallery/arrow_range_plot.png)

## `nested_bars`

Layered subset bars: gray total, cyan subset, blue core

![nested_bars](_static/gallery/nested_bars.png)

## `scale_bar`

Choropleth scale-bar legend

![scale_bar](_static/gallery/scale_bar.png)

## Export pipeline

The same run also produces a standalone [HTML report](_static/gallery/sample_report.html) with figures inlined as SVG, and a print-ready [PDF](_static/gallery/sample_report.pdf).
