---
id: rep-nmlus
status: closed
deps: []
links: []
created: 2026-08-22T11:10:58Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Turn on the remove_spam cron, safely

Ready for implementation.

Objective: the remove_spam management command runs daily on a schedule, with a conservative link-ratio threshold and a size floor, and the first full-table run does not exhaust memory.

Background: the command has apparently never run in production. Every paste in the table still has spam_processed=False, so the first run will scan the entire Paste table.

Scope, two files plus tests.

1. main/management/commands/remove_spam.py
   - Replace the hardcoded 'len(paste.body) >= 50' size gate with a --min-length option, default 500. Purpose: a single pasted URL must never be deleted. The spam URLs seen in the wild are about 60 characters each, so 500 is roughly eight of them.
   - Use 'ratio_threshold is not None' rather than a truthiness test, so --link-ratio 0 means zero rather than off.
   - Iterate the queryset with .iterator(). The database is Postgres, so this uses a server-side cursor instead of loading every paste body into memory. This matters because the first run selects the whole table.
   - Use paste.save(update_fields=['spam_processed']) for the not-spam path.
   - Add tests. There are none for this command today. Cover calculate_link_ratio and the command's delete/keep decisions, including that a body shorter than --min-length is never deleted on the ratio path.

2. misc/dokku/app.json
   - Add a 'cron' key alongside the existing 'scripts' key, with one task: command 'python /code/manage.py remove_spam --link-ratio 0.98 --min-length 500', schedule '@daily', and concurrency_policy 'forbid'.
   - Match the shape of the existing predeploy entry, which is 'python /code/manage.py migrate --noinput'.

Non-goals:
- Do NOT change calculate_link_ratio's maths. It already scores a body of pure URLs at exactly 1.0, which is the case we want to catch.
- Do NOT add schemeless-link matching, per-line link ratios, or any new spam heuristic. These were considered and deliberately rejected; the owner would rather miss spam than delete a genuine paste.
- Do NOT add a --reprocess flag or otherwise change how spam_processed works.
- Do NOT touch the regex or spam-terms paths.
- Do NOT touch main/views.py; the noindex work is already done and committed separately.

Caveats:
- Dokku tokenizes the cron command and execs it directly. Shell operators are not interpreted and a bare one fails validation at deploy time, so keep the command free of pipes, redirects and semicolons.
- A single very long URL, over --min-length characters on its own, would still be deleted. Accepted; it is rare and the alternative is a link-count metric that is not worth the extra code.

## Acceptance Criteria

remove_spam has a --min-length option defaulting to 500, uses is not None for the ratio, and iterates with .iterator(). Tests cover the ratio calculation and the delete/keep decisions. misc/dokku/app.json has a valid cron entry running the command daily. Suite green.

