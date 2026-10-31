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
