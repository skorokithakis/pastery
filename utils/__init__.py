from mixpanel import Mixpanel
from mixpanel_async import AsyncBufferedConsumer
from django.conf import settings

if getattr(settings, "MIXPANEL_TOKEN", None):
    mp = Mixpanel(settings.MIXPANEL_TOKEN, consumer=AsyncBufferedConsumer())
else:
    mp = None


def send_event(user_id, name, data):
    """Send an event to Mixpanel."""
    if not mp:
        return

    mp.track(user_id, name, data)


def identify_user(user_id, user):
    if not mp:
        return

    mp.people_set(user_id, {
        "$email": user.email,
        "style": user._style_name
    })
