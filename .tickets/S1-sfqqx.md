---
id: S1-sfqqx
status: open
deps: []
links: []
created: 2026-08-09T17:55:14Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Run the test suite on PostgreSQL 18 and drop django-nose

Objective: make the test suite exercise the same database as production, and remove the dead test runner.

Production was just upgraded from PostgreSQL 9.6 to 18, while still on Django 2.0. So this ticket also verifies the current code against the new server.

Work:
- Remove django_nose from INSTALLED_APPS, delete TEST_RUNNER and NOSE_ARGS from pastery/settings.py, remove django-nose from pyproject.toml. Django's default DiscoverRunner takes over; the suite already passes under it.
- Coverage moves to a plain 'coverage run ./manage.py test' plus 'coverage report'. Coverage config must live in exactly one file: .coveragerc and the [coverage:run] block in setup.cfg currently duplicate each other.
- The CI tests job gets a PostgreSQL 18 service container. Point Django at it by writing pastery/local_settings.py from the workflow; settings.py already imports that file at the end inside a try/except. Do NOT set DATABASE_URL to do this: that branch also switches sessions to Redis and parses EMAIL_URL with a regex that will raise.
- docker-compose.yml: postgres:9.6 becomes postgres:18.
- Bump psycopg2-binary only if 2.8.6 cannot talk to PostgreSQL 18.

Report explicitly, as the first line of your summary: does './manage.py migrate' succeed against PostgreSQL 18 on the current Django 2.0 code? PostgreSQL 12 removed the pg_attrdef.adsrc column and Django 2.0's Postgres introspection reads it. Production already runs 18, so if this is broken then deploys are broken right now and I need to know immediately.

Non-goals: no new tests, no Django version change, no other dependency upgrades.

Caveat: use Poetry 1.4.0 for any lock operation. Poetry 2.x rewrites the whole lock into a new format.

## Acceptance Criteria

CI tests job runs against PostgreSQL 18 and is green. Coverage is still reported. No reference to django-nose or nose remains in the repo.


## Notes

**2026-08-09T18:03:22Z**

Update from production, 2026-08-09. Stavros ran migrate against PostgreSQL 18 on the live Django 2.0 image. It works: 'No migrations to apply', no introspection error. So the pg_attrdef.adsrc concern is cleared and deploys are not currently broken. You no longer need to answer that question; treat it as settled.

But the same run exposed a dirty baseline. makemigrations produces a pending 'Alter field raw_language on paste' that is not in the repo. The last choices migration is 0027, generated 2025-07-28, and main/models.py has not changed the language list since. So either the Pygments version that generated 0027 differs from the one poetry.lock pins at 2.10.0, or something in the deployed image registers extra Pygments lexers.

Add to this ticket: generate that migration and commit it, so the baseline is clean before anything else moves. Two things to report:
- What actually differs in the generated choices list. Name the languages that appear or disappear. I want to know the cause, not just the symptom.
- Whether generating it twice in the CI environment is stable, that is, whether the second run produces nothing further.

This AlterField only changes choices, which is form and admin validation only, so it emits no SQL on PostgreSQL and is deploy-neutral. Several later tickets use 'makemigrations --check is clean' as acceptance, and they all depend on this baseline being fixed first.

**2026-08-09T18:40:36Z**

The dirty-baseline part of my earlier note is done, by commit d17dbd7. Migration 0031 is committed, choices= is off Paste.raw_language, and the tests job already runs makemigrations --check --dry-run before collectstatic. Do not redo any of it. Your baseline is origin/master at c0aef60, which is ahead of this workspace; pull before you start.
