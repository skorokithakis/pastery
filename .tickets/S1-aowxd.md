---
id: S1-aowxd
status: closed
deps: [S1-nzsrw]
links: []
created: 2026-08-09T18:21:12Z
type: chore
priority: 2
assignee: Stavros Korokithakis
external-ref: STA-108
---
# Fail CI when migrations are missing

Objective: catch missing migrations automatically, so this cannot silently drift again.

Add './manage.py makemigrations --check --dry-run' to the tests job in .github/workflows/ci.yml. Put it before the existing test step. It needs no database and no collected static files.

Scope: .github/workflows/ci.yml only.

Non-goals: do not add it to pre-commit, do not change the Python version, do not touch the deploy job.

Caveat: this check is only meaningful after the raw_language choices fix. Before that, it would pass or fail depending on whether dev dependencies were installed.

Leave the work uncommitted.


## Notes

**2026-08-09T18:21:14Z**

ready for implementation
