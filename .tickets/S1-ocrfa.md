---
id: S1-ocrfa
status: open
deps: [S1-gfyky, rep-mcpwp]
links: []
created: 2026-08-09T17:56:35Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Upgrade Django 2.2 to 3.2 LTS

Objective: second rung of the LTS ladder.

Bump Django to the latest 3.2.x, and bump third-party packages as far as that requires. The likely ones are django-bootstrap3, djangoql, django-redis, django-ipware, django-tokenauth, django-webauthin and django-annoying.

Set DEFAULT_AUTO_FIELD to django.db.models.AutoField. Use AutoField, not BigAutoField: BigAutoField would generate AlterField migrations that rewrite the primary key column of every table on a live PostgreSQL database, for no benefit here.

Report the output of Django's system checks before and after, in particular the W042 auto-field warning.

Note that django-ipware moves several major versions here or at the next rung. The client-IP test from the safety-net ticket is the guard; if it fails, the rate limiter and the spam blocker are both keying on Cloudflare's address rather than the visitor's.

Non-goals: no code cleanup beyond what 3.2 requires.

Caveat: use Poetry 1.4.0 for lock operations. Must stay deployable to Dokku.

## Acceptance Criteria

Suite green on PostgreSQL 18. collectstatic works. makemigrations --check is clean. System checks report no W042.


## Notes

**2026-08-09T18:40:51Z**

Ordering change: uv replaces Poetry before this ticket runs. Ignore the 'use Poetry 1.4.0' caveat in the description; there is no poetry.lock by then. Use uv for all lock operations.

**2026-08-09T18:47:12Z**

ready for implementation

**2026-08-12T17:42:21Z**

Before you bump third-party packages here, read gnosis gtxgkc. The stale adjacent pins (django-bootstrap3 12.1.0, django-redis 4.11.0, whitenoise 5.0, djangoql 0.14.0, pytz 2020.1) do not move on their own, because plain 'uv lock' is preference-preserving. They move only if you raise their floor or run 'uv lock --upgrade'. Raise floors deliberately, package by package, rather than reaching for --upgrade; a fresh resolution moves about 30 packages at once and makes any failure unattributable. coverage is already dealt with by rep-mcpwp.
