# PR Preview Manager

Each same-repo PR gets a static-site preview at `https://<owner>.github.io/<repo>/pr-preview/pr-<N>/`, updated on every push and removed on close. The same tools run locally with no GitHub account, which is the path assessors run. This repo is a submission for a 3-hour AI-engineering exercise. Scope: meet AC1–AC11, nothing more. Review rules: `AGENTS.md`.

Local working notes (git-ignored, not in the repo): requirements and ACs in `thoughts/shared/requirements/2026-10-26-pr-preview-manager-requirements.md`; design in `thoughts/shared/designs/2026-10-26-pr-preview-manager.md`. The committed versions are `evidence/intent.md` and `evidence/design.md`.

## Layout

```
src/build_site.py     render site/ with PR + SHA
src/previewctl.py     prepare / remove / status
tests/                pytest; pyproject.toml sets pythonpath = ["src"]
site/                 sample input: index.html, style.css
.github/workflows/    ci.yml, preview.yml
evidence/             submission evidence pack
```

## Commands

```bash
make setup                              # one-time: creates .venv with ruff + pytest
make verify                             # ruff check . && pytest -q  (run before every commit; CI runs the same)
.venv/bin/ruff check . --fix            # autofix lint
.venv/bin/pytest -q tests/test_previewctl.py -k remove   # run one test
make demo                               # previews for PR 1 + 2 in .preview-root/, served on localhost:8000
make demo-build                         # same, without starting the server (for checks)
make clean                              # delete dist/ and .preview-root/

python3 src/build_site.py --pr 42 --sha abc1234 --out dist/
python3 src/previewctl.py prepare --pr 42 --sha abc1234 --source dist/ --target .preview-root
python3 src/previewctl.py remove  --pr 42 --target .preview-root
python3 src/previewctl.py status  --target .preview-root

ruby -ryaml -e 'ARGV.each { |f| YAML.load_file(f); puts "#{f}: ok" }' .github/workflows/*.yml   # check workflow YAML parses

gh run list --workflow preview.yml -L 5  # recent preview runs
gh run view <run-id> --log-failed        # why a run failed
gh pr view <N> --comments                # preview link comment
```

## Fixed values

- Pages source: `gh-pages` branch, root, contains `.nojekyll`.
- Preview folder: `pr-preview/pr-<N>/`. Manifest: `pr-preview/previews.json` = `{"<N>": {"sha": "...", "updated_at": "..."}}`.
- `previewctl.py` exit codes: `0` success, `1` validation rejected, `2` unexpected error.
- Workflow: concurrency group `gh-pages`, `cancel-in-progress: false`; permissions `contents: write`, `pull-requests: write`.
- Live check: poll every 10s, for at most 5 min, until the page contains the SHA.

## Code rules

- Python code is exactly two files, `src/build_site.py` and `src/previewctl.py`, which import only the standard library.
- Python never runs `git` or `gh` and never calls the GitHub API; those belong in workflow YAML.
- `previewctl.py` runs every validation check before its first write.
- Each `previewctl.py` command prints one line to stdout (command, PR, SHA, result). Rejections and errors print the reason to stderr.
- Each invalid-input test asserts exit code `1` and an unchanged folder hash, checked before and after the command.
- Tests use `tmp_path` and need no network.
- Links in `site/` are relative: no `href` or `src` starts with `/` or `http`.
- The workflow uses `github.event.pull_request.head.sha` for the build, the live check and the PR comment.
- The workflow writes the preview URL to `$GITHUB_STEP_SUMMARY`.
- Before a workflow change is committed, every file in `.github/workflows/` parses as YAML (see the `ruby -ryaml` command above), and every `run:` line containing `: ` or ` #` is a block scalar (`run: |`).

## Submission rules

- The human makes every commit, push, PR and merge. The agent never runs `git commit`, `git push`, `git reset`, `gh pr create` or `gh pr merge`. Read-only commands such as `git status`, `git diff`, `git log`, `gh run list` and `gh pr view` are fine.
- When a phase's changes are ready, the agent stops and lists the files and suggested commit messages for the human to commit.
- Each phase gets its own branch (for example `feat/safe-cli`) with several small commits, then one PR. Nothing is committed directly to `main`.
- Commits happen only when `make verify` passes. A PR is merged only when CI is green, using `gh pr merge --merge`. No squashing, rebasing, amending pushed commits or force-pushing.
- After a Codex review lands, record it in `evidence/agentic-workflow.md`. Fix any real finding in the next PR.
- Never fake results. An AC counts as met only when it links to a real PR or workflow run, or quotes real command output. Report failures and skipped steps as they are.
- Never commit `thoughts/`, the exercise brief, secrets, tokens or personal data. Use sample data only.
- `README.md` covers: what it does, prerequisites, setup, `make demo`, `make verify`, one example including a rejection with exit `1`, known limitations, and a link to `evidence/`.
- `evidence/` contains exactly `intent.md`, `design.md`, `agentic-workflow.md`, `verify.md`, `operate.md` and `decisions.md` (3–5 decisions), each kept short. Base `design.md` on the design doc above.
- At the end of each milestone, add to `evidence/agentic-workflow.md`: the time, what the agent did, one representative prompt, and any human intervention or correction.
- Do not add anything on the out-of-scope list: forks, private previews, Docker, custom domains, split jobs, stale-preview cleanup. Describe them in `evidence/` as next steps instead.

## Milestones

1. Before the timer: public repo, orphan `gh-pages` branch with `.nojekyll`, Pages enabled, Codex review enabled. Record the start time.
2. `CLAUDE.md`, `AGENTS.md`, `site/`, `build_site.py`.
3. `Makefile`, `ci.yml` running tests.
4. `previewctl.py` and tests (AC1–AC5), `make demo` (AC2).
5. `preview.yml` open and update path, tested with a real PR (AC6, AC7).
6. Close path (AC8).
7. README, `evidence/`, fresh-clone run of `make verify` + `make demo` (AC9–AC11). Record the end time.

If behind at 2:00, drop the PR comment and keep the URL in the job summary.
