---
id: S1-nfunh
status: closed
deps: []
links: []
created: 2026-08-09T09:00:44Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Consolidate CI into a single workflow so deploy needs tests

Ready for implementation.

Objective: replace the three separate workflow files with one .github/workflows/ci.yml containing three jobs, so that deploy depends on BOTH checks and runs on the exact commit that passed.

Why: deploy.yml currently triggers via workflow_run on the 'pre-commit' workflow only, so a red test run does not block a production deploy. Adding 'tests' to the workflow_run list does NOT fix this, because workflow_run treats that list as OR.

Delete .github/workflows/pre-commit.yml, tests.yml and deploy.yml. Create .github/workflows/ci.yml:
- name: CI
- triggers: pull_request, and push to master (block style, as the current files use)
- top-level 'permissions: contents: read'
- job 'pre-commit': same steps as the current pre-commit.yml, unchanged
- job 'tests': same steps as the current tests.yml, unchanged
- job 'deploy': same steps as the current deploy.yml, plus 'needs: [pre-commit, tests]' and 'if: github.event_name == 'push' && github.ref == 'refs/heads/master''. Drop the workflow_run trigger and the old workflow_run if-guard, which no longer apply.

Keep the emoji step names on the deploy job. The workflow itself is named 'CI', not the old emoji name.

Also update the two README.md badges. They point at tests.yml and pre-commit.yml, which will no longer exist. Replace them with a single badge for ci.yml, same inline-link Markdown style.

Caveats:
- Do NOT change any step content, action version, or the Python 3.9 pin. This is a restructure, not a rewrite.
- fetch-depth 0 on the deploy checkout is still required.
- On a push event actions/checkout creates a real local 'master' branch, so 'git push dokku master' still works. Do not switch to pushing HEAD.
- The deploy job must not run on pull_request events, including from forks. The if-guard covers this.

Non-goals: do not add caching, do not add a concurrency group, do not add matrix builds, do not change the Dokku target, do not touch poetry.lock or pyproject.toml.

## Design

Chose one workflow with job-level 'needs' over three workflows chained by workflow_run. It gates deploy on both checks, which workflow_run cannot express, and it removes the branch-tip race because the deploy job runs in the same run on the tested commit. Cost is that the layout no longer mirrors the dead-mans-switch repo.

## Acceptance Criteria

One workflow file. Deploy runs only after both checks pass, only on push to master, and pushes the tested commit to the pastery Dokku app.

