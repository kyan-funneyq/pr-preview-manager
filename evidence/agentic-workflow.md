# Agentic workflow

## Tools

- **Claude Code (Opus 5.5)**: the primary coding agent, used for design, planning, implementation and verification.
- **Codex code review**: automatic review of each PR against the rules in `AGENTS.md`.

## How the work was driven

Claude Code ran three slash commands in sequence. Each one produced a document that the next one built on:

| Step | Command | What it produced |
|---|---|---|
| 1. Design | `/create_design` | An engineering design doc built from the requirements: architecture, flows, key decisions, risks. Revised several times to match the brief and MVP scope. |
| 2. Plan | `/create_plan` | A phased implementation plan. For each phase: exact files, code, and success criteria that can be checked by running a command. Phases go from local MVP to CI, safe CLI, publish, close path and packaging. |
| 3. Build | `/implement_plan` | Implementation one phase at a time, running every automated check in the plan and ticking it off. The agent stops after each phase for human review and commit. |

Standing instructions the agent followed throughout:
- `CLAUDE.md`: commands, fixed values, and code and submission rules, each written so it can be checked.
- `AGENTS.md`: review rules that Codex checks on every PR.

The design and plan documents were kept as local working notes. Their content is summarised in `evidence/design.md`.

## Timeline

Timer started **2026-10-26 23:40** (local time).

| Time | Phase | What the agent did | Human steering |
|---|---|---|---|
| Pre-timer | Framing | `/create_design` and `/create_plan`; wrote `CLAUDE.md` and `AGENTS.md` | Cut edge-case handling to keep an MVP scope. Kept the local demo required after re-reading the brief. Moved code into `src/`. Chose one PR per phase so Codex reviews each one. |
| 23:40 | 1 Local MVP | `/implement_plan`, phase 1: `site/`, `src/build_site.py`, `src/previewctl.py prepare`, Makefile, `pyproject.toml`, first tests | Merged as [PR #1](https://github.com/kyan-funneyq/pr-preview-manager/pull/1) |
| 00:37 | 2 CI | `/implement_plan`, phase 2: `.github/workflows/ci.yml` running `make setup verify` on PRs and pushes to `main`, read-only permissions. Ran `make setup verify` in a clean copy of the repo to imitate a CI run | Asked why the actions weren't on their latest versions. The agent had picked them from memory; it then looked up the real latest releases with `gh api`, read the v7 release notes and moved to `checkout@v7` and `setup-python@v7`. Merged as [PR #2](https://github.com/kyan-funneyq/pr-preview-manager/pull/2); CI green on the PR and on `main` |
| 00:45 | 3 Safe CLI | `/implement_plan`, phase 3: symlink and containment checks, stage → swap → restore in `prepare`, `remove`, `status`, and 21 new tests (33 in total). To show the new tests catch the issues Codex reported on PR #1, it ran them against the phase 1 `previewctl.py`; they fail there on source symlinks, symlinked preview folders and the failed swap | |

## Codex review findings

| PR | Finding (severity) | Response |
|---|---|---|
| #1 | `prepare` follows a symlinked `pr-preview/` and writes outside the preview root (P1) | Known MVP gap; fixed in phase 3 by a containment check |
| #1 | Symlinks in the source are copied into the published site (P1) | Known MVP gap; fixed in phase 3 by rejecting symlinks |
| #1 | The old preview is deleted before the copy, so a failed copy loses it (P1) | Known MVP gap; fixed in phase 3 by staging, swapping and restoring |
| #1 | Invalid-input tests don't compare existing previews before and after (P1) | Known MVP gap; fixed in phase 3 by hashing the existing previews before and after |
| #2 | No findings | – |

All four findings matched `AGENTS.md` rules 1–3 and items already planned for phase 3. Phase 1 was kept deliberately simple, and the review confirmed that the review rules catch exactly those gaps.

## How output was reviewed

- `make verify` (ruff + pytest) before every commit.
- Phase 1, after `make demo-build`:
  - each built page contains its own PR number and SHA;
  - the manifest has both entries;
  - both previews and `style.css` are fetched from a local `http.server`;
  - `--pr abc` exits with code 1.
- Ruff caught one line over the length limit on the first run; it was fixed before the phase was finished.
