import markdown
import pygments
import shortuuid
import textile
from django.db import models
from django.db.utils import IntegrityError
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from pygments import highlight
from pygments.lexers import guess_lexer, get_all_lexers
from pygments.formatters import HtmlFormatter


def get_languages():
    """Return the list of all supported languages."""
    lexers = [[lexer[1][0], lexer[0]] for lexer in get_all_lexers()]
    lexers += [["markdown", "Markdown"], ["textile", "Textile"], ]
    sorted_lexers = sorted(lexers, key=lambda x: x[0].lower())

    top = [
        "bash", "c", "csharp", "cpp", "css", "html", "java", "js", "json",
        "markdown", "lua", "text", "objective-c", "perl", "php", "python",
        "ruby", "swift"
    ]

    top_languages = [["autodetect", _("Autodetect")]]
    bottom_languages = [["autodetect", "--------"]]
    for language in sorted_lexers:
        if language[0] in top:
            top_languages.append(language)
        else:
            bottom_languages.append(language)

    return top_languages + bottom_languages


LANGUAGES = get_languages()
LANGUAGE_DICT = dict(LANGUAGES)
# Rename the default style to avoid confusion.
STYLES = sorted([[x[0], x[0].title().replace("Default", "Plain")] for x in pygments.styles.STYLE_MAP.items()], key=lambda x: x[1])


def paste_uuid():
    """Create a UUID for a paste."""
    return shortuuid.ShortUUID("abdcefghjkmnpqrstuvwxyz").random()[:6]


class User(AbstractUser):
    """A proxy for the User model, to add various methods."""
    _style_name = models.CharField(
            verbose_name=_("Style name"),
            choices=[["", _("Default")]] + STYLES,
            max_length=50,
            blank=True,
            help_text=_("Pick the color style you prefer for all pastes on the site."),
            )

    class Meta:
        db_table = "auth_user"

    @property
    def style_name(self):
        return self._style_name if self._style_name else settings.DEFAULT_STYLE


class PasteManager(models.Manager):
    def create(self, *args, **kwargs):
        # Try to create new IDs for the paste if one collides.
        tries = 10
        for x in range(tries):
            try:
                return super(PasteManager, self).create(*args, **kwargs)
            except IntegrityError:
                print("Collision %s." % x)
        raise IntegrityError("Could not find a paste ID after %s tries." % tries)


class Paste(models.Model):
    id = models.CharField(
        max_length=100,
        primary_key=True,
        db_index=True,
        default=paste_uuid,
        editable=False
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    title = models.CharField(
        max_length=500,
        blank=True,
        help_text=_("The title of the paste.")
    )
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    expiration = models.DateTimeField(blank=True, null=True)
    raw_language = models.CharField(
        verbose_name=_("Language"),
        max_length=100,
        choices=LANGUAGES,
        default="autodetect"
    )

    objects = PasteManager()

    def __str__(self):
        return self.title if self.title else self.id

    @classmethod
    def get_by_id_or_404(cls, paste_id):
        """Retrieve a paste by its ID, or None if it doesn't exist."""
        paste = cls.objects.filter(pk=paste_id.lower()).first()

        if not paste or paste.has_expired():
            raise Http404
        else:
            return paste

    def get_absolute_url(self):
        return reverse("paste", args=[self.id])

    def has_expired(self):
        return self.expiration and self.expiration < timezone.now()
    has_expired.boolean = True

    def get_language_display(self):
        """Return the human-readable language name."""
        return LANGUAGE_DICT[self.language]

    @property
    def language(self):
        """
        The final language of the lexer. This is either the user-specified
        language, or a guessed language, if the former was not specified.
        """
        key = "pastery:paste_%s_language" % self.id
        value = cache.get(key, None)
        if value:
            return value

        if self.raw_language == "autodetect":
            try:
                language = guess_lexer(self.body).aliases[0]
            except pygments.util.ClassNotFound:
                language = "text"
        else:
            language = self.raw_language

        cache.set(key, language, settings.CACHING_TIME)
        return language

    @property
    def rendered_body(self):
        key = "pastery:paste_%s_rendered_body" % self.id
        value = cache.get(key, None)
        if value:
            return value

        language = self.language
        if language == "markdown":
            rendered = markdown.markdown(self.body, ["markdown.extensions.extra"])
        elif language == "textile":
            rendered = textile.textile(self.body)
        else:
            formatter = HtmlFormatter(linenos="table", cssclass="paste")
            rendered = highlight(
                self.body, pygments.lexers.get_lexer_by_name(language),
                formatter
            )
        cache.set(key, rendered, settings.CACHING_TIME)
        return rendered
