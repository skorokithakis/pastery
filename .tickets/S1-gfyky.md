---
id: S1-gfyky
status: closed
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

**2026-08-09T18:47:12Z**

ready for implementation

**2026-08-12T16:59:28Z**

Two mechanical points for the implementer.

Deprecation warnings are not visible by default. Python hides DeprecationWarning outside __main__, and Django's test runner does not unhide RemovedInDjangoXXWarning for a project suite. Run the suite once with PYTHONWARNINGS=always::DeprecationWarning (or -Wa) before you report the list, or you will report an empty list that is not true.

Report every version that moves in uv.lock, not only Django. Most Django-adjacent pins here (django-bootstrap3 12.1.0, django-redis 4.11.0, whitenoise 5.0, djangoql 0.14.0, pytz 2020.1) sit where they do because uv backtracked to satisfy django<2.1. Raising the Django floor will let some of them jump on their own. Silent movement is the risk, not the movement itself.

Do not chase the coverage percentage; coverage 4.4.2 misreports this codebase. See gnosis reanmn.

Leave the untracked ARCHITECTURE.md out of your commit.

**2026-08-12T17:15:42Z**

Done. Django 2.0.13 -> 2.2.28 (specifier >=2.2,<2.3; 2.2.28 is the last 2.2 release). uv.lock moved django plus its new dependency sqlparse 0.5.5 and nothing else. Zero source changes, zero migrations generated. 92 tests green, collectstatic clean, makemigrations --check clean, pre-commit clean. No RemovedInDjango* warnings at all, which is what the S1-cnpew forward-compatibility work bought us; the only warnings left are Django 2.2's own distutils use and a pre-existing naive-datetime RuntimeWarning from webauthin's AuthData model.

PG 18 was exercised against a real PostgreSQL 18.4, but not through docker compose, because no Docker daemon was reachable in the sandbox. CI is the confirmation on a real runner.

Finding worth carrying forward, recorded as gnosis gtxgkc: plain 'uv lock' is preference-preserving, so the stale adjacent pins did not move and will not move on any rung unless a floor is raised or 'uv lock --upgrade' is run deliberately.
