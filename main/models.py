import datetime
import hashlib
from typing import Dict, List

import bleach
import markdown
import pygments
import shortuuid
import textile

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import F, Q
from django.db.models.signals import post_save
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.http import Http404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_all_lexers, get_lexer_by_name, guess_lexer

from utils import identify_user, send_event
from utils.md_nofollow import NofollowExtension


def clean(text: str) -> str:
    """Convenience method to bleach.clean()."""
    allowed_tags = ['a', 'abbr', 'acronym', 'address', 'area', 'b', 'bdo',
        'big', 'blockquote', 'br', 'button', 'caption', 'center', 'cite',
        'code', 'col', 'colgroup', 'dd', 'del', 'dfn', 'dir', 'div', 'dl', 'dt',
        'em', 'fieldset', 'font', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'hr', 'i', 'img', 'input', 'ins', 'kbd', 'label', 'legend', 'li', 'map',
        'menu', 'ol', 'optgroup', 'option', 'p', 'pre', 'q', 's', 'samp',
        'select', 'small', 'span', 'strike', 'strong', 'sub', 'sup', 'table',
        'tbody', 'td', 'textarea', 'tfoot', 'th', 'thead', 'u', 'tr', 'tt', 'u',
        'ul', 'var']
    allowed_attributes = {
        'a': ['href', 'title', 'rel', 'name', 'alt'],
        'abbr': ['title'],
        'acronym': ['title'],
        'img': ['src', 'title', 'alt', 'width', 'height'],
    }
    allowed_styles = ["font-weight", "text-align", "text-transform"]

    return bleach.clean(
            text,
            tags=allowed_tags,
            attributes=allowed_attributes,
            styles=allowed_styles
            )


def get_languages() -> List:
    """
    Return the list of all supported languages.

    Pygments' get_lexer_by_name is odd in that it doesn't accept a name at all,
    but rather an alias. This function generates the list of all lexers, along
    with their friendly names, by picking the first alias for each lexer and
    returning a list with it, after reordering the most frequent aliases to the
    top.
    """
    banned_lexers = ["md"]
    # Create a tuple of (first_alias, friendly_name) for each lexer.
    lexers = [[lexer[1][0], lexer[0]] for lexer in get_all_lexers() if lexer[1][0] not in banned_lexers]
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


def get_aliases() -> Dict[str, str]:
    """
    Return an alias dictionary.

    This function constructs a dictionary that maps all Pygments aliases to
    the lexer's first alias. This way, any language that comes in can be mapped
    to the alias that Pygments supports for that language.
    """
    alias_dict = {
            "markdown": "markdown",
            "textile": "textile"
            }
    for name, aliases, filetypes, mimetypes in get_all_lexers():
        for alias in aliases:
            alias_dict[alias] = aliases[0]
    return alias_dict


def get_styles() -> List:
    """Return all available highlighters and their names."""
    highlighters = [
        ['default', 'Plain'],
        ['algol', 'Algol'],
        ['algol_nu', 'Algol_Nu'],
        ['arduino', 'Arduino'],
        ['autumn', 'Autumn'],
        ['borland', 'Borland'],
        ['bw', 'Bw'],
        ['colorful', 'Colorful'],
        ['emacs', 'Emacs'],
        ['friendly', 'Friendly'],
        ['fruity', 'Fruity'],
        ['igor', 'Igor'],
        ['lovelace', 'Lovelace'],
        ['manni', 'Manni'],
        ['monokai', 'Monokai'],
        ['murphy', 'Murphy'],
        ['native', 'Native'],
        ['paraiso-dark', 'Paraiso-Dark'],
        ['paraiso-light', 'Paraiso-Light'],
        ['pastie', 'Pastie'],
        ['perldoc', 'Perldoc'],
        ['rrt', 'Rrt'],
        ['solarized', 'Solarized'],
        ['solarized_dark', 'Solarized_Dark'],
        ['solarized_dark256', 'Solarized_Dark256'],
        ['tango', 'Tango'],
        ['trac', 'Trac'],
        ['vim', 'Vim'],
        ['vs', 'Vs'],
        ['xcode', 'Xcode'],
    ]
    return highlighters


LANGUAGES = get_languages()
LANGUAGE_DICT = dict(LANGUAGES)
ALIAS_DICT = get_aliases()

# Rename the default style to avoid confusion.
STYLES = get_styles()


def generate_api_key() -> str:
    """Create an API key for a user."""
    return shortuuid.ShortUUID().random(32)


def generate_paste_uuid() -> str:
    """Create a UUID for a paste."""
    return shortuuid.ShortUUID("abdcefghjkmnpqrstuvwxyz").random()[:6]


