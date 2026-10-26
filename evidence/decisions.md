# Decisions

## 1. Python owns files, YAML owns git and GitHub

- **Context:** Many PRs write to one shared `gh-pages` branch, so a bad file operation could damage another PR's preview.
- **Decision:** All validation and file work lives in `previewctl.py`, which never calls git, `gh` or the network. The workflow does checkout, commit, push, polling and comments.
- **Trade-off:** Two places to read. In return, every safety property is tested locally with `tmp_path`, and Python never holds a token.

## 2. Branch-based Pages, not artifact deploys

- **Context:** GitHub Pages serves one site per repository.
- **Decision:** Each preview is a folder on `gh-pages`.
- **Trade-off:** `gh-pages` history grows by one commit per publish or remove. An artifact deploy would replace the whole site on each run, wiping other PRs' previews.

## 3. Validate first, then stage, swap and restore

- **Context:** "A failed command never changes existing previews."
- **Decision:**
  - All checks run before the first write, and a rejection exits 1.
  - `prepare` copies into a staging folder, swaps it into place, and restores the old preview if the swap fails.
  - The manifest is replaced atomically.
- **Not built:** rollback if the manifest write fails *after* a successful swap. The window is tiny, and the git commit protects the published site.

## 4. One concurrency group with `queue: max`

- **Context:** Every run pushes to the same branch.
- **Decision:** All preview runs share the `gh-pages` group, with `cancel-in-progress: false` and `queue: max`.
- **Trade-off:** Runs wait for each other, but pushes never race and up to 100 waiting runs are kept. `queue: max` was added after Codex flagged that the default queue keeps only one waiting run.

## 5. Single publish job for now; split build and publish later

- **Context:** PR code (tests, dependencies, `previewctl.py` from the PR) runs in the job that holds the write token.
- **Decision:** Keep one job, which the requirements scope out of the split, and document the gap. The production design is a read-only build job, plus a publish job that runs trusted `main` code on the built artifact (see `design.md`).
- **Not built:** split jobs, fork support, private previews, automatic stale-preview cleanup.
