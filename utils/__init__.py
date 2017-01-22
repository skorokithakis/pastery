from django.conf import settings
from mixpanel import Mixpanel
from mixpanel_async import AsyncBufferedConsumer

if getattr(settings, "MIXPANEL_TOKEN", None):
    mp = Mixpanel(settings.MIXPANEL_TOKEN, consumer=AsyncBufferedConsumer())
else:
    mp = None


def send_event(user_id, name, data):
    """Send an event to Mixpanel."""
    if not mp:
        return

    mp.track(user_id, name, data)


def identify_user(user):
    if not mp:
        return

    if isinstance(user.username, bytes):
        # It may sometimes occur that persona usernames are bytes before being
        # saved. We guard against that here.
        username = user.username.decode("utf8")
    else:
        username = user.username

    mp.people_set(username, {
        "$email": user.email,
        "style": user._style_name
    })
