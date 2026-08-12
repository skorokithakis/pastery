---
id: rep-hczwu
status: closed
deps: []
links: []
created: 2026-08-12T14:32:45Z
type: chore
priority: 2
assignee: Stavros Korokithakis
---
# Fail CI when the committed Cloudflare ranges drift from the published lists

Objective: the Cloudflare ranges committed in pastery/ratelimit.py are a maintenance point. If Cloudflare publishes a new range and the list is not refreshed, every visitor arriving through that range is bucketed by the edge IP they share and gets rate limited as one visitor. If Cloudflare withdraws a range and we keep it, we trust a range that now belongs to someone else. Neither is visible without a check, so add one.

Scope: a new script misc/check_cloudflare_ips.py and a new workflow .github/workflows/cloudflare-ips.yml. Nothing else changes. Do not touch the ranges themselves.

The workflow:
- Must be its own file, not a job in ci.yml. The jobs in ci.yml gate the deploy job through "needs", and a check that depends on reaching cloudflare.com must never be able to block a deploy or turn an unrelated pull request red.
- Triggers: a weekly schedule plus workflow_dispatch. Not on push or pull_request.
- Steps: checkout, setup-python, run the script. No dependency install, see below.

The script:
- Fetches https://www.cloudflare.com/ips-v4 and https://www.cloudflare.com/ips-v6 using nothing but the standard library.
- Reads the committed CIDRs out of pastery/ratelimit.py as text rather than importing the module. Importing it would pull in Django and so force the whole pinned dependency set to be installed just to read two tuples. Say this in a comment, so the next person does not "fix" it into an import.
- Because it reads source text, it must fail loudly rather than silently pass if the constants are ever reformatted: assert it extracted a non-zero number of ranges, and that every extracted value parses as a network.
- Compares both directions and reports both, because they are different problems: published but missing from our list, and present in our list but no longer published.
- On a mismatch, print the ranges to add and the ranges to remove, so fixing the list is copy and paste. Exit non-zero.
- Retry the fetch a couple of times with a timeout, so one transient network failure does not raise a false alarm every week. A fetch that fails after the retries should still fail the job, with a message that says the fetch failed rather than implying drift.

Non-goals: do not open a pull request or edit the list automatically. Do not add the check to ci.yml. No new dependency.

## Acceptance Criteria

Running the script locally exits zero against the list committed today, and exits non-zero with a readable report when a range is added to or removed from the committed tuples by hand.


## Notes

**2026-08-12T14:32:45Z**

ready for implementation
