from django.conf.urls import url

from api import views  # noqa


urlpatterns = [
    url(r'^paste/$', views.PasteView.as_view(), name="paste"),
    url(r'^paste/(?P<paste_id>[^/]+)/$', views.PasteView.as_view(), name="paste-id"),
]
