# PR Preview Manager

The `preview.yml` workflow publishes a static-site preview of each same-repo PR to `gh-pages` under `pr-preview/pr-<N>/`. `previewctl.py` handles the files and the workflow YAML handles git and GitHub. Commands and project conventions: `CLAUDE.md`. Verify with `make verify`.

## Code Review Rules

Flag a PR if any of these is broken:

1. **Writes stay in the preview root.** `previewctl.py` creates, renames or deletes paths only under `<target>/pr-preview/`. `remove` touches only `pr-preview/pr-<N>/` and key `"<N>"` in `previews.json`.
2. **Validation before writes.** Every check (PR is a positive integer, SHA is 7–40 hex characters, `index.html` exists, no symlinks, path stays inside `pr-preview/`) runs before the first filesystem write, and a failed check exits with code `1`.
3. **Failures leave previews unchanged.** Writes go to a temp path, then `os.rename`/`os.replace` into place. A failed swap restores the old folder. Each invalid-input test checks that the folder hash is identical before and after.
4. **Minimal permissions.** The workflow `permissions:` block lists exactly `contents: write` and `pull-requests: write`. No other permission and no `pull_request_target` trigger.
5. **Forks excluded.** Every job in the preview workflow has `if: github.event.pull_request.head.repo.full_name == github.repository`.
6. **No secrets in published output.** Nothing under `site/` or `dist/` reads `secrets.*`, environment variables or tokens, and `build_site.py` substitutes only `{{PR}}` and `{{SHA}}`.
7. **No git or GitHub calls from Python.** No `subprocess` running `git`/`gh`, and no HTTP calls in `.py` files.
8. **Standard library only.** `.py` files import nothing outside the standard library, except `pytest` in tests.
9. **Sample data only.** No real personal data, credentials or confidential documents anywhere in the diff.