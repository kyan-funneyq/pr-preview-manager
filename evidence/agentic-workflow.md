# Agentic workflow

## Tools

- **Claude Code (Opus 5.5)**: the primary coding agent, used for design, planning, implementation and verification.
- **Codex code review**: automatic review of each PR against the rules in `AGENTS.md`.

## How the work was driven: the RPI framework

The work followed a **Research → Plan → Implement (RPI)** workflow, run through Claude Code slash commands. Each stage writes a document that the next stage reads, so the agent works from written, reviewed context instead of re-deriving it each time. A human reviews and approves each document before the next stage starts.

| Stage | Command | Purpose | Used in this project |
|---|---|---|---|
| Research | `/research_codebase` | Investigate existing code and produce a research doc with file:line references | Not needed: the repo started empty, so there was no codebase to research |
| Research (design) | `/create_design` | Turn requirements and research into a high-level design: architecture, flows, decisions, risks | Yes: produced the design doc from the requirements and was revised to match the brief and MVP scope |
| Plan | `/create_plan` | Write a phased plan: exact files, code, and success criteria checkable by running a command | Yes: six phases from local MVP to CI, safe CLI, publish, close path and packaging |
| Implement | `/implement_plan` | Build one phase at a time, run the plan's checks, tick them off, stop for human review | Yes: each phase ends with passing checks, then the human commits and opens a PR |

For later changes to the existing code, the loop starts at `/research_codebase`.

Standing instructions the agent followed throughout:
- `CLAUDE.md`: commands, fixed values, and code and submission rules, each written so it can be checked.
- `AGENTS.md`: review rules that Codex checks on every PR.

The design and plan documents were kept as local working notes. The plan's phases appear in the timeline below.

## Timeline

Timer started **2026-10-26 23:40** (local time).

| Time | Phase | What the agent did | Human steering |
|---|---|---|---|
| Pre-timer | Framing | `/create_design` and `/create_plan`; wrote `CLAUDE.md` and `AGENTS.md` | Cut edge-case handling to keep an MVP scope. Kept the local demo required after re-reading the brief. Moved code into `src/`. Chose one PR per phase so Codex reviews each one. |
| 23:40 | 1 Local MVP | `/implement_plan`, phase 1: `site/`, `src/build_site.py`, `src/previewctl.py prepare`, Makefile, `pyproject.toml`, first tests | Merged as [PR #1](https://github.com/kyan-funneyq/pr-preview-manager/pull/1) |
| 00:37 | 2 CI | `/implement_plan`, phase 2: `.github/workflows/ci.yml` running `make setup verify` on PRs and pushes to `main`, read-only permissions. Ran `make setup verify` in a clean copy of the repo to imitate a CI run | Asked why the actions weren't on their latest versions. The agent had picked them from memory; it then looked up the real latest releases with `gh api`, read the v7 release notes and moved to `checkout@v7` and `setup-python@v7`. Merged as [PR #2](https://github.com/kyan-funneyq/pr-preview-manager/pull/2); CI green on the PR and on `main` |
| 00:45 | 3 Safe CLI | `/implement_plan`, phase 3: symlink and containment checks, stage → swap → restore in `prepare`, `remove`, `status`, and 21 new tests (33 in total). To show the new tests catch the issues Codex reported on PR #1, it ran them against the phase 1 `previewctl.py`; they fail there on source symlinks, symlinked preview folders and the failed swap | |
| 01:24 | 4–5 Publish and close | `/implement_plan`, phases 4 and 5: `.github/workflows/preview.yml` with a `publish` job and a `remove` job. Checked which `checkout@v7` inputs affect PR checkouts. Parsed the YAML and dry-ran both paths against a scratch clone of `gh-pages` | Asked whether the PR's own preview could be cleaned up; the close job was moved into the same PR so it removes its own preview on merge |

## Codex review findings

| PR | Finding (severity) | Response |
|---|---|---|
| #1 | `prepare` follows a symlinked `pr-preview/` and writes outside the preview root (P1) | Known MVP gap; fixed in phase 3 by a containment check |
| #1 | Symlinks in the source are copied into the published site (P1) | Known MVP gap; fixed in phase 3 by rejecting symlinks |
| #1 | The old preview is deleted before the copy, so a failed copy loses it (P1) | Known MVP gap; fixed in phase 3 by staging, swapping and restoring |
| #1 | Invalid-input tests don't compare existing previews before and after (P1) | Known MVP gap; fixed in phase 3 by hashing the existing previews before and after |
| #2 | No findings | – |
| #3 | No result: the review was still showing "Running" when the PR was merged, even after an `@codex review` comment | Merged on green CI and the 33 tests, which include the tests written for the #1 findings |

All four findings matched `AGENTS.md` rules 1–3 and items already planned for phase 3. Phase 1 was kept deliberately simple, and the review confirmed that the review rules catch exactly those gaps.

## How output was reviewed

- `make verify` (ruff + pytest) before every commit.
- Phase 1, after `make demo-build`:
  - each built page contains its own PR number and SHA;
  - the manifest has both entries;
  - both previews and `style.css` are fetched from a local `http.server`;
  - `--pr abc` exits with code 1.
- Ruff caught one line over the length limit on the first run; it was fixed before the phase was finished.
- Phase 4, before the first real run:
  - During `/implement_plan`, the agent added its own pre-run check: parsing `preview.yml` as YAML. It caught two `run:` lines that GitHub would have rejected, because `: ` and ` #` break a plain YAML string. Both were fixed before the workflow ran.
  - This check wasn't part of the workflow yet, so it was added to `CLAUDE.md` as a standing rule: every workflow file must parse, and any `run:` line containing `: ` or ` #` must be a block scalar. Later phases follow it.
  - A dry run against a scratch clone of `gh-pages` confirmed that only `pr-preview/` files change and that the live check finds the full SHA.
  - A close-path dry run with two previews deleted only the closed PR's folder and manifest entry; the other preview stayed. Closing a PR that was never published staged nothing.
