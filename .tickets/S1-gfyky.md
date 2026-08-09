---
id: S1-gfyky
status: open
deps: [S1-cnpew]
links: []
created: 2026-08-09T17:56:28Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Upgrade Django 2.0 to 2.2 LTS

Objective: first rung of the LTS ladder.

Bump Django to the latest 2.2.x. Bump third-party Django packages only as far as 2.2 needs; leave the rest alone.

Run makemigrations --check and commit anything Django generates.

In your summary, list every deprecation warning the test run emits, because 3.2 is the next stop and those warnings are the preview of it.

Non-goals: no code cleanup beyond what 2.2 requires. No new features.

Caveat: use Poetry 1.4.0 for lock operations. Must stay deployable to Dokku.

## Acceptance Criteria

Suite green on PostgreSQL 18. collectstatic works. makemigrations --check is clean.


## Notes

**2026-08-09T18:40:51Z**

Ordering change: uv replaces Poetry before this ticket runs. Ignore the 'use Poetry 1.4.0' caveat in the description; there is no poetry.lock by then. Use uv for all lock operations.
