---
id: S1-ocrfa
status: closed
deps: [S1-gfyky, rep-mcpwp]
links: []
created: 2026-08-09T17:56:35Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Upgrade Django 2.2 to 3.2 LTS

Objective: second rung of the LTS ladder.

Bump Django to the latest 3.2.x, and bump third-party packages as far as that requires. The likely ones are django-bootstrap3, djangoql, django-redis, django-ipware, django-tokenauth, django-webauthin and django-annoying.

Set DEFAULT_AUTO_FIELD to django.db.models.AutoField. Use AutoField, not BigAutoField: BigAutoField would generate AlterField migrations that rewrite the primary key column of every table on a live PostgreSQL database, for no benefit here.

Report the output of Django's system checks before and after, in particular the W042 auto-field warning.

Note that django-ipware moves several major versions here or at the next rung. The client-IP test from the safety-net ticket is the guard; if it fails, the rate limiter and the spam blocker are both keying on Cloudflare's address rather than the visitor's.

Non-goals: no code cleanup beyond what 3.2 requires.

Caveat: use Poetry 1.4.0 for lock operations. Must stay deployable to Dokku.

## Acceptance Criteria

Suite green on PostgreSQL 18. collectstatic works. makemigrations --check is clean. System checks report no W042.


## Notes

**2026-08-09T18:40:51Z**

Ordering change: uv replaces Poetry before this ticket runs. Ignore the 'use Poetry 1.4.0' caveat in the description; there is no poetry.lock by then. Use uv for all lock operations.

**2026-08-09T18:47:12Z**

ready for implementation

**2026-08-12T17:42:21Z**

Before you bump third-party packages here, read gnosis gtxgkc. The stale adjacent pins (django-bootstrap3 12.1.0, django-redis 4.11.0, whitenoise 5.0, djangoql 0.14.0, pytz 2020.1) do not move on their own, because plain 'uv lock' is preference-preserving. They move only if you raise their floor or run 'uv lock --upgrade'. Raise floors deliberately, package by package, rather than reaching for --upgrade; a fresh resolution moves about 30 packages at once and makes any failure unattributable. coverage is already dealt with by rep-mcpwp.

**2026-08-12T17:48:33Z**

Stale part of the description: django-ipware is no longer a dependency. It was dropped on the rendering-libraries rung (commit c91a150) because nothing imported it after the client-IP logic became project code (pastery/ratelimit.py, the Cloudflare trust chain, rep-dfzrh). The client-IP tests still stand guard and must stay green, but there is no ipware package to bump.

Also carried over from the 2.2 rung: deprecation warnings are hidden by default. Run the suite once with PYTHONWARNINGS=always::DeprecationWarning before reporting the list; 4.2 is the next stop and its removals are previewed here. The 2.2 rung emitted no RemovedInDjango warnings, so anything that appears now is new signal, not noise.

The webauthin AuthData naive-datetime RuntimeWarning predates this ladder. If the 3.2-forced webauthin bump happens to fix it, say so; do not fix it by hand.

**2026-08-12T18:10:01Z**

Done. Django 2.2.28 -> 3.2.25 (last 3.2 release). Lock moved django plus its new transitive dependency asgiref (marker split 3.11.1 below Python 3.10, 3.12.1 above) and nothing else. One source change: DEFAULT_AUTO_FIELD = AutoField in settings, with the comment explaining why never BigAutoField (four AlterField primary-key rewrites on the live database were confirmed to appear with BigAutoField, and W042 fires four times with the setting absent). No migrations generated. System check zero issues, no W042. 92 tests green on PostgreSQL 18.4 and SQLite, coverage 94%, collectstatic and pre-commit clean.

None of the six candidate packages needed a bump; all verified working on 3.2, not merely importable (gnosis vybccx). Client-IP tests 18/18 green. The webauthin naive-datetime RuntimeWarning survives, nothing forced the bump that would fix it.

Preview for the 4.2 rung, confirmed live by RemovedInDjango40Warning: tokenauth 0.5.1 (ugettext_lazy x3, conf.urls.url x3) and djangoql 0.14.0 (conf.urls.url x3). Exactly the two packages the S1-gxjol note predicts must move or be replaced there. Nothing else warned.
