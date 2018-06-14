from api import views  # noqa
from django.conf.urls import url

app_name = "api"
urlpatterns = [
    url(r"^paste/$", views.PasteView.as_view(), name="paste"),
    url(r"^paste/(?P<paste_id>[^/]+)/$", views.PasteView.as_view(), name="paste-id"),
]
