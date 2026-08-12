---
id: rep-mybaj
status: open
deps: []
links: []
created: 2026-08-12T15:43:20Z
type: chore
priority: 3
assignee: Stavros Korokithakis
---
# Move the GitHub Actions off deprecated Node 20

Objective: stop the workflows depending on a deprecated runtime. Every run of CI now annotates that actions/checkout@v4, actions/setup-python@v5, actions/cache@v4 and webfactory/ssh-agent@v0.9.0 target Node 20, which is deprecated and is already being forced onto Node 24. Nothing is broken yet; it will break when the runners stop forcing it.

Where they are pinned:
- .github/workflows/ci.yml: checkout and setup-python in the pre-commit and tests jobs, checkout in the docker job, checkout and webfactory/ssh-agent in the deploy job.
- .github/workflows/cloudflare-ips.yml: checkout and setup-python.

Bump each to a major that runs on Node 24. Check what the current majors actually are at implementation time rather than trusting this description.

Two wrinkles to expect:
- actions/cache@v4 is not ours. It comes from inside pre-commit/action@v3.0.1, so it cannot be bumped directly. That action is also unmaintained upstream, and its own README points people at running pre-commit directly instead. Replacing it with an explicit pre-commit install and run, keeping the --all-files --hook-stage=manual arguments, may be the only way to clear that annotation. Decide which, and say why.
- The Python pin must stay 3.9 in both workflows. It matches the Dockerfile and Django 2.0 cannot be imported on 3.12 or newer. S1-picfo moves it later; do not anticipate that here. Confirm the runner still provides 3.9 with the newer setup-python.

Non-goals: no other CI changes, no new jobs, no change to what any job does.

## Acceptance Criteria

CI is green on a pull request and the Node 20 deprecation annotations are gone from every job. The pre-commit, tests, docker and deploy jobs still do exactly what they did before, and Python stays pinned to 3.9.

