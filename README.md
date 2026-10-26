# PR Preview Manager

Every same-repo pull request gets its own live preview of a static site on GitHub Pages, at `https://<owner>.github.io/<repo>/pr-preview/pr-<N>/`. The preview updates on every push and is removed when the PR closes. Other PRs' previews are never touched.

A small standard-library Python CLI (`src/previewctl.py`) does all the file work behind strict validation. GitHub Actions does the git and GitHub work. The same tools run locally with no GitHub account.

## Prerequisites

- Python 3.12+ (`python3`)
- GNU Make
- A web browser

No GitHub account or token is needed. Only `make setup` needs network access, once, to install the two pinned dev tools from PyPI.

## Setup

```bash
make setup      # creates .venv with pinned ruff + pytest
```

## Run

```bash
make demo
```

This builds previews for two example PRs into `.preview-root/` and serves them at:

- http://localhost:8000/pr-preview/pr-1/ (PR #1, SHA `a1b2c3d`)
- http://localhost:8000/pr-preview/pr-2/ (PR #2, SHA `e4f5a6b`)

Press Ctrl+C to stop. Use `make demo-build` to build without serving, and `make clean` to delete the output.

## Verify

```bash
make verify     # ruff + 33 pytest tests; CI runs the same command
```

## Example

```console
$ make clean
$ python3 src/build_site.py --pr 42 --sha abc1234 --out dist/pr-42
build pr=42 sha=abc1234 out=dist/pr-42 result=ok

$ python3 src/previewctl.py prepare --pr 42 --sha abc1234 --source dist/pr-42 --target .preview-root
prepare pr=42 sha=abc1234 path=.preview-root/pr-preview/pr-42 result=ok

$ python3 src/previewctl.py status --target .preview-root
pr=42 sha=abc1234 updated_at=2026-10-26T15:30:00+00:00 folder=ok
status previews=1 result=ok

$ python3 src/previewctl.py prepare --pr 42 --sha xyz --source dist/pr-42 --target .preview-root
rejected: SHA must be 7-40 hex characters, got 'xyz'
$ echo $?
1

$ python3 src/previewctl.py remove --pr 42 --target .preview-root
remove pr=42 result=removed
```

Exit codes: `0` success, `1` rejected by validation (nothing written), `2` unexpected error.

## How it works on GitHub

`.github/workflows/preview.yml` runs on same-repo pull requests:

- **Opened or updated:**
  1. Run `make verify`.
  2. Build the site with the PR number and head SHA.
  3. Run `previewctl prepare` into a `gh-pages` checkout, then commit and push.
  4. Poll the live URL until it shows the SHA.
  5. Comment the link on the PR.
- **Closed:** run `previewctl remove` and push.

All runs share one concurrency group, so pushes to `gh-pages` never race.

Real runs:

| What | PR | Workflow runs |
|---|---|---|
| Opening a PR publishes its preview | [#4](https://github.com/kyan-funneyq/pr-preview-manager/pull/4) | [publish](https://github.com/kyan-funneyq/pr-preview-manager/actions/runs/40344751456) |
| A new push updates the preview | [#4](https://github.com/kyan-funneyq/pr-preview-manager/pull/4) | [publish](https://github.com/kyan-funneyq/pr-preview-manager/actions/runs/40347659727) |
| Merging removes the preview | [#4](https://github.com/kyan-funneyq/pr-preview-manager/pull/4) | [remove](https://github.com/kyan-funneyq/pr-preview-manager/actions/runs/40348358622) |
| Closing one PR leaves the other's preview alone | [#5](https://github.com/kyan-funneyq/pr-preview-manager/pull/5), [#6](https://github.com/kyan-funneyq/pr-preview-manager/pull/6) | [remove #5](https://github.com/kyan-funneyq/pr-preview-manager/actions/runs/40349596092) |

`.github/workflows/ci.yml` runs `make setup verify` on every PR and on every push to `main`.

## Repo layout

```
src/build_site.py     render site/ with PR + SHA
src/previewctl.py     prepare / remove / status
tests/                pytest (tmp_path only, no network)
site/                 sample input: index.html, style.css
.github/workflows/    ci.yml, preview.yml
evidence/             evidence pack
```

## Known limitations

- **Same-repo PRs only.** Fork PRs are skipped.
- **Previews are public** (GitHub Pages). Browsers may cache a page for up to 10 minutes, so a removed preview can still appear in a browser that opened it recently.
- **No retry if a close run fails.** Previews are removed automatically when a PR closes. If that run fails, though, nothing sweeps the leftover preview later. `status` lists it and `previewctl remove` deletes it.
- **PR code runs in a job that holds a write token.** The production fix is separate build and publish jobs; see `evidence/design.md`.
- **The preview folder and the manifest are not updated as one atomic unit.** A failure between the two steps can leave them out of sync locally. The git commit is the atomic step for the published site.

## Evidence pack

See [`evidence/`](evidence/):
- [intent](evidence/intent.md)
- [design](evidence/design.md)
- [agentic workflow](evidence/agentic-workflow.md)
- [verify](evidence/verify.md)
- [operate](evidence/operate.md)
- [decisions](evidence/decisions.md)
