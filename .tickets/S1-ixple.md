---
id: S1-ixple
status: open
deps: [S1-jlmlp]
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

