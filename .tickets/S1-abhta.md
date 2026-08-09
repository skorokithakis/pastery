---
id: S1-abhta
status: closed
deps: [S1-picfo]
links: []
created: 2026-08-09T17:57:13Z
type: chore
priority: 3
assignee: Stavros Korokithakis
---
# Stop Pygments bumps from generating huge migrations

Objective: end the migration churn. Optional cleanup, not part of the upgrade.

main/models.py builds LANGUAGES from the Pygments lexer list at import time and passes it as a model field's choices. Django serialises the evaluated list into a migration, so every Pygments bump writes a migration of roughly 470 lines. There are 32 migrations in main/ and most of them are exactly this, and nothing else.

Django 5.0 accepts a callable for choices and records the callable reference in the migration rather than the evaluated list. Convert the language choices, and the style choices if they have the same problem, to callables.

Caveat: this moves the choice list from migration time to runtime. Confirm the paste form in main/views.py and the admin in main/admin.py still offer the same options, and confirm that makemigrations produces nothing after the conversion migration itself.

Non-goals: do not squash or delete any existing migration.

## Acceptance Criteria

The conversion migration does not inline the language list. makemigrations --check is clean afterwards. The paste form still lists the same languages in the same order.


## Notes

**2026-08-09T18:40:35Z**

Cancelled, not done. Obsoleted by commit d17dbd7, which removed choices= from Paste.raw_language and moved the list onto the paste form and a new admin form instead. That fixes the churn at the root on Django 2.0, so the Django 5.0 callable-choices approach this ticket proposed is no longer needed. The root cause turned out to be better than my guess: get_all_lexers() also returns lexers registered by other installed packages through the pygments.lexers entry point, and IPython registers three, so the choices list differed by three entries depending on whether dev dependencies were installed.
