# CI/CD and image testing

Charts are code whose *output is pixels*, so gtviz's CI tests both the code
and the pictures. Two complementary review modes run on every push:

## Human mode: rendered images as artifacts

The `test` job runs the full pytest suite, and every chart test saves its
figure (PNG + SVG) to `tests/output/`. That directory is uploaded as a
**`test-images` artifact** on each CI run. Reviewing a PR that touches chart
code? Download the artifact and *look at the charts* — the diff that matters
is visual.

The `gallery` job goes further: it runs `examples/generate_gallery.py`,
producing every chart type plus a complete sample HTML report and PDF, and
uploads the lot as the **`gallery` artifact**. This is the "what does the
library actually produce right now" snapshot.

## Headless mode: baseline comparison

The `visual-regression` job re-renders all test images and compares them
pixel-wise against committed baselines in `tests/baseline/`:

```bash
python tools/compare_images.py --threshold 1.0
```

- Each image's **mean pixel difference** must stay within the threshold
  (percent of full scale). Small antialiasing noise passes; layout changes,
  color changes, and missing elements fail.
- On failure, a `*_diff.png` heat image is written per failing chart and
  uploaded as the **`image-diffs` artifact**, so you can see exactly which
  pixels moved.

### Accepting intentional changes

Changed a chart on purpose? Re-bless the baselines locally and commit them:

```bash
pytest                                  # regenerate tests/output/
python tools/compare_images.py --update # copy into tests/baseline/
git add tests/baseline && git commit -m "Update chart baselines: <why>"
```

The baseline images in the repo double as a reviewable visual history of
every chart — `git log -- tests/baseline` shows when each chart last
changed appearance.

### Determinism notes

Pixel comparison only works if rendering is deterministic. The suite pins
the `Agg` backend, uses a seeded synthetic dataset, and renders at a fixed
DPI. Font availability differs across OSes, which is why the headless job
runs on a single pinned platform (ubuntu, Python 3.12) while the functional
matrix (3.10–3.13) checks code behavior everywhere.

## Pipeline summary

| job | what it checks | output for review |
|---|---|---|
| `lint` | ruff | — |
| `test` (matrix 3.10–3.13) | all unit tests + coverage | `test-images` artifact (human) |
| `visual-regression` | pixel diffs vs baselines | `image-diffs` artifact on failure (headless) |
| `gallery` | full gallery + HTML/PDF report build | `gallery` artifact (human) |
| `docs` | Sphinx build, warnings-as-errors | `docs-html` artifact |
| `release` (on `v*` tags) | build + publish to PyPI (trusted publishing) | — |

Read the Docs builds and hosts the published documentation on every push to
`main`, regenerating the gallery images in its `pre_build` step so the docs
always show current output.
