from django.conf.urls import url

from api import views


urlpatterns = [
    url(r'^paste/(|(?P<paste_id>[^/])+/)$', views.PasteView.as_view(), name="paste"),
]
