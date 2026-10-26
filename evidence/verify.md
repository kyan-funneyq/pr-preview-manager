# Verify

## Results

| AC | Check | Result |
|---|---|---|
| AC1 | `make setup verify` | ruff clean, 33 passed; also run in a clean copy with no `.venv` |
| AC2 | `make demo-build`, then fetch both pages from `http.server` | Each page shows its own `#N` and SHA; `style.css` returns 200 |
| AC3 | `test_update_one_leaves_other_identical`, `test_update_replaces_files_and_sha` | pass |
| AC4 | `test_remove_leaves_other`, `test_remove_missing_succeeds` | pass |
| AC5 | `test_invalid_input_changes_nothing` (11 cases) and `test_symlinked_preview_dir_rejected`, each comparing a folder hash before and after | pass |
| AC6 | PR #4 opened → [publish run](https://github.com/kyan-funneyq/pr-preview-manager/actions/runs/40344751456) | Pages deployed `gh-pages` `68260c9`; live check found `bde86af…` after ~50s; link commented on the PR |
| AC7 | Second push to PR #4 → [publish run](https://github.com/kyan-funneyq/pr-preview-manager/actions/runs/40347659727) | Live page and manifest moved to `8aa73c9…`; a second PR comment was posted |
| AC8 | PR #4 merged → [remove run](https://github.com/kyan-funneyq/pr-preview-manager/actions/runs/40348358622) | `pr-4` URL returns 404; manifest `{}` |
| AC8 | PR #5 closed while #6 open → [remove run](https://github.com/kyan-funneyq/pr-preview-manager/actions/runs/40349596092) | `pr-5` returns 404. `pr-6` returns 200 with an identical page hash, and the `gh-pages` commit touched 0 `pr-6` files |
| AC9 | `ci.yml` on PRs and `main` | Green on PR #2 ([run](https://github.com/kyan-funneyq/pr-preview-manager/actions/runs/40332867515)) and on `main` after merges ([latest](https://github.com/kyan-funneyq/pr-preview-manager/actions/runs/40348357809)) |
| AC10 | README and `evidence/` | This pack |
| AC11 | Fresh `git clone` of `main` (`abf857b`), then `make setup verify demo-build` and fetch both pages | 33 passed; both previews `folder=ok`; pages show `#1 a1b2c3d` and `#2 e4f5a6b` |

## Where each check runs

| Check | Local | PR (CI) | Preview workflow |
|---|---|---|---|
| ruff + pytest (`make verify`) | ✓ | ✓ | ✓ before building |
| Workflow YAML parses | ✓ (`ruby -ryaml`, a `CLAUDE.md` rule) | – | GitHub rejects invalid YAML |
| Demo build and serve | ✓ | – | – |
| Live URL shows the SHA | – | – | ✓ fails the run after 5 minutes |
| Codex review against `AGENTS.md` | – | ✓ advisory | – |

## Known gaps

- **Folder and manifest aren't one atomic unit.** If the manifest write fails after a successful swap, `prepare` exits 2 with the new folder in place and the old SHA in the manifest. `remove` has the reverse gap. The git commit protects the published site, because nothing is pushed on a non-zero exit.
- **No test exercises the workflow YAML itself.** The publish and close paths were checked by dry runs against a scratch `gh-pages` clone and then by the real runs above.
- **Python 3.12 is tested only in CI;** locally the checks ran on 3.14.
- **Browser caching.** A removed preview can still show in a browser that opened it in the last 10 minutes, because Pages lets browsers cache it. The server itself returns 404 at once.
- **PR #6 was left open** after the AC8 test so its live preview can be checked.
