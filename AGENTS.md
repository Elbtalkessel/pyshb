# AGENTS.md

Bootstrap file for coding agents working on **pyshb**.

Project knowledge lives in the Gitea wiki at `gitea.x.home.arpa/python/pyshb/wiki`,
**not** in this repository. Read the relevant pages before planning or writing code.

## Read these first

| Page | Covers |
| --- | --- |
| `Workflow` | The milestone → issue → branch → PR → review → merge loop. **Read this before any task.** |
| `Conventions` | Quality gates, branch/commit naming, Python style rules. |
| `Architecture` | Three-layer design, AST node taxonomy, hard constraints. |
| `Decisions` | Settled decisions — check before proposing an approach. |
| `Tracker` | Current milestone/issue state and what is in flight. |

Fetch one page:

```
gitea_wiki_read(method="get", owner="python", repo="pyshb", pageName="Workflow")
```

Or clone the lot:

```
git clone git@gitea.x.home.arpa:python/pyshb.wiki.git /tmp/pyshb-wiki
```

## Hard rules

1. **Never push to `master`.** Work on `feature/issue-<n>-<slug>`. The one
   exception (the `AGENTS.md` bootstrap) is spent.
2. **Never merge your own PR.** Run the gates, post a review verdict as a PR
   comment, then stop and wait for a human.
3. **Never merge without the issue's acceptance criteria passing.** All three
   gates clean: `uv run pytest`, `uv run ruff check .`, `uv run ty check`.
4. **Never suppress a type error** with `as any` or `# type: ignore`. Fix it.
5. **Never delete a test** to make a gate pass.
6. **Never add `.md` files to this repo** for planning or documentation. Put
   that knowledge in the wiki instead.
7. **Zero runtime dependencies.** Standard library only.

## Environment

- Python `>=3.14`, `uv` for tooling, `devenv` for the dev shell.
- `src/pyshb/base.py` is the legacy pre-AST implementation — still tested and
  still exported, but do not build new features on it.