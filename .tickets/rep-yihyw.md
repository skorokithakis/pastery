---
id: rep-yihyw
status: closed
deps: []
links: []
created: 2026-08-10T19:11:10Z
type: task
priority: 1
assignee: Stavros Korokithakis
---
# Stop the flaky poetry install in the tests job

Objective: make 'poetry install --no-root' deterministic for the rest of the modernisation chain.

The tests job sets 'poetry config virtualenvs.create false', so Poetry installs into the runner's system Python and downgrades its setuptools to the locked 67.6.0 partway through the install. Any sdist that gets built after that point runs against a half-swapped setuptools and fails. Which package it hits depends on install ordering and on whatever setuptools the runner image ships that week, so the same commit passes and then fails with no change to the repo. Seen on curtsies 0.4.1 twice, and previously on cbor2.

Two packages in this dependency set have no wheels at all and so must be built every time: curtsies 0.4.1, pulled in by bpython, and uwsgi 2.0.21, which is a main dependency. Either can be the one that fails.

Fix: install the locked setuptools before Poetry runs, so there is no version swap partway through. Add a step after 'pip install poetry==1.4.0' and before 'poetry install --no-root':

    - run: pip install setuptools==67.6.0

The version must match what poetry.lock pins, which is 67.6.0 today. Add a comment saying this is a temporary prop for the pinned 2020-era dependency set, that it exists to stop the mid-install setuptools swap, and that it is deleted when the project moves to uv.

Scope: .github/workflows/ci.yml only.

Non-goals: do not remove 'virtualenvs.create false'. That would work too, but it forces every later step through 'poetry run' and is a bigger change for no extra benefit two tickets before Poetry is deleted. Do not upgrade or remove any package, do not touch poetry.lock or pyproject.toml, and do not bundle any other ticket.

## Acceptance Criteria

The tests job installs the locked setuptools before poetry install. CI is green. Nothing outside .github/workflows/ci.yml changes.


## Notes

**2026-08-10T19:11:14Z**

ready for implementation

**2026-08-10T19:22:19Z**

The setuptools pre-install was the wrong fix and made things worse. It is reverted.

Evidence from four runs of the same commit. When ambient setuptools was 79.0.1 at the moment curtsies was built, the build succeeded. When it was 67.6.0, either because the swap landed mid-build or because the pre-install put it there from the start, the build failed. Pinning 67.6.0 up front removed the race but guaranteed the losing state, so an intermittent failure became an every-run failure.

So the trigger is the locked setuptools 67.6.0 being present in the ambient environment, not the swap itself. The swap only mattered because it was one way of arriving at that state.

New direction, which is the fix the CI notes already called the proper one: stop 'virtualenvs.create false'. With Poetry owning the system Python, its ephemeral build environment sees the ambient site-packages, so the locked setuptools collides with the setuptools the build environment resolves for itself. A real virtualenv isolates the two and leaves the runner's own setuptools alone. Cost is a 'poetry run' prefix on the four steps after the install.

Non-goal reversed: the description forbids touching 'virtualenvs.create false'. Ignore that. It is now the point of the ticket.
