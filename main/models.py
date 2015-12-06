import markdown
import pygments
import shortuuid
import textile
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
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


def paste_uuid():
    """Create a UUID for a paste."""
    return shortuuid.ShortUUID("abdcefghjkmnpqrstuvwxyz").random()[:6]


class User(AbstractUser):
    """A proxy for the User model, to add various methods."""
    _style_name = models.CharField(
            choices=[["", _("Default")]] + list([x[0], x[0].title()] for x in pygments.styles.STYLE_MAP.items()),
            max_length=50,
            blank=True
            )

    class Meta:
        db_table = "auth_user"

    @property
    def style_name(self):
        return self._style_name if self._style_name else "monokai"


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
    expiration = models.DateTimeField()
    raw_language = models.CharField(
        verbose_name=_("Language"),
        max_length=100,
        choices=LANGUAGES,
        default="autodetect"
    )

    def __str__(self):
        return self.title if self.title else self.id

    @classmethod
    def get_by_id_or_404(cls, paste_id):
        """Retrieve a paste by its ID, or None if it doesn't exist."""
        paste = cls.objects.filter(pk=paste_id).first()

        if not paste or paste.has_expired():
            raise Http404
        else:
            return paste

    def get_absolute_url(self):
        return reverse("paste", args=[self.id])

    def has_expired(self):
        return self.expiration < timezone.now()
    has_expired.boolean = True

    @property
    def language(self):
        """
        The final language of the lexer. This is either the user-specified
        language, or a guessed language, if the former was not specified.
        """
        if self.raw_language == "autodetect":
            try:
                language = guess_lexer(self.body).aliases[0]
            except pygments.util.ClassNotFound:
                language = "text"
        else:
            language = self.raw_language
        return language

    @property
    def rendered_body(self):
        language = self.language
        if language == "markdown":
            return markdown.markdown(self.body, ["markdown.extensions.extra"])
        elif language == "textile":
            return textile.textile(self.body)
        else:
            formatter = HtmlFormatter(linenos="table", cssclass="paste")
            return highlight(
                self.body, pygments.lexers.get_lexer_by_name(language),
                formatter
            )
