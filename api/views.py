import datetime
import json
from collections import namedtuple

from annoying.decorators import ajax_request
from brake.decorators import ratelimit
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from schema import Schema, Use, Optional, And, SchemaError

from main.models import Paste, LANGUAGE_DICT

User = get_user_model()


@require_POST
@ratelimit(rate="1000/d")
@ratelimit(rate="500/h")
@ratelimit(rate="20/m")
@csrf_exempt
@ajax_request
def paste(request):
    if getattr(request, 'limited', False):
        response = {"result": "error", "error_msg": "You're pasting too much, please slow down."}
        return HttpResponse(json.dumps(response), content_type="application/json", status=429)

    schema = Schema(
        And({
            Optional("title", default=""): And([str], Use(lambda x: x[0]), lambda x: len(x) < 200, error="\"title\" should be a string less than 200 characters long."),
            Optional("language", default="autodetect"): And([str], Use(lambda x: x[0]), Use(lambda x: x if x in LANGUAGE_DICT.keys() else "autodetect"), error="\"language\" should be the name of a supported language."),
            Optional("duration", default=1440): And([str], Use(lambda x: x[0]), Use(int), Use(lambda x: x > 0), error="\"duration\" should be an integer number of minutes before the paste is deleted."),
            Optional("api_key", default=None): Use(lambda x: User.objects.get(api_key=x[0]), error="\"api_key\" must be a valid API key."),
            },
            # Make a named tuple out of the result.
            Use(lambda x: namedtuple('GenericDict', x.keys())(**x))
            )
    )

    try:
        data = schema.validate(dict(request.GET))
    except SchemaError as e:
        response = {"result": "error", "error_msg": str(e)}
        return HttpResponse(json.dumps(response), content_type="application/json", status=422)

    try:
        body = request.body.decode("utf8")
    except UnicodeDecodeError:
        response = {"result": "error", "error_msg": "Your request body was not valid UTF-8."}
        return HttpResponse(json.dumps(response), content_type="application/json", status=422)

    paste = Paste.objects.create(
            title=data.title,
            raw_language=data.language,
            body=body,
            user=data.api_key,
            expiration=timezone.now() + datetime.timedelta(minutes=data.duration),
            )

    return {
        "url": "https://%s%s" % (get_current_site(request).domain, paste.get_absolute_url()),
        "language": paste.language,
        "title": paste.title,
        "duration": data.duration,
    }
