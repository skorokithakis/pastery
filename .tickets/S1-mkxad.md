---
id: S1-mkxad
status: open
deps: [S1-ixple]
links: []
created: 2026-08-09T17:56:58Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Replace Poetry with uv

Objective: move dependency management to uv, and remove the Poetry 1.4.0 pin.

The pin exists because Poetry 2.x rewrites the lock file into a new format. Poetry 1.4.0 dates from early 2023 and is not expected to install on Python 3.13, so the tooling has to change before the Python bump can happen. uv is the replacement.

Work:
- Convert pyproject.toml to PEP 621 metadata with uv's dependency groups. Preserve the split between main dependencies and dev dependencies; the Dockerfile installs main only.
- Generate uv.lock and delete poetry.lock.
- Update the Dockerfile and both Poetry invocations in .github/workflows/ci.yml.
- The Dockerfile has a duplicated 'ADD pyproject.toml' line. Clean it up while you are there.

Keep Python pinned at 3.9 in this ticket. The Python bump is the next ticket and I want the tooling change verifiable on its own.

Report any dependency whose resolved version changes as a result of the switch.

## Acceptance Criteria

docker build succeeds. CI is green. The resolved main dependency set matches what poetry.lock produced, with any difference reported.


## Notes

**2026-08-09T18:40:50Z**

Moved earlier: this now runs fourth, straight after the dead-dependency deletion, not last. Two reasons.

First, gnosis entry cauqbb records that the tests job's 'poetry install --no-root' is intermittently flaky, because virtualenvs.create false makes Poetry downgrade the runner's system setuptools partway through the install and a later sdist build then runs against the half-swapped version. That flakiness would otherwise hit every one of the ten tickets after this one. uv builds each sdist in its own isolated environment, so it removes the cause rather than working around it.

Second, every later ticket currently carries a 'use Poetry 1.4.0' caveat. Doing this early deletes that rule from all of them.

It sits after the deletion ticket on purpose: that removes fourteen packages, including brotlipy, which has no modern wheels, so uv gets the easiest version of the old dependency set to resolve.

Two corrections to the description above. It no longer says 'the Python bump is the next ticket'; the Python bump stays at the end, after Django 5.2. And if uv cannot resolve the locked set, stop and report. Do NOT upgrade packages to make the resolution succeed: that would smuggle a dependency upgrade into a tooling ticket and we would not know which change caused what.
