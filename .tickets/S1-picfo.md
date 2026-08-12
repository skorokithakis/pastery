---
id: S1-picfo
status: closed
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

**2026-08-12T17:42:21Z**

Add coverage to the marker-split list in the note above. rep-mcpwp raised the coverage floor to >=7,<8 and the lock now holds coverage 7.10.7 for python_full_version < 3.10 and 7.15.4 for >= 3.10, because 7.10 is the last line that runs on 3.9. Moving to 3.13 silently selects 7.15.4. Coverage 7.15.4's 'coverage report' was exercised on 3.13 and works, but statement attribution does shift slightly between 7.x minor versions, so expect the percentage to move a little on this rung and do not read that as a regression.

**2026-08-12T17:45:30Z**

Stopgap from the 2026-08-12 note is now in place: the pre-commit and tests jobs in ci.yml pin runs-on to ubuntu-24.04, because they are the only jobs that ask setup-python for 3.9. Remember to flip them back to ubuntu-latest on this rung, the comment above the jobs block says so too.

**2026-08-12T20:35:46Z**

Being executed together with S1-tlgrm as one combined rung, per Stavros's decision of 2026-08-12; see the note there. The dependency arrow stays for bookkeeping but both close together. Everything in this ticket's notes (bleach floor, marker-split report, golden rendering re-run, ubuntu-24.04 pin removal) is in scope for the combined rung.

**2026-08-12T21:28:45Z**

Done, shipped together with S1-tlgrm as one commit. Python 3.13 in all six places (Dockerfile, .python-version, both ci.yml pins, requires-python, setup.cfg mypy). Stale 3.9 comments deleted; ubuntu-24.04 pins removed after verifying 3.13 has ubuntu-26.04 builds in the actions manifest. bleach floor raised to >=6.4,<7 and its comment deleted. Marker splits selected their new branch: bleach 6.4.0, markdown 3.10.3, requests 2.34.2, coverage 7.15.4, asgiref 3.12.1, regex 2026.7.19, urllib3 2.7.0; golden rendering tests re-run deliberately, output byte-identical. Forced by 3.13: psycopg2-binary >=2.9.10 (first cp313 wheels), uwsgi >=2.0.27 (2.0.21 uses _PyImport_AcquireLock, removed in 3.13; 2.0.31 built from sdist and served HTTP under 3.13 locally, CI docker job is the final gate), greenlet dev floor, mypy>=1.16 and flake8>=5 in the dev group. django-stubs deleted rather than bumped: dev-only, the pre-commit mypy hook never used it, and 1.15 was wrong for 5.2.
