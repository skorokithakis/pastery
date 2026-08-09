---
id: S1-hydza
status: closed
deps: []
links: []
created: 2026-08-09T00:19:58Z
type: feature
priority: 1
assignee: Stavros Korokithakis
---
# Unbreak poetry install and add GitHub Actions tests workflow

Ready for implementation.

Objective: make 'poetry install' work again, then add a workflow that runs the Django test suite.

Part 1 - unbreak poetry install.
'poetry install --no-root' currently fails. django-webauthin pulls in cbor2 5.1.2, which is published as an sdist only (no wheels at all), and its build fails against modern setuptools with 'ModuleNotFoundError: No module named pkg_resources'.
Fix: run 'poetry update cbor2' and commit the resulting poetry.lock. Verified to work on Python 3.9. Change ONLY the cbor2 entry and whatever the resolver must touch alongside it. Do not regenerate the whole lock file and do not edit pyproject.toml.

Part 2 - create .github/workflows/tests.yml:
- name: tests
- triggers: pull_request, and push to master
- single job on ubuntu-latest
- steps: actions/checkout@v4; actions/setup-python@v5 with python-version 3.9; install poetry; 'poetry install --no-root'; 'poetry run ./manage.py collectstatic --noinput'; 'poetry run ./manage.py test'

Reference implementation: https://github.com/skorokithakis/dead-mans-switch .github/workflows/tests.yml (that repo uses uv; this one uses Poetry, so adapt).

Caveats:
- collectstatic MUST run before the tests. Settings use whitenoise CompressedManifestStaticFilesStorage, so templates cannot render without a manifest.
- No database or cache service is needed. Settings fall back to SQLite and locmem when IN_DOCKER and DATABASE_URL are unset. Do not add service containers.
- Python is pinned to 3.9 to match the Dockerfile. Django 2.0 cannot be imported on Python 3.12+ (distutils was removed).
- The suite currently passes: 41 tests, all green. If anything fails in CI, it is an environment problem, not a broken test. Do not modify test files to make CI pass; report the problem instead.
- TEST_RUNNER is django_nose and NOSE_ARGS includes --with-coverage, so the run writes an htmlcov/ directory. That is gitignored already.

Non-goals: do not upgrade Python, Django, or any other dependency. Do not replace django-nose. Do not add coverage reporting or upload artifacts. Do not touch .gitlab-ci.yml.

## Acceptance Criteria

'poetry install --no-root' succeeds on Python 3.9, and the workflow runs all 41 tests to a green result.

