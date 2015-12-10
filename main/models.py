import bleach
import hashlib
import markdown
import pygments
import shortuuid
import textile
from django.db import models
from django.db.models.signals import post_save
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from pygments import highlight
from pygments.lexers import guess_lexer, get_all_lexers
from pygments.formatters import HtmlFormatter

from utils import send_event, identify_user


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


def get_styles():
    """Return all available styles and their names."""

    styles = list(pygments.styles.STYLE_MAP.items())
    styles = styles + [
        ["solarized", "Solarized"],
        ["solarized_dark", "Solarized Dark"],
        ["solarized_dark256", "Solarized Dark 256"],
    ]
    styles = [[x[0], x[0].title().replace("Default", "Plain")] for x in styles]
    return sorted(styles, key=lambda x: x[1])

LANGUAGES = get_languages()
LANGUAGE_DICT = dict(LANGUAGES)
# Rename the default style to avoid confusion.
STYLES = get_styles()


def generate_api_key():
    """Create an API key for a user."""
    return shortuuid.ShortUUID().random(32)


def generate_paste_uuid():
    """Create a UUID for a paste."""
    return shortuuid.ShortUUID("abdcefghjkmnpqrstuvwxyz").random()[:6]


class User(AbstractUser):
    """A proxy for the User model, to add various methods."""
    api_key = models.CharField(
            verbose_name=_("API key"),
            max_length=64,
            help_text=_("Your API key."),
            default=generate_api_key,
            unique=True,
            )
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
        """Create a paste, retrying if there's an ID collision."""

        address = hashlib.sha256(kwargs["user_address"].encode("utf8")).hexdigest()[:16]
        user_id = address if address else kwargs["user"].username
        send_event(user_id, "new_paste", {"raw_language": kwargs["raw_language"]})

        # Try to create new IDs for the paste if one collides.
        tries = 10
        for x in range(tries):
            try:
                return super(PasteManager, self).create(*args, **kwargs)
            except IntegrityError:
                print("Collision %s." % x)
        raise IntegrityError("Could not find a paste ID after %s tries." % tries)


class ActivePasteManager(models.Manager):
    """A manager that ignores expired pastes."""
    def get_queryset(self):
        return super().get_queryset().exclude(expiration__lt=timezone.now())


class Paste(models.Model):
    id = models.CharField(
        max_length=100,
        primary_key=True,
        db_index=True,
        default=generate_paste_uuid,
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
    user_address = models.CharField(max_length=1000, blank=True)

    objects = PasteManager()
    active = ActivePasteManager()

    def __str__(self):
        return self.title if self.title else self.id

    def as_dict(self):
        """Represent the object as a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.get_full_url(),
            "language": self.language,
            "duration": int((self.expiration - timezone.now()).total_seconds() / 60) if self.expiration else None,
        }

    @classmethod
    def get_by_id_or_404(cls, paste_id):
        """Retrieve a paste by its ID, or None if it doesn't exist."""
        paste = cls.active.filter(pk=paste_id.lower()).first()

        if not paste:
            raise Http404
        else:
            return paste

    def get_full_url(self):
        return "https://%s%s" % (Site.objects.get_current().domain, self.get_absolute_url())

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
            rendered = markdown.markdown(bleach.clean(self.body), ["markdown.extensions.extra"])
        elif language == "textile":
            rendered = textile.textile(bleach.clean(self.body))
        else:
            formatter = HtmlFormatter(linenos="table", cssclass="paste")
            rendered = highlight(
                self.body, pygments.lexers.get_lexer_by_name(language),
                formatter
            )
        cache.set(key, rendered, settings.CACHING_TIME)
        return rendered


@receiver(post_save, sender=User)
def identify(sender, instance, created, **kwargs):
    """
    Identify a user to Mixpanel.
    """
    identify_user(instance.username, instance)


@receiver(post_save, sender=Paste)
def clear_cache(sender, instance, created, **kwargs):
    """
    Clear the cache when a paste is saved. Users can't really save
    pastes, but admins can, and it might be useful.
    """
    cache.delete_many([
        "pastery:paste_%s_language" % instance.id,
        "pastery:paste_%s_rendered_body" % instance.id,
    ])
