---
id: S1-dofra
status: closed
deps: [S1-kovwi, S1-hydza]
links: []
created: 2026-08-09T00:20:14Z
type: feature
priority: 1
assignee: Stavros Korokithakis
---
# Add Dokku deploy workflow and remove GitLab CI

Ready for implementation.

Objective: replace the GitLab deploy job with a GitHub Actions one, then delete the GitLab CI config.

Part 1 - create .github/workflows/deploy.yml, closely following https://github.com/skorokithakis/dead-mans-switch .github/workflows/deploy.yml:
- trigger: workflow_run on the 'pre-commit' workflow, types [completed], branches [master]
- job guard: only run when github.event.workflow_run.conclusion == 'success' AND github.event.workflow_run.event == 'push'
- steps: actions/checkout@v4 with fetch-depth 0; webfactory/ssh-agent@v0.9.0 with ssh-private-key from the DOKKU_SSH_KEY secret; write an ~/.ssh/config entry for host projects.stavros.io with Port 16022, StrictHostKeyChecking no, UserKnownHostsFile /dev/null; add a 'dokku' git remote and push master to it.

Target, from the old GitLab config: ssh://dokku@projects.stavros.io:16022/pastery. The app name is 'pastery' (the DMS repo uses 'deadmansswitch', so do not copy that verbatim). Port 16022 goes in the SSH config, not the remote URL.

Part 2 - delete .gitlab-ci.yml.

Caveats:
- fetch-depth 0 is required. Dokku needs the full history for the push.
- Keep misc/terraform/ untouched. The GitLab terraform job used GitLab-managed remote state, which has no GitHub equivalent. It is being dropped from CI deliberately; Terraform will be run by hand.
- The repo uses git-crypt. Encrypted blobs are pushed as-is, exactly as GitLab did. Do not add any decryption step.
- Deploying from the branch tip rather than the exact commit that passed CI is a known and accepted tradeoff.

Non-goals: do not add a Terraform workflow. Do not add a claude.yml workflow. Do not change misc/dokku/*, the Dockerfile, or any deployment setting. Do not create the DOKKU_SSH_KEY secret; that is a manual step for the repo owner.

## Design

Deploy chains off workflow_run of 'pre-commit' rather than off push, so a failing lint run blocks the deploy. The tests workflow is deliberately not part of that chain, which matches the reference repo.

## Acceptance Criteria

The workflow pushes to the correct Dokku app on a successful master build, and .gitlab-ci.yml is gone.

