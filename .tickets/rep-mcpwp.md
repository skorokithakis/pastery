---
id: rep-mcpwp
status: closed
deps: []
links: []
created: 2026-08-12T17:25:49Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Raise the coverage floor so the safety net is legible

Objective: make the coverage report tell the truth before the risky Django rungs run, not after.

coverage is locked at 4.4.2 (2017). It is an unconstrained dependency in pyproject.toml, so it will never move on its own: plain 'uv lock' is preference-preserving, and no rung of the Django ladder names coverage because it is not a Django package. gnosis reanmn assumed it would be 'upgraded later in the chain'. Nothing in the chain does it.

Scope:
- Raise the coverage constraint in pyproject.toml to >=7,<8 and re-lock.
- Only coverage may move. Do NOT run 'uv lock --upgrade'; a fresh resolution drags in about 30 unrelated bumps and that is a separate decision belonging to the Django rungs.
- Do NOT edit .coveragerc. The omit list is already correct; it only looked broken because basename matching arrived in coverage 6. Confirm 'main/admin.py' now actually drops out of the report rather than assuming it.
- Report the coverage percentage before and after, and confirm the phantom statements attributed to main/models.py beyond line 705 are gone.
- Update gnosis reanmn, or supersede it with a new entry that references it. Its two caveats stop being true with this change and a stale caveat is worse than none.

Non-goals: no --fail-under gate, no CI changes, no .coveragerc edits, no other dependency bumps, no test changes.

Caveats: coverage is invoked as 'coverage run ./manage.py test' and 'coverage report' in ci.yml; both spellings are stable across 4.4 to 7, but confirm rather than assume. Coverage is not gated in CI, so a number that moves cannot turn master red. Python is still 3.9 on this rung, so the resolver must pick a 3.9-compatible coverage 7.

## Acceptance Criteria

Coverage report is truthful: no statements attributed past the real end of main/models.py, main/admin.py omitted as .coveragerc intends. Suite still green. uv.lock shows coverage and its own dependencies moving, and nothing else.


## Notes

**2026-08-12T17:25:56Z**

ready for implementation

**2026-08-12T17:42:21Z**

Done. coverage 4.4.2 -> 7.10.7 on Python 3.9 (7.15.4 above 3.10; 7.10 is the last line supporting 3.9). Only coverage moved in the lock, and coverage 7 declares no runtime dependencies, so the diff is literally just coverage.

Reported total went 44% -> 93% on the same 92 tests. Both reanmn claims verified and now dead: main/models.py had phantom missing lines 749-2046 in a 729-line file and now reports nothing past line 653; main/admin.py was in the report at 48% and is now correctly omitted by .coveragerc without editing it. 4.4.2's distortion was worse than reanmn described, the test files themselves reported 17-63% with inflated statement counts and all report 100% now.

reanmn edited to record the resolution, gtxgkc corrected because its closing sentence had become false. ci.yml spellings unchanged and still exit 0.
