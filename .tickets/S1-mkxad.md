---
id: S1-mkxad
status: closed
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

**2026-08-09T18:47:12Z**

ready for implementation

**2026-08-10T20:06:29Z**

Scope corrections found before starting.

1. PRODUCTION TRAP. misc/dokku/Procfile hardcodes '/usr/local/bin/uwsgi'. That path works today only because 'poetry config virtualenvs.create false' installs into the image's system Python. A default 'uv sync' would put uwsgi in /code/.venv/bin instead, the Procfile would point at nothing, and the container would fail at boot. 'docker build succeeds', this ticket's acceptance criterion, would still pass, and master auto-deploys to Dokku on push, so this breaks production without any red in CI.

Decision: keep installing into the system Python. Set ENV UV_PROJECT_ENVIRONMENT=/usr/local in the Dockerfile so uv sync targets the system prefix. /usr/local/bin/uwsgi stays valid and the Procfile is not touched. This is also the minimal diff, which is what we want from a tooling swap.

2. Stronger acceptance: build the image AND run it, confirm uwsgi actually starts and serves. Build success alone is not enough here.

3. ci.yml has moved on since this ticket was written. It no longer has 'two Poetry invocations': there are six, at lines 48, 54, 74, 77, 78 and 79. The setuptools pre-install prop is already gone, replaced by a real virtualenv in c56e3d6. The comment at lines 49-53 explains that workaround and must be deleted with it, as must the Python-3.9 rationale comment only if the pin moves, which it does not here.

4. README lines 15-18 also use poetry. Update them.

5. Keep requires-python as '>=3.8,<4', matching the current Poetry constraint, even though the image and CI both run 3.9. Changing the floor changes the resolution input and would undermine the 'resolved set matches poetry.lock' check. Narrowing it is a separate decision.

6. Pin the uv version in both the Dockerfile and CI, for the same reproducibility reason Poetry was pinned. Removing the Poetry pin does not mean going unpinned.

**2026-08-10T22:16:28Z**

Rejecting the first conversion of pyproject.toml. It pinned every direct dependency with '==' and added a 45-entry [tool.uv] constraint-dependencies block holding every transitive version.

That does make the resolution match, but by moving the lock into the manifest. pyproject then no longer states which versions are ACCEPTABLE, only which are currently installed, which is uv.lock's job. Two costs, and the second is the real one:

- The next three tickets in this chain all edit these very packages. S1-nweul bumps markdown, bleach, textile and pygments; S1-bldcp replaces django-brake; S1-bskcx replaces raven. Each would have to fight hard pins, and worse, fight constraint-dependencies pins on cryptography, setuptools and friends that have nothing to do with the package being changed.
- A tooling swap should not silently change what the manifest means.

Correct approach: translate the existing Poetry constraints faithfully, one for one. 'bleach = "*"' becomes 'bleach', 'django = "==2.0.*,>=2.0.0"' becomes 'django>=2.0,<2.1', 'django-ipware = "~=2.1.0"' becomes 'django-ipware~=2.1.0', and so on. No constraint-dependencies block. uv.lock holds the exact versions, because that is what a lock file is for. Then prove the resolved set still matches poetry.lock.

**2026-08-11T05:30:21Z**

Now I understand why attempt one pinned everything, and I was wrong to reject it outright without an alternative.

poetry.lock froze every open constraint years ago. 'bleach = "*"' is locked at 3.2.0, pygments at 2.10.0, whitenoise at 5.0, coverage at 4.4.2, pytz at 2020.1. Poetry kept them there because the lock was only ever refreshed with --no-update, which prefers locked versions. A fresh uv resolution has no such history, so a FAITHFUL translation of the loose constraints legitimately resolves bleach to 6.2.0 and pygments to 2.20.0. That is not uv misbehaving; it is what 'bleach = "*"' has always permitted.

Consequence: the suite goes red, 1 failure and 7 errors, all in PasteRenderingTests. bleach 4.0 removed the 'styles' argument to Cleaner, which main/models.py:187 still passes, and pygments now emits Whitespace tokens, which breaks the byte-exact golden. Both are precisely the tripwires S1-jlmlp installed, and re-baselining them belongs to S1-nweul, not here.

So there are two ways to satisfy 'the resolved main dependency set matches what poetry.lock produced':

A. Pin exact versions in pyproject, plus a constraint-dependencies block for the transitives. Rejected: it moves the lock into the manifest and the transitive pins will fight S1-nweul, S1-bldcp and S1-bskcx.

B. Keep the faithful loose constraints in pyproject and seed uv.lock with the old versions, then re-lock WITHOUT --upgrade so uv preserves them. uv treats an existing uv.lock as a preference source, exactly as Poetry did with --no-update. End state: manifest states what is acceptable, lock states what is installed, versions unchanged, suite green.

Going with B. It reproduces the semantics the repo already relied on, and it leaves the later upgrade tickets a clean lever: edit the constraint, then 'uv lock --upgrade-package X'.

Also worth fixing while here: 'uv sync --no-dev' is deprecated in uv 0.11, prefer '--no-group dev'. And the .venv in the tree is a Poetry-era environment that uv adopted, with stale INSTALLER stamps; rebuild it from scratch so the verification means something.

**2026-08-11T10:28:29Z**

Cannot verify the image in this environment: there is no Docker daemon and no privileges to start one. That matters, because nothing else verifies it either. ci.yml builds no image; the Dockerfile is first exercised by Dokku at deploy time, on a push to master. Dokku's CHECKS file does an HTTP check, so a bad image fails the deploy and the old container keeps serving rather than the site going down, but the failure would still be discovered in production.

This ticket rewrites the image's entire install mechanism, so shipping it unverified is not acceptable. Adding a 'docker' job to ci.yml that builds the image and boots it with the Procfile's real command, and making deploy depend on it. Small, and it pays for itself on every later ticket in this chain, all of which touch dependencies.

Confirms the system-Python decision was right for a second reason: docker-compose.yml runs 'python manage.py ...' directly, so a /code/.venv would have broken local development too, not just the Procfile.
