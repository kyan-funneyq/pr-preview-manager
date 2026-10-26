# Intent

## Problem

Reviewers of a static site want to click a link and see a pull request's change running, without checking it out. GitHub Pages serves one site per repository, so every PR's preview has to live as a folder inside one shared `gh-pages` branch. The hard part is making sure one PR's run can never break another PR's preview.

## Users

- **PR authors:** get a working preview link on their PR, updated on every push.
- **Reviewers:** open the link and see the exact commit under review (the page shows the PR number and SHA).
- **Maintainers:** previews are removed when PRs close; `status` shows what is published.

## Assumptions

- The site is static and builds with no secrets.
- Only PRs from this repository are trusted; their authors already have push access.
- GitHub Pages is enabled from the `gh-pages` branch root, with `.nojekyll`.

## Constraints

- 3-hour timebox, built mainly with AI coding agents.
- Python standard library only at runtime. Dev tools are pytest and ruff.
- Python does validation and files; workflow YAML does git and GitHub.
- The core path runs locally with no GitHub account or credentials.
- A failed command never changes existing previews.
- No Docker, backend or database; no reuse of `pr-preview-action`.

## Out of scope

- Fork PRs
- Private previews
- Non-static apps
- Custom domains
- Separate build and publish jobs (documented as the production next step)
- Automatic cleanup of stale previews

## Success criteria

| ID | Criterion |
|---|---|
| AC1 | `make verify` passes from a clean checkout with no GitHub access |
| AC2 | `make demo` serves PR 1 and PR 2 previews on `localhost:8000`, each showing its own PR number and SHA |
| AC3 | Updating a preview replaces its content and manifest SHA; the other preview is byte-identical |
| AC4 | Removing a preview deletes only that preview and its manifest entry |
| AC5 | Bad PR number, bad SHA, missing `index.html`, symlinks and paths outside the root are rejected with exit 1, with nothing changed |
| AC6 | Opening a real PR publishes its preview, the workflow confirms the live URL shows the SHA, and the PR gets a comment |
| AC7 | Pushing a new commit updates the live preview to the new SHA |
| AC8 | Closing a PR removes its preview; another open PR's preview still works |
| AC9 | `ci.yml` runs `make verify` on PRs and pushes to `main` |
| AC10 | README and evidence pack exist, with links to the real runs |
| AC11 | Following only the README from a fresh clone, `make verify` and `make demo` work with no credentials |

Results: [`verify.md`](verify.md).
