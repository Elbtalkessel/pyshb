# AGENTS.md

Bootstrap file for coding agents working on **pyshb**.

Knowledge is split by scope into two Gitea wikis. Read the relevant pages before
planning or writing code; the repository carries only `README.md`
(operator-facing) and this file.

- **Instance-wide** — `gitea.x.home.arpa/kb/gitea/wiki`: who you act as on Gitea,
  the task lifecycle and review rules, dependencies. True in every repo here.
- **This project** — `gitea.x.home.arpa/python/pyshb/wiki`: architecture, gates,
  Python conventions, this repo's own decisions.

## Quick reference

The wikis are authoritative; this block restates the invariants so routine work
does not re-read them. If it disagrees with a wiki, the wiki wins.

- **Fetch first, work from a fresh worktree.** `git fetch origin`, then create the
  worktree from `origin/master` — never read or edit the reference clone's
  checkout, it goes stale:
  ```
  git -C ~/Projects/pyshb worktree add ~/Projects/worktrees/pyshb/issue-<n>-<slug> \
      -b feature/issue-<n>-<slug> origin/master
  ```
- **Branch**: `feature/issue-<n>-<slug>`. Never commit to `master` (protected).
  Squash merge.
- **Commit**: terse imperative single line. Commit as the host git identity —
  never override `user.name` / `user.email`. Run `git commit` inside `devenv
  shell` (`devenv shell git commit -m ...`): the pre-commit `ty` hook needs
  `VIRTUAL_ENV`. Do not pipe `git commit` through `tail` — it masks the exit code
  and lets `&& git push` run on a failed commit.
- **Gates** — run all three in one devenv bootstrap:
  ```
  devenv shell bash -c "uv run pytest -q && ruff check . && ty check"
  ```
- **Review**: post a `COMMENT`-state review verdict, then request `@risus` as a
  reviewer. The reviewer approves and merges; the agent never merges.
- **PR body**: what changed + a **Verification** section with exact command
  output + a `Closes #<n>` trailer.
- **Tools**: `uv`, `ruff`, `ty` exist only inside `devenv shell`.

## Read these first — project

| Page  | Covers                                                       |
| ----- | ------------------------------------------------------------ |
| `Home` | Wiki entrypoint containing list of pages and when to read them |

## Read these first — instance-wide

| Page  | Covers                                                       |
| ----- | ------------------------------------------------------------ |
| `Home` | Wiki entrypoint containing list of pages and when to read them |

Fetch one page:

```
gitea_wiki_read(method="get", owner="python", repo="pyshb", pageName="Home")
gitea_wiki_read(method="get", owner="kb", repo="gitea", pageName="Home")
```

Or clone the lot:

```
git clone git@gitea.x.home.arpa:python/pyshb.wiki.git /tmp/pyshb-wiki
git clone git@gitea.x.home.arpa:kb/gitea.wiki.git /tmp/gitea-wiki
```
