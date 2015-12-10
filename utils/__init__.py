from mixpanel import Mixpanel
from django.conf import settings


def send_event(user_id, name, data):
    """Send an event to Mixpanel."""
    if getattr(settings, "MIXPANEL_TOKEN", None) is None:
        return

    mp = Mixpanel(settings.MIXPANEL_TOKEN)
    mp.track(user_id, name, data)


def identify_user(user_id, user):
    mp = Mixpanel(settings.MIXPANEL_TOKEN)
    mp.people_set(user_id, {
        "$email": user.email,
        "style": user._style_name
    })
