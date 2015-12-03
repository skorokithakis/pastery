import shortuuid
import pygments
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from pygments import highlight
from pygments.lexers import guess_lexer, get_all_lexers
from pygments.formatters import HtmlFormatter


def paste_uuid():
    return shortuuid.ShortUUID("abdcefghjkmnpqrstuvwxyz").random()[:6]


class Paste(models.Model):
    LEXERS = sorted([[lexer[1][0], lexer[0]] for lexer in get_all_lexers()], key=lambda x: x[0].lower())

    id = models.CharField(max_length=100, primary_key=True, db_index=True, default=paste_uuid, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    title = models.CharField(max_length=500, blank=True)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    expiration = models.DateTimeField()
    language = models.CharField(max_length=100, choices=LEXERS, blank=True)

    def __str__(self):
        return self.title if self.title else self.id

    def get_absolute_url(self):
        return reverse("paste", args=[self.id])

    @property
    def style(self):
        return self.formatter.get_style_defs()

    @property
    def formatter(self):
        return HtmlFormatter(style="monokai", linenos="table", cssclass="paste")

    @property
    def lexer(self):
        if self.language:
            lexer = pygments.lexers.get_lexer_by_name(self.language)
        else:
            try:
                lexer = guess_lexer(self.body)
            except pygments.util.ClassNotFound:
                lexer = pygments.lexers.get_lexer_by_name("Text")
        return lexer

    @property
    def rendered_body(self):
        return highlight(self.body, self.lexer, self.formatter)
