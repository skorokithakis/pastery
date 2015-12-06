from django.conf.urls import url

from main import views


urlpatterns = [
    url(r'^$', views.home, name="home"),
    url(r'^(?P<paste_id>[a-z]{3,})/raw/$', views.raw_paste, name="raw-paste"),
    url(r'^(?P<paste_id>[a-z]{3,})/$', views.paste, name="paste"),
]
