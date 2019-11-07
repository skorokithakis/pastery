import datetime
import json
from collections import namedtuple

from brake.decorators import ratelimit
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from ipware.ip import get_ip
from schema import And
from schema import Optional
from schema import Schema
from schema import SchemaError
from schema import Use

from main.models import ALIAS_DICT
from main.models import Paste

User = get_user_model()


class PasteView(View):
    @method_decorator(ratelimit(rate="1000/d", method=["POST"]))
    @method_decorator(ratelimit(rate="500/h", method=["POST"]))
    @method_decorator(ratelimit(rate="20/m", method=["POST"]))
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        data = super().dispatch(*args, **kwargs)

        if isinstance(data, HttpResponse):
            return data

        status_code = 200  # type: ignore

        if data.get("result") == "error":
            status_code = 422

        if "status_code" in data:
            status_code = data["status_code"]
            del data["status_code"]

        data_str = json.dumps(data)
        response = HttpResponse(
            data_str, content_type="application/json", status=status_code
        )
        response["content-length"] = len(data_str)
        return response

    def get(self, request, paste_id=None):
        schema = Schema(
            {
                "api_key": Use(
                    lambda x: User.objects.get(api_key=x[0]),
                    error='"api_key" must be a valid API key.',
                )
            }
        )

        try:
            data = schema.validate(dict(request.GET))
        except SchemaError as e:
            return {"result": "error", "error_msg": str(e)}

        if paste_id:
            qs = Paste.active.filter(pk=paste_id)
        else:
            qs = Paste.active.filter(user=data["api_key"]).order_by("-created")

        for paste in qs:
            paste.increment_views()

        return {
            "pastes": [paste.as_dict(include_body=paste_id is not None) for paste in qs]
        }

    def post(self, request, paste_id=None):
        if getattr(request, "limited", False):
            return {
                "result": "error",
                "error_msg": "You're pasting too much, please slow down.",
                "status_code": 429,
            }

        schema = Schema(
            And(
                {
                    Optional("title", default=""): And(
                        [str],
                        Use(lambda x: x[0]),
                        lambda x: len(x) < 200,
                        error='"title" should be a string less than 200 characters long.',
                    ),
                    Optional("language", default="autodetect"): And(
                        [str],
                        Use(lambda x: x[0]),
                        Use(lambda x: ALIAS_DICT.get(x, "autodetect")),
                        error='"language" should be the name of a supported language.',
                    ),
                    Optional("duration", default=30 * 24 * 60): And(
                        [str],
                        Use(lambda x: int(x[0])),
                        lambda x: 0 < x <= 50 * 365 * 24 * 60,
                        error='"duration" should be a positive integer number of minutes before the paste is deleted.',
                    ),
                    Optional("api_key", default=None): Use(
                        lambda x: User.objects.get(api_key=x[0]),
                        error='"api_key" must be a valid API key.',
                    ),
                    Optional("max_views", default=0): And(
                        [str],
                        Use(lambda x: int(x[0])),
                        lambda x: x >= 0,
                        error='"max_views" should be a non-negative integer number of views before the paste is deleted.',
                    ),
                },
                # Make a named tuple out of the result.
                Use(lambda x: namedtuple("GenericDict", x.keys())(**x)),
            )
        )

        try:
            data = schema.validate(dict(request.GET))
        except SchemaError as e:
            return {"result": "error", "error_msg": str(e)}

        if request.FILES:
            # Get the first file in a form-data form.
            filename = list(request.FILES.keys())[0]
            body = request.FILES[filename].read()
        else:
            body = request.body

        try:
            body = body.decode("utf8")
        except UnicodeDecodeError:
            return {
                "result": "error",
                "error_msg": "Your request body was not valid UTF-8.",
            }

        paste = Paste.objects.create(
            title=data.title,
            raw_language=data.language,
            body=body,
            user=data.api_key,
            max_views=data.max_views,
            expiration=timezone.now() + datetime.timedelta(minutes=data.duration),
            user_address=get_ip(request) or "",
        )

        return paste.as_dict()

    def delete(self, request, paste_id=None):
        schema = Schema(
            {
                "api_key": Use(
                    lambda x: User.objects.get(api_key=x[0]),
                    error='"api_key" must be a valid API key.',
                )
            }
        )

        try:
            data = schema.validate(dict(request.GET))
        except SchemaError as e:
            return {"result": "error", "error_msg": str(e)}

        paste = Paste.objects.filter(user=data["api_key"], pk=paste_id).first()
        if paste:
            paste.delete()
            return {"result": "success"}
        else:
            return {
                "result": "error",
                "error_msg": "That paste does not belong to you.",
            }
