---
id: S1-nzsrw
status: closed
deps: []
links: []
created: 2026-08-09T18:21:05Z
type: bug
priority: 1
assignee: Stavros Korokithakis
external-ref: STA-108
---
# Make Paste.raw_language migration state environment-independent

Objective: stop the migration state of main.Paste depending on which packages happen to be installed.

Background: models.get_languages() calls pygments.lexers.get_all_lexers(), which returns built-in lexers PLUS any lexer registered by another installed package through the 'pygments.lexers' entry point. IPython (a dev dependency) registers three: ipython2, ipython3, ipythonconsole. So Paste.raw_language.choices has 513 entries with dev deps installed and 510 without. Migration 0027 baked in the 513-entry version. In a dev/CI env (poetry install with dev deps) makemigrations reports no changes; in a production-style env (Dockerfile runs poetry install --only main) it wants to write a new ~510-line migration. Pygments upgrades cause the same churn. This is why 8 of the 30 migrations are 480-600 line files that emit no SQL: choices never affects the database schema for a CharField.

Fix: remove 'choices=LANGUAGES' from Paste.raw_language in main/models.py, and declare the choices in the two forms that need them instead.

Scope:
- main/models.py: remove choices= from Paste.raw_language only. Keep verbose_name, max_length, default.
- main/views.py, pasteform_factory(): declare 'raw_language = forms.ChoiceField(choices=LANGUAGES, label=_("Language"))' on PasteForm. The home page template reads form.raw_language.label, so the label must stay 'Language'. Existing initial/clone behaviour must keep working.
- main/admin.py: PasteAdmin declares no 'fields', so its change form currently renders raw_language as a dropdown. Add a small ModelForm with the same ChoiceField and set it as PasteAdmin.form so the dropdown is kept.
- Generate the resulting migration (0031). It must be a single AlterField on raw_language with no choices, and it must contain no other operations.

Non-goals:
- Do NOT touch User._style_name. Its STYLES list is hardcoded and static, and it already matches migration 0023 exactly.
- Do NOT squash, edit or delete any existing migration.
- Do NOT change api/views.py. The API validates language through ALIAS_DICT with a schema, not through model choices.
- Do NOT change get_languages(), get_aliases() or get_styles().
- Do NOT modify pyproject.toml or poetry.lock.

Caveats:
- A local Python 3.9 interpreter is required; the dependency set does not build on 3.11+. A working env already exists at the virtualenv created by: poetry env use /home/stavros/.local/share/uv/python/cpython-3.9-linux-x86_64-gnu/bin/python3.9 && poetry install --no-root
- After the change, 'poetry run ./manage.py makemigrations --check --dry-run' must report no changes, and it must report no changes whether or not dev dependencies are installed. That environment-independence is the point of the task.
- 'poetry run ./manage.py test' needs a collected static manifest first: 'poetry run ./manage.py collectstatic --noinput'.
- Leave the work uncommitted.

## Design

The ChoiceField declaration is duplicated between the paste form and the admin form. That is two lines; do not build a shared abstraction for it.

choices on a CharField is used only for form widget generation and full_clean() validation. It never appears in the column definition, so the generated AlterField produces no SQL on PostgreSQL and is safe to deploy in any order.

Django's ModelForm currently builds a TypedChoiceField from the model choices. An explicit forms.ChoiceField gives the same widget and the same 'select a valid choice' validation, so there is no behaviour change for either form.

## Acceptance Criteria

makemigrations reports no pending changes both with dev dependencies installed and with only main dependencies installed. The home page language dropdown and the admin paste language dropdown both still render as select elements with the full language list. The existing test suite passes.


## Notes

**2026-08-09T18:21:14Z**

ready for implementation
