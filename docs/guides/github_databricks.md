# Publishing to GitHub and pulling into Databricks

## 1. Create the GitHub repo

```bash
cd gtviz
git init -b main
git add .
git commit -m "gtviz 0.3.0: brand-default survey visualization library"

# with GitHub CLI:
gh repo create Giving-Tuesday/gtviz --private --source . --push
# or manually: create an empty repo at github.com/new, then
git remote add origin git@github.com:Giving-Tuesday/gtviz.git
git push -u origin main
```

CI runs on the first push (lint, test matrix + image artifacts,
visual-regression, gallery, docs, pipeline). Baselines in `tests/baseline/`
are committed, so the visual-regression job is green from commit one.

## 2. Optional one-time setup

- **Read the Docs**: import the repo at readthedocs.org — `.readthedocs.yaml`
  is already in place; docs publish on every push to `main`.
- **PyPI trusted publishing** (for `release.yml`): PyPI → project →
  Publishing → add GitHub `Giving-Tuesday/gtviz`, workflow `release.yml`,
  environment `pypi`. Then `git tag v0.3.0 && git push --tags` publishes.
- **Branch protection** on `main` requiring the `test` and
  `visual-regression` checks keeps unreviewed chart changes out.

## 3. Pull into Databricks

1. Databricks → **Repos** → **Add Repo** → paste the GitHub URL
   (set up a GitHub PAT under User Settings → Linked accounts if prompted).
2. Open `notebooks/brand_defaults_review_V1` inside the repo and attach a
   cluster — the first cell `%pip install -e` installs the package from the
   repo's own `src/`, so **edits to library code in the repo are live after
   re-running that cell + restart**.
3. Iterate on defaults: edit `src/gtviz/theme.py` or a function default in
   the Databricks editor, re-run the notebook, judge, repeat.
4. When a default is settled: commit + push from the Repos UI (or locally),
   run `pytest && python tools/compare_images.py --update` to bless the new
   baselines, and commit those too — CI shows the visual diff history.

For cluster-wide (non-editable) installs instead, add
`git+https://github.com/Giving-Tuesday/gtviz.git@main` as a cluster library, or
`%pip install git+https://...` in any notebook.
