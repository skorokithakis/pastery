---
id: S1-gxjol
status: open
deps: [S1-ocrfa]
links: []
created: 2026-08-09T17:56:43Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Upgrade Django 3.2 to 4.2

Objective: third rung. 4.2 is a transit stop, not a resting place; it is already end of life, so we ship it and move on.

Bump Django to the latest 4.2.x, skipping 4.0 and 4.1 as separate deploys. Bump third-party packages as far as that requires.

This is the rung where the removals bite, because everything dropped in 4.0 and 4.1 lands at once. The three known ones (ugettext, conf.urls.url, request.is_ajax) were already handled in earlier tickets. Expect others that were not found by inspection.

Leave STATICFILES_STORAGE alone. It is deprecated in 4.2 but still works, and it moves in the next ticket.

CI must keep running collectstatic before the tests. Whitenoise's manifest storage means templates cannot render without a collected static manifest.

Report every deprecation warning from the test run, since 5.2 is the next stop.

Non-goals: no code cleanup beyond what 4.2 requires.

Caveat: use Poetry 1.4.0 for lock operations. Must stay deployable to Dokku.

## Acceptance Criteria

Suite green on PostgreSQL 18. collectstatic works. makemigrations --check is clean. POST requests still work; the CSRF trusted-origin settings from the earlier ticket are what makes that true.


## Notes

**2026-08-09T18:40:51Z**

Ordering change: uv replaces Poetry before this ticket runs. Ignore the 'use Poetry 1.4.0' caveat in the description; there is no poetry.lock by then. Use uv for all lock operations.

**2026-08-09T18:47:12Z**

ready for implementation
