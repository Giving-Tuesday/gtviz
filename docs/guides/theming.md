# Theming

## Profiles

gtviz ships two rcParams profiles, ported from the production report code:

```python
gtviz.theme.use("report")        # quarterly-report defaults
gtviz.theme.use("publication")   # spineless, tick-less, bold-titled
```

**`report`** sets 300-dpi savefig output, 14 pt base fonts, and 16 pt titles —
tuned for figures dropped into an A4/letter report at half-page width.

**`publication`** removes all spines and tick marks, pads labels, and bolds
titles — the cleaner look used for externally published figures.

Profiles are plain `matplotlib.rcParams` updates, so anything you set after
calling `use()` wins, and you can mix with your own style sheets.

## Palette tokens

`gtviz.theme.palette` centralizes the colors used across charts and tables:

| token | default | used by |
|---|---|---|
| `accent` | `#4e79a7` | dot plots, funnels, table bar fills |
| `high` / `low` | `#dcfcd9` / `#fae8eb` | table + comparison shading |
| `zebra` | `#f5f5f5` | table row striping |
| `series` | 10-color categorical list | any multi-series chart |

Change them globally:

```python
gtviz.theme.palette["accent"] = "#2f6bb0"
gtviz.theme.palette["series"] = my_brand_colors
```

Every chart also accepts explicit `color=`/`colors=` per call when a one-off
override is cleaner than a global change.

## Map colors

Choropleths default to a discretized 25-step Spectral colormap
(`gtviz.theme.spectral_cmap(25)`) — enough steps to look continuous while
keeping the scale-bar labels legible. Pass any matplotlib colormap via
`cmap=` to `choropleth_table` and `scale_bar`; just pass the *same* one to
both so the legend matches the map.
