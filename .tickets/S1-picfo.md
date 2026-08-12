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

**2026-08-12T13:19:38Z**

Two things S1-nweul left for this rung.

1. Raise the bleach floor in pyproject.toml to >=6.4,<7 once Python is 3.13, and delete the comment above it. 6.4 fixes GHSA-8rfp-98v4-mmr6 and needs Python 3.10, so 3.9 was stuck on 6.2.

2. uv.lock currently holds marker-split versions: bleach 6.2/6.4, markdown 3.9/3.10.3, requests 2.32.5/2.34.2, split on python_full_version 3.10. Moving to 3.13 silently selects the newer branch of each. Report which versions actually change, and re-run the golden rendering tests deliberately rather than assuming the Python bump cannot touch rendering.

**2026-08-12T15:52:47Z**

Deadline pressure on this rung, found while researching rep-mybaj on 2026-08-12.

Python 3.9 has no Ubuntu 26.04 build. The actions/python-versions manifest stops at 24.04 for the whole 3.9 series. ubuntu-latest is 24.04 today, but 26.04 is already published as a preview runner image. When ubuntu-latest flips to it, setup-python can no longer supply 3.9 and CI goes red with no commit from us.

This ticket is the only thing that frees us from the pin, so the ladder below it is on a clock we do not control. If ubuntu-latest flips before the ladder finishes, the stopgap is to pin runs-on to ubuntu-24.04 in ci.yml rather than to rush a Django rung.
