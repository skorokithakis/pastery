from django.urls import re_path

from api import views  # noqa

app_name = "api"
urlpatterns = [
    re_path(r"^paste/$", views.PasteView.as_view(), name="paste"),
    re_path(
        r"^paste/(?P<paste_id>[^/]+)/$", views.PasteView.as_view(), name="paste-id"
    ),
]
