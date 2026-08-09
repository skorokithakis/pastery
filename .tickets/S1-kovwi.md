---
id: S1-kovwi
status: closed
deps: []
links: []
created: 2026-08-09T00:19:45Z
type: feature
priority: 1
assignee: Stavros Korokithakis
---
# Add GitHub Actions pre-commit workflow

Ready for implementation.

Objective: port the lint/type-check half of the GitLab CI 'test' job to GitHub Actions.

Create .github/workflows/pre-commit.yml:
- name: pre-commit
- triggers: pull_request, and push to master
- single job on ubuntu-latest
- steps: actions/checkout@v4, actions/setup-python@v5 pinned to python-version 3.9, pre-commit/action@v3.0.1 with extra_args '--all-files --hook-stage=manual'

Reference implementation: https://github.com/skorokithakis/dead-mans-switch .github/workflows/pre-commit.yml

Caveats:
- The workflow NAME must be exactly 'pre-commit'. The deploy workflow keys off it via workflow_run.
- Do NOT install project dependencies, run migrate, or run collectstatic. The GitLab job did that, but pre-commit hooks run in isolated environments and do not need it.
- --hook-stage=manual matches the GitLab job and must be kept.
- Python is pinned to 3.9 to match the Dockerfile (python:3.9-slim). Do not use a newer version. Django 2.0 cannot be imported on Python 3.12+.

Non-goals: do not change .pre-commit-config.yaml, do not fix any lint errors the workflow surfaces (report them instead), do not touch .gitlab-ci.yml.

## Acceptance Criteria

The workflow file is valid YAML, is named 'pre-commit', and runs the same check the GitLab 'test' job ran.

