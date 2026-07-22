# Choropleth maps

gtviz's map tooling is deliberately decoupled from any specific map graphic:
it produces the **color table** (region -> hex) and the **scale-bar
legend**, and you apply the colors to whatever geometry you use — an SVG US
county map, a GeoJSON layer, a BI tool.

## The workflow

```python
# 1. Aggregate + colorize: one row per county
tab = gtviz.choropleth_table(df, "gave_money", region_col="Fips")
tab.head()
#     Fips    n   value    color
#  0  01001  612   0.548  #f7fcb4
#  ...

# 2. Legend matching the same scale
fig, ax = gtviz.scale_bar(tab.attrs["scale_min"] * 100,
                          tab.attrs["scale_max"] * 100,
                          caption="% gave money, by county")

# 3. Apply: e.g. set each SVG path's fill by county id
for _, row in tab.iterrows():
    svg_doc.set_fill(path_id=row["Fips"], color=row["color"])
```

## Absolute vs relative scales

**`mode="absolute"`** (default) maps values linearly between the observed
min and max, extended by `extend_range=0.3` (30%) so the extreme counties
don't sit at the very ends of the colormap — a readability trick carried
over from the original reports.

**`mode="relative"`** bins values by quartile (or your own `cutoffs=`) and
assigns one color per bin — better when the story is "which counties are in
the top/bottom group" rather than exact levels. Pair with
`scale_bar(..., cutoffs=[...])` to draw the binned legend.

## FIPS safety

County FIPS codes start with zeros (`01001` — Autauga County, AL) and are
destroyed by integer casting. `choropleth_table` normalizes the region
column to zero-padded 5-character strings and never round-trips through
int — a bug class the original codebase had to fight repeatedly. Set
`fips=False` if your regions aren't FIPS codes.

## Sparse counties

Survey data rarely covers every county. Regions with fewer than
`min_count` responses get `missing_color` (white by default) rather than a
misleading extreme color from a 3-person sample.
