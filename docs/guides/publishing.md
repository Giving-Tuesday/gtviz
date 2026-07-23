# Publishing: PyPI, Read the Docs, and badges

Everything in the repo is wired; these are the **one-time external setups**
that make the badges live and the release workflow able to publish. Each is
independent — do them in any order.

## 1. PyPI (trusted publishing — no API token)

`release.yml` uses PyPI's OIDC trusted publishing, so there is no token to
store. Register the publisher once:

1. Create the project's publisher at
   <https://pypi.org/manage/account/publishing/> → **Add a pending
   publisher**:
   - PyPI project name: `gtviz`
   - Owner: `Giving-Tuesday`
   - Repository: `gtviz`
   - Workflow name: `release.yml`
   - Environment: `pypi`
2. In GitHub → repo **Settings → Environments → New environment** → name it
   `pypi` (optionally add required reviewers so a release needs approval).
3. Publish by pushing a version tag that matches `pyproject.toml`:
   ```bash
   git tag v0.3.2
   git push --tags
   ```
   The `build` job verifies the tag equals the package version, builds,
   `twine check`s, then the `pypi` job publishes.

### Dry run first (recommended)

Test the whole pipeline against **Test PyPI** without touching real PyPI:

1. Add a matching pending publisher on <https://test.pypi.org> with
   environment `testpypi`, and create a `testpypi` GitHub environment.
2. Actions → **Release** → **Run workflow** → target `testpypi`.
3. Verify: `pip install -i https://test.pypi.org/simple/ gtviz`.

## 2. Read the Docs

1. Sign in at <https://readthedocs.org> with GitHub, **Import a Project**,
   select `Giving-Tuesday/gtviz`. The project slug must be `gtviz` so the
   README badge URL resolves.
2. `.readthedocs.yaml` is already present — RTD installs the package with
   the `docs` extra, regenerates the gallery in `pre_build`, and builds
   `docs/conf.py`. First build kicks off on import; subsequent builds run on
   every push to `main`.
3. The badge (`readthedocs.org/projects/gtviz/badge`) goes green after the
   first successful build.

## 3. Codecov (coverage badge)

1. Sign in at <https://codecov.io> with GitHub, enable `Giving-Tuesday/gtviz`.
2. For a **public** repo, uploads work with no token. For a **private**
   repo, copy the repo upload token and add it as a GitHub Actions secret
   named `CODECOV_TOKEN` (Settings → Secrets and variables → Actions).
3. CI already uploads `coverage-3.12.xml` from the `test` job; the badge
   populates after the next CI run on `main`.

## 4. Badges

The README header renders: PyPI version, supported Python versions, CI
status, Read the Docs, Codecov coverage, Ruff, and license. They resolve
automatically once the services above are connected — no manual URLs to
maintain. If you rename the repo or PyPI project, update the owner/repo
slugs in the badge URLs at the top of `README.md`.

## Release checklist

1. Bump `version` in `pyproject.toml` **and** `src/gtviz/__init__.py`
   (they must match; CI's `build` job enforces the tag matches too).
2. Add a `CHANGELOG.md` entry.
3. `git commit`, ensure CI is green.
4. `git tag vX.Y.Z && git push --tags`.
5. Watch Actions → **Release**; approve the `pypi` environment if you set
   required reviewers.
