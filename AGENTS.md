# AGENTS.md

Bootstrap for coding agents working on **pyshb**.

Knowledge is split by scope into two Gitea wikis. The repo carries only
`README.md` (operator-facing) and this file.

- **Instance-wide** — `gitea.x.home.arpa/kb/gitea/wiki`: workflow, review rules,
  commit style, dependencies, environment. True in every repo here.
- **This project** — `gitea.x.home.arpa/python/pyshb/wiki`: this repo's own
  facts and decisions.

Run `gidged identity` before working — it prints the reference clone, worktree
and wiki paths, and your git identity. Dump both wikis with `gidged wiki`; do
all work in a worktree (`gidged worktree <branch>`).

## Read first — project

| Page | Covers |
| --- | --- |
| `Home` | Wiki entrypoint listing every page and when to read it |

## Read first — instance-wide

| Page | Covers |
| --- | --- |
| `Home` | Wiki entrypoint listing every page and when to read it |

Fetch one page:

```
gitea_wiki_read(method="get", owner="python", repo="pyshb", pageName="Home")
gitea_wiki_read(method="get", owner="kb", repo="gitea", pageName="Home")
```
