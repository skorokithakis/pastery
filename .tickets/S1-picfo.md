---
id: S1-picfo
status: open
deps: [S1-tlgrm]
links: []
created: 2026-08-09T17:57:05Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Move from Python 3.9 to 3.13

Objective: the last step of the modernisation. Python 3.13 is inside Django 5.2's tested matrix; 3.14 is not.

Change the version in all four places, in one commit, so that CI and production cannot drift:
- The Dockerfile base image.
- Both pins in .github/workflows/ci.yml, in the pre-commit job and the tests job.
- requires-python in pyproject.toml.
- python_version in the [mypy] section of setup.cfg.

Also delete the comment at the top of ci.yml that explains the 3.9 pin. It says Django 2.0 cannot be imported on 3.12 or newer, which stops being true with this commit.

uwsgi has no wheels and builds from an sdist; the Dockerfile already installs build-essential, so confirm it still builds.

While you are here: django-stubs is pinned at 1.15 and will be wrong for Django 5.2. Either bump it or delete it. It is a dev-only dependency and the pre-commit mypy hook does not use it, because that hook declares no additional_dependencies, so deleting it is defensible. Pick whichever is simpler and say which you did and why.

## Acceptance Criteria

CI, the Dockerfile, pyproject.toml and setup.cfg all name Python 3.13. docker build succeeds. Suite green.


## Notes

**2026-08-09T18:47:12Z**

ready for implementation
