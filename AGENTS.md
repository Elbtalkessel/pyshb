# AGENTS.md

Bootstrap file for coding agents working on **pyshb**.

Knowledge is split by scope into two Gitea wikis. Read the relevant pages before
planning or writing code; the repository carries only `README.md`
(operator-facing) and this file.

- **Instance-wide** — `gitea.x.home.arpa/kb/gitea/wiki`: who you act as on Gitea,
  the task lifecycle and review rules, dependencies. True in every repo here.
- **This project** — `gitea.x.home.arpa/python/pyshb/wiki`: architecture, gates,
  Python conventions, this repo's own decisions and tracker.

## Read these first — project

| Page | Covers |
| --- | --- |
| `Workflow` | The milestone → issue → branch → PR → review → merge loop. **Read this before any task.** |
| `Conventions` | Quality gates, branch/commit naming, Python style rules. |
| `Architecture` | Three-layer design, AST node taxonomy, hard constraints. |
| `Decisions` | Settled decisions — check before proposing an approach. |
| `Tracker` | Current milestone/issue state and what is in flight. |

## Read these first — instance-wide

| Page | Covers |
| --- | --- |
| `AgentIdentity` | Which account, key and token you push as, and how to prove it. **Read before your first push.** |
| `Workflow` | The lifecycle, and the review/merge rules in detail. |
| `Dependencies` | Recording blocked-by relations on issues and PRs. |
| `Decisions` | Settled instance-wide rules (G-rules). |

Fetch one page:

```
gitea_wiki_read(method="get", owner="python", repo="pyshb", pageName="Workflow")
gitea_wiki_read(method="get", owner="kb", repo="gitea", pageName="AgentIdentity")
```

Or clone the lots:

```
git clone git@gitea.x.home.arpa:python/pyshb.wiki.git /tmp/pyshb-wiki
git clone git@gitea.x.home.arpa:kb/gitea.wiki.git /tmp/gitea-wiki
```

## Hard rules

1. **Never push to `master`.** Work on `feature/issue-<n>-<slug>`. The one
   exception (the `AGENTS.md` bootstrap) is spent.
2. **Never merge without an approving human review.** Run the gates, post a
   review verdict as a `COMMENT`, request `@risus`, then stop. Never post
   `APPROVED` on your own work. Once the approval lands on the current head,
   merge it yourself: squash, keep the branch, close the issue, tick the
   milestone checkbox.
3. **Never merge without the issue's acceptance criteria passing.** All three
   gates clean: `uv run pytest`, `uv run ruff check .`, `uv run ty check`.
4. **Never suppress a type error** with `as any` or `# type: ignore`. Fix it.
5. **Never delete a test** to make a gate pass.
6. **Never add `.md` files to this repo** for planning or documentation. Put that
   knowledge in the wikis (`kb/gitea` `Decisions` G003).
7. **Zero runtime dependencies.** Standard library only.
8. **If an issue or PR has a dependency, record it as a Gitea dependency** —
   `blocked_by` / `blocking` on the issue itself, not in prose. Same-repo only;
   cross-repo dependencies go in the body with a link. Details: `kb/gitea`
   `Dependencies`.
9. **Commit as `nastya <pieceof@duck.com>`.** The VM default identity is not on
   that account, so pass it explicitly and check
   `git log -1 --format='%an <%ae>'`. Details: `kb/gitea` `AgentIdentity`.

## Environment

- Python `>=3.14`, `uv` for tooling, `devenv` for the dev shell.
- `src/pyshb/base.py` is the legacy pre-AST implementation — still tested, but
  module-tier only. It is never re-exported from the package root, and you must
  not build new features on it.
