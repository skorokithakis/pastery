---
id: rep-mybaj
status: closed
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


## Notes

**2026-08-12T15:52:30Z**

Researched the majors so they do not need rediscovering. Verified 2026-08-12; re-check if this sits for a while.

- actions/checkout v4 -> v7 (node24). The allow-unsafe-pr-checkout breaking change in v5+ only affects pull_request_target and issue_comment triggers, so it does not touch us.
- actions/setup-python v5 -> v7 (node24). v7 dropped the pip-install input, which we do not use.
- webfactory/ssh-agent v0.9.0 -> v0.10.0. Pure node24 bump, nothing else changed. Only the deploy job uses it, and that job does not run on a pull request, so CI cannot prove it. Accepted risk.
- actions/cache v4 is node20; v5 and v6 are node24.

Keep the existing pinning style: floating major for actions/*, exact tag for third-party.

Python 3.9 survives the bump: ubuntu-latest is Ubuntu 24.04 today and the version manifest has 3.9.25 built for 24.04. Confirm it resolves anyway.

**2026-08-12T15:52:41Z**

Decisions taken, both open questions in the description are now closed.

1. pre-commit job: inline the action. pre-commit/action@v3.0.1 is a composite action with actions/cache@v4 hardcoded inside it, which cannot be overridden, and upstream is in maintenance-only mode. Replace it with the three steps that matter, dropping only its "pip freeze --local" debug step:

    - run: pip install pre-commit
    - uses: actions/cache@v6
      with:
        path: ~/.cache/pre-commit
        key: pre-commit-3|${{ env.pythonLocation }}|${{ hashFiles('.pre-commit-config.yaml') }}
    - run: pre-commit run --show-diff-on-failure --color=always --all-files --hook-stage=manual

Keep the cache; without it every run rebuilds the mypy hook environment. Do not pin pre-commit: unpinned matches today's behaviour exactly. Add a short comment saying that the 3.9 pin caps pip's resolution at pre-commit 4.3.0, because 4.6 and newer need Python 3.10, so CI deliberately runs an older pre-commit than a developer's machine will.

2. cloudflare-ips.yml: delete the setup-python step rather than bumping it. The script is standard-library only, so it needs no pinned interpreter, and deleting the step removes the annotation instead of deferring it. This overrides the "no other CI changes" non-goal in the description, deliberately. Invoke it as "python3 misc/check_cloudflare_ips.py", not "python": python3 is guaranteed and matches the script's own shebang. Adjust the comment above the step, which currently explains why nothing is installed, so it also covers why there is no interpreter pin.

Note that this leaves ci.yml as the only place pinning 3.9 in a workflow, which is what S1-picfo will edit.

**2026-08-12T15:52:44Z**

ready for implementation
