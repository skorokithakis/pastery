---
id: S1-tlgrm
status: open
deps: [S1-gxjol]
links: []
created: 2026-08-09T17:56:51Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Upgrade Django 4.2 to 5.2 LTS

Objective: reach the target version. 5.2 LTS is supported until April 2028.

Bump Django to the latest 5.2.x, and bump third-party packages to releases that declare 5.2 support.

Settings changes this rung forces:
- Delete USE_L10N. It was removed in 5.0 and its old behaviour is now the only behaviour.
- Replace STATICFILES_STORAGE, removed in 5.1, with the STORAGES dictionary. Keep whitenoise's CompressedManifestStaticFilesStorage for the staticfiles entry, and Django's default FileSystemStorage for the default entry.

Contingency, to report rather than to work around: PostgreSQL 18 is newer than Django 5.2, which was released before it. If anything misbehaves at the database layer, tell me instead of patching around it. The answer may be to go to Django 6.0 rather than stop at 5.2.

Non-goals: no code cleanup beyond what 5.2 requires.

Caveat: use Poetry 1.4.0 for lock operations. Must stay deployable to Dokku.

## Acceptance Criteria

Suite green on PostgreSQL 18. collectstatic works and produces the static manifest. makemigrations --check is clean.


## Notes

**2026-08-09T18:40:51Z**

Ordering change: uv replaces Poetry before this ticket runs. Ignore the 'use Poetry 1.4.0' caveat in the description; there is no poetry.lock by then. Use uv for all lock operations.

**2026-08-09T18:47:12Z**

ready for implementation
