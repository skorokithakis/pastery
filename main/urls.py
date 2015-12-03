from django.conf.urls import url
from django.contrib import admin

from main import views


urlpatterns = [
    url(r'^$', views.home, name="home"),
    url(r'^(?P<paste_id>[a-z]{5,})$', views.paste, name="paste"),
]
