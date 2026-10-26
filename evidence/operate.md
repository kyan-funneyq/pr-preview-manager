# Operate

## Run

| Where | How |
|---|---|
| Local | `make setup`, then `make verify` and `make demo` (see README) |
| GitHub | Automatic on PR open, push, reopen and close; nothing to run by hand |

## Logs and status

Each `previewctl` command prints one line to stdout. Rejections and errors go to stderr.

```
prepare pr=6 sha=ae3570c… path=gh-pages/pr-preview/pr-6 result=ok
remove pr=5 result=removed            # or result=absent if there was nothing to remove
rejected: source contains symlinks: dist/leak
```

`status` lists every preview and flags drift between the folders and the manifest:

```
pr=6 sha=ae3570c… updated_at=2026-10-26T15:26:25+00:00 folder=ok
pr-9 folder=untracked                  # folder with no manifest entry
status previews=1 result=ok
```

To check the live state on GitHub:

```bash
git fetch origin gh-pages && git show origin/gh-pages:pr-preview/previews.json
gh run list --workflow preview.yml -L 5
gh run view <id> --log-failed
```

Each workflow run writes the preview URL to its job summary.

## Config and secrets

- **No configuration files.** Fixed values (paths, manifest name, concurrency group) live in the code and the workflow.
- **No secrets locally.**
- **In CI, only the built-in `GITHUB_TOKEN`,** scoped to `contents: write` and `pull-requests: write`, and never rendered into the site.

## Failure modes

| Symptom | Cause | Action |
|---|---|---|
| `rejected: …`, exit 1 | Bad input | Fix the input; nothing was changed |
| `error: …`, exit 2 | Unexpected failure (disk, permissions, bad manifest) | Read the message; previews are unchanged unless the manifest write itself failed (see Known gaps in `verify.md`) |
| "Preview not live after 5 minutes" | Pages slow or not deployed | Check the `pages-build-deployment` run, then re-run the job; re-running is safe |
| Removed preview still shows in a browser | Browser cache (up to 10 minutes) | Hard-refresh, or check with `curl -I <url>`, which shows the real 404 |
| `folder=untracked` / `folder=missing` | A run failed between the folder and manifest steps | `previewctl remove --pr N`, or re-run the PR's workflow |
| Stale preview after a close | Close run failed, or was cancelled by hand | Re-run the failed `remove` job, or run `previewctl remove` on a `gh-pages` checkout, then commit and push |

## Rollback and degrade

- **A bad preview:** push a fix to the PR, or revert the `gh-pages` commit for it (one commit per publish or remove).
- **If Pages is down,** the publish job fails at the live check, and the PR shows it. Other previews are unaffected.
- **Locally,** `make clean` resets everything.

## Local to cloud

- **The local and CI paths run the same code.** Only the target folder and the publish step (web server or git push) differ.
- **Next steps for a cloud enterprise setup** (detail in `design.md`):
  - separate build and publish jobs, using trusted publisher code;
  - private object storage behind a CDN with SSO;
  - OIDC credentials instead of long-lived secrets;
  - scheduled cleanup of stale previews;
  - staged promotion with an approval gate.
