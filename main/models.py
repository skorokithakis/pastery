import shortuuid
import pygments
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from pygments import highlight
from pygments.lexers import guess_lexer, get_all_lexers
from pygments.formatters import HtmlFormatter


def get_languages():
    """Return the list of all supported languages."""
    lexers = [[lexer[1][0], lexer[0]] for lexer in get_all_lexers()]
    lexers += [
            ["markdown", "Markdown"],
            ["textile", "Textile"],
            ["restructuredtext", "reStructuredText"],
        ]
    sorted_lexers = sorted(lexers, key=lambda x: x[0].lower())
    sorted_lexers = [
            ["autodetect", _("Autodetect")],
        ] + sorted_lexers
    return sorted_lexers


def paste_uuid():
    """Create a UUID for a paste."""
    return shortuuid.ShortUUID("abdcefghjkmnpqrstuvwxyz").random()[:6]


class User(AbstractUser):
    """A proxy for the User model, to add various methods."""
    class Meta:
        db_table = "auth_user"

    def style_name(self):
        return "monokai"


class Paste(models.Model):
    id = models.CharField(
        max_length=100,
        primary_key=True,
        db_index=True,
        default=paste_uuid,
        editable=False
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    title = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    expiration = models.DateTimeField()
    language = models.CharField(
        max_length=100,
        choices=get_languages(),
        default="autodetect",
    )

    def __str__(self):
        return self.title if self.title else self.id

    def get_absolute_url(self):
        return reverse("paste", args=[self.id])

    def has_expired(self):
        return self.expiration < timezone.now()
    has_expired.boolean = True

    @property
    def style(self):
        return self.formatter.get_style_defs(".pastetable")

    @property
    def formatter(self):
        return HtmlFormatter(style="monokai", linenos="table", cssclass="paste")

    @property
    def lexer_language(self):
        if self.language == "autodetect":
            try:
                language = guess_lexer(self.body).name
            except pygments.util.ClassNotFound:
                language = "text"
        else:
            language = self.language
        return language

    @property
    def rendered_body(self):
        return highlight(self.body, pygments.lexers.get_lexer_by_name(self.lexer_language), self.formatter)
