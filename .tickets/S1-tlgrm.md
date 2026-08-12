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

**2026-08-12T20:27:14Z**

Preview from the 4.2 rung, measured with the suite running under warnings-always.

Warnings pointing at this rung: USE_L10N (RemovedInDjango50Warning, delete per the description), STATICFILES_STORAGE (RemovedInDjango51Warning, replace with STORAGES per the description), and webauthin 0.0.6's own migration 0003 using the deprecated django.utils.timezone.utc alias, removed in 5.0, so webauthin 0.0.6 likely cannot even migrate on 5.x and must be bumped here. Its AuthData naive-datetime RuntimeWarning is a second reason; check whether a newer webauthin fixes both.

Filter gotcha: RemovedInDjango51Warning is a PendingDeprecationWarning in 4.2, so PYTHONWARNINGS=always::DeprecationWarning does not show the STATICFILES_STORAGE warning. Use plain PYTHONWARNINGS=always for the warning report on this rung.

Also carried forward: tokenauth 0.5.5 is the LAST release and still probes the pre-4.x ratelimit module names, so the login rate-limit shim in pastery/urls.py stays alive on this rung too; its comment is current. django-annoying 0.10.6, django-bootstrap3 12.1.0, django-redis 4.11.0 and whitenoise 5.0 survived 4.2 unchanged, but 5.2 may be the rung that finally forces some of them; whitenoise 5.0 predates the STORAGES dictionary, so expect the STORAGES change to force a whitenoise floor raise.
