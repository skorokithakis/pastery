---
id: S1-ixple
status: closed
deps: [S1-jlmlp, rep-dbelk, rep-yihyw]
links: []
created: 2026-08-09T17:55:42Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Delete dead dependencies and the code that goes with them

Objective: remove everything that is unused, permanently disabled, or obsolete. This is a deletion ticket. Nothing gets upgraded here.

Remove from pyproject.toml and the lock: hypothesis, fake-factory, django-qmethod, docutils, sqlparse, mixpanel, mixpanel-py-async, django-sendgrid-v5, django-debug-toolbar, django-cloudflare-push, django-recaptcha, django-extensions, werkzeug, brotlipy.

The first five are imported nowhere at all. The rest need code changes:

- debug_toolbar: drop from INSTALLED_APPS and MIDDLEWARE, and delete DEBUG_TOOLBAR_CONFIG and DEBUG_TOOLBAR_PATCH_SETTINGS. The toolbar is already permanently off, because SHOW_TOOLBAR_CALLBACK is a lambda returning 'False and (...)'. Deleting it also deletes the request.is_ajax() call, which is one of the Django 4.0 breakages.
- django_cloudflare_push.middleware.push_middleware: drop from MIDDLEWARE. HTTP/2 server push is gone from browsers and from Cloudflare.
- django-recaptcha: drop 'captcha' from INSTALLED_APPS, drop the ReCaptchaField import and the ENABLE_CAPTCHA branch in the form in main/views.py, drop the form.captcha block in main/templates/home.html, and delete ENABLE_CAPTCHA, RECAPTCHA_PUBLIC_KEY, RECAPTCHA_PRIVATE_KEY, RECAPTCHA_USE_SSL and NOCAPTCHA. ENABLE_CAPTCHA is already False.
- django-extensions: drop from INSTALLED_APPS. docker-compose.yml calls runserver_plus; change it to runserver. werkzeug exists only for runserver_plus, so it goes too.
- brotlipy: replace with the whitenoise brotli extra, so whitenoise keeps compressing.
- Mixpanel: utils.send_event and utils.identify_user are stubs that return immediately. Delete both, delete the 'identify' post_save receiver in main/models.py that calls identify_user, and delete the import and any call sites in main/views.py.
- CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY: check main/management/commands/remove_spam.py first. If that command uses its own token, delete both settings. If it reads them, keep them and say so.
- Delete local.yml. It is a dead Ansible playbook that installs from a requirements.txt which does not exist in this repo.

Non-goals: do not bump the version of anything that stays. Do not touch Django. Leave django-annoying, djangoql, django-bootstrap3, django-ipware, django-redis, django-tokenauth and django-webauthin alone.

Caveat: use Poetry 1.4.0 for lock operations.

## Acceptance Criteria

Suite green. collectstatic still works, with brotli compression intact. A grep for each removed package name finds nothing outside the lock history.


## Notes

**2026-08-09T18:47:12Z**

ready for implementation

**2026-08-10T07:18:18Z**

Lock operations: use 'poetry lock --no-update', not plain 'poetry lock'. Found while doing S1-sfqqx, and it is pre-existing, not caused by that ticket. Plain 'poetry lock' re-resolves with no locked preferences, then picks a yanked docutils 0.21.post1 for the '==0.*' constraint, fails to load it, drops into compatibility mode and grinds for ever on a sendgrid/cryptography conflict against the pinned werkzeug==0.11.*. Note that this ticket deletes both docutils and werkzeug, so it may cure itself, but start with --no-update anyway: it also keeps the lock diff minimal, which is what we want for a deletion ticket. This rule dies at S1-mkxad with Poetry.

**2026-08-10T18:59:43Z**

Add html5lib to the removal list. It is declared in pyproject.toml as a direct dependency and, since be765fc, nothing in the repo imports it. It was briefly the target of an import in main/models.py; that now goes through bleach.html5lib_shim instead.

Caution: bleach vendors its own copy at bleach._vendor.html5lib and the sanitizer depends on it. Remove the top-level html5lib distribution only. Do not act on a blanket grep for the string 'html5lib', and do not touch the import in main/models.py.

**2026-08-10T19:36:59Z**

Pre-implementation findings, all in scope:

1. send_event has a third call site the ticket does not mention: main/models.py line 441, in PasteManager.create. Delete it with the others.
2. utils/ holds only __init__.py, which holds only send_event and identify_user. rep-dbelk already deleted md_nofollow.py. So the whole utils package goes, not just the two functions.
3. MIXPANEL_TOKEN in settings.py is dead once mixpanel goes. Delete it.
4. README.md also tells the reader to run runserver_plus. Change it with docker-compose.yml.
5. Stale 'Hypothesis' comments in main/tests.py and api/test_shadowban.py, plus '.hypothesis/' in .gitignore. Clean them, or the grep acceptance criterion fails.
6. CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY: remove_spam.py DOES read both, in ban_ip. So keep them, per the ticket rule. Note that ban_ip is dead code, its first statement is 'return True', but that is a separate question and not this ticket's.

Environment caveat: the poetry on PATH is 2.4.1. CI pins 1.4.0. Poetry 2.x writes lock-version 2.1, which 1.4.0 cannot read, so locking with the default poetry would break CI. Lock with 1.4.0 specifically.

**2026-08-10T19:47:33Z**

Done. Two review passes found nothing in the change itself. Both only flagged a stale ARCHITECTURE.md, which was an untracked scratch artifact from my repo scan, never in git; deleted.

CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY kept, as required: ban_ip in remove_spam.py reads both. Worth knowing that ban_ip cannot run, its first statement is 'return True', so the settings are live only in the linter's eyes. Not this ticket's problem.

Verified: 66 tests pass, collectstatic emits 372 .br files with brotli 1.2.0, makemigrations --check clean, pre-commit clean, lock-version still 2.0, no surviving package moved version.
