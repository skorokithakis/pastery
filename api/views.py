import datetime
from collections import namedtuple

from annoying.decorators import ajax_request
from django.contrib.sites.shortcuts import get_current_site
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from schema import Schema, Use, Optional, And, SchemaError

from main.models import Paste


@require_POST
@csrf_exempt
@ajax_request
def paste(request):
    schema = Schema(
        And({
            Optional("title", "hi"): And([str], Use(lambda x: x[0])),
            Optional("language", "autodetect"): And([str], Use(lambda x: x[0])),
            Optional("expiration", 1440): And([str], Use(lambda x: x[0]), Use(int)),
            Optional(object): object,  # Ignore everything else.
            },
            # Make a named tuple out of the result.
            Use(lambda x: namedtuple('GenericDict', x.keys())(**x))
            )
    )

    try:
        data = schema.validate(dict(request.GET))
    except SchemaError as e:
        return {"result": "error", "error_msg": str(e)}

    paste = Paste.objects.create(
            title=data.title,
            language=data.language,
            body=request.body,
            expiration=timezone.now() + datetime.timedelta(minutes=data.expiration),
            )

    return {"url": "https://%s%s" % (get_current_site(request).domain, paste.get_absolute_url())}
