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
| Pre-timer | Framing | `/create_design`, `/create_plan`, `CLAUDE.md`, `AGENTS.md` | Cut to MVP scope; kept local demo required per the brief |
| 23:40 | 1 Local MVP | Site, build script, `prepare`, Makefile, first tests | Merged [#1](https://github.com/kyan-funneyq/pr-preview-manager/pull/1) |
| 00:37 | 2 CI | `ci.yml` running `make setup verify` | Asked for latest action versions → bumped to v7; merged [#2](https://github.com/kyan-funneyq/pr-preview-manager/pull/2) |
| 00:45 | 3 Safe CLI | Symlink/path checks, swap and restore, `remove`, `status`, 33 tests | Merged [#3](https://github.com/kyan-funneyq/pr-preview-manager/pull/3) |
| 01:24 | 4–5 Publish and close | `preview.yml` publish and remove jobs; YAML check and dry runs | Moved close job into same PR; merged [#4](https://github.com/kyan-funneyq/pr-preview-manager/pull/4); AC8 via [#5](https://github.com/kyan-funneyq/pr-preview-manager/pull/5)/[#6](https://github.com/kyan-funneyq/pr-preview-manager/pull/6) |
| 02:28 | 6 Package | README, evidence pack, fresh-clone check | Spotted a cached removed preview → confirmed 404, documented |

Timer ended **02:40** (local time), when this final PR was merged. Total: **3h 00m**.

## Codex review

Every finding was checked before acting on it:

- **PR #1, four P1 findings:** symlinks, writing outside the preview root, no restore on a failed copy, and tests not checking existing previews. All were known MVP gaps already planned for phase 3, and phase 3 fixed them.
- **PR #4, valid finding:** the concurrency group kept only one waiting run. Fixed with `queue: max`, after checking GitHub's current docs.
- **PR #4, rejected finding:** "`GITHUB_TOKEN` pushes don't trigger a Pages build". Not reproduced: the same commit's run had already triggered a Pages deployment and passed the live check.

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