class User(AbstractUser):
    """A proxy for the User model, to add various methods."""
    username = models.CharField(
        _('username'),
        max_length=150,
        default=generate_api_key,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = None  # type: None
    last_name = None  # type: None
    email = models.EmailField(_('email address'), unique=True)
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

    def get_full_name(self):
        return self.email
    get_short_name = get_full_name

    @property
    def style_name(self):
        return self._style_name if self._style_name else settings.DEFAULT_STYLE

    def reset_key(self):
        "Reset the user's API key."
        self.api_key = generate_api_key()
        self.save()


class PasteManager(models.Manager):
    def create(self, *args, **kwargs) -> "Paste":
        """Create a paste, retrying if there's an ID collision."""

        # Try to create new IDs for the paste if one collides.
        tries = 10
        for x in range(tries):
            try:
                paste = super(PasteManager, self).create(*args, **kwargs)
            except IntegrityError:
                continue
            else:
                break
        else:
            raise IntegrityError("Could not find a paste ID after %s tries." % tries)

        if not paste.user:
            # Anonymous users only get month-long pastes.
            max_expiration = timezone.now() + datetime.timedelta(minutes=30 * 24 * 60)
            paste.expiration = max_expiration if paste.expiration is None else min(paste.expiration, max_expiration)
            paste.save()

        if kwargs.get("user"):
            user_id = kwargs["user"].username
        else:
            user_id = hashlib.sha256(kwargs.get("user_address", "").encode("utf8")).hexdigest()[:16]

        send_event(user_id, "new_paste", {
            "raw_language": kwargs["raw_language"],
            "id": paste.id,
            "url": paste.get_full_url(),
            })

        return paste


class ActivePasteManager(models.Manager):
    """A manager that ignores expired pastes."""
    def get_queryset(self):
        qs = super().get_queryset()
        # Exclude pastes that are over time or over views.
        qs = qs.exclude(Q(expiration__lt=timezone.now()) | (Q(max_views__gt=0) & Q(views__gte=F("max_views"))))
        return qs


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
    views = models.IntegerField(default=0, blank=False)
    max_views = models.IntegerField(default=0, blank=False)

    objects = PasteManager()
    active = ActivePasteManager()

    def __str__(self) -> str:
        return self.title if self.title else self.id

    def as_dict(self, include_body: bool=False) -> Dict:
        """Represent the object as a dictionary."""
        r = {
            "id": self.id,
            "title": self.title,
            "url": self.get_full_url(),
            "language": self.language,
            "duration": int((self.expiration - timezone.now()).total_seconds() / 60) if self.expiration else None,
        }

        if include_body:
            r["body"] = self.body

        return r

    @classmethod
    def get_by_id_or_404(cls, paste_id) -> "Paste":
        """Retrieve a paste by its ID, or None if it doesn't exist."""
        paste = cls.active.filter(pk=paste_id.lower()).first()

        if not paste:
            raise Http404
        else:
            return paste

    def get_full_url(self) -> str:
        return "https://%s%s" % (Site.objects.get_current().domain, self.get_absolute_url())

    def get_absolute_url(self) -> str:
        return reverse("main:paste", args=[self.id])

    def has_expired(self) -> bool:
        return ((self.expiration and
                 self.expiration < timezone.now()) or
                (self.max_views and self.views >= self.max_views))
    has_expired.boolean = True  # type: ignore

    def get_language_display(self) -> bool:
        """Return the human-readable language name."""
        return LANGUAGE_DICT[self.language]

    def increment_views(self):
        """Increment the view counter."""
        self.views += 1
        self._skip_invalidation = True
        self.save()

    @property
    def filename(self) -> str:
        """
        Something that looks like a filename this paste
        can be represented by.
        """
        key = "pastery:language_%s_extension" % self.language
        glob = cache.get(key, None)
        if not glob:
            if self.language == "markdown":
                glob = "*.md"
            elif self.language == "textile":
                glob = "*.txl"
            else:
                lexer = get_lexer_by_name(self.language)
                if lexer.filenames and "*" in lexer.filenames[0]:
                    glob = lexer.filenames[0]
                else:
                    glob = "*"
            cache.set(key, glob, settings.CACHING_TIME)
        return glob.replace("*", self.id)

    @property
    def language(self) -> str:
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
    def rendered_body(self) -> str:
        key = "pastery:paste_%s_rendered_body" % self.id
        value = cache.get(key, None)
        if value:
            return value

        language = self.language
        if language == "markdown":
            rendered = clean(markdown.markdown(self.body, ["markdown.extensions.extra", NofollowExtension()]))
        elif language == "textile":
            rendered = clean(textile.textile_restricted(self.body))
        else:
            formatter = HtmlFormatter(linenos="table", linespans="line", anchorlinenos=True, lineanchors="l", cssclass="paste")
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
    identify_user(instance)


@receiver(post_save, sender=Paste)
def clear_cache(sender, instance, created, **kwargs):
    """
    Clear the cache when a paste is saved. Users can't really save
    pastes, but admins can, and it might be useful.
    """
    if getattr(instance, "_skip_invalidation", False):
        # Reset attribute, just in case.
        instance._skip_invalidation = False
        return
    cache.delete_many([
        "pastery:paste_%s_language" % instance.id,
        "pastery:paste_%s_rendered_body" % instance.id,
    ])
