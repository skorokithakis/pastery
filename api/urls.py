from django.conf.urls import url

from api import views


urlpatterns = [
    url(r'^paste/$', views.paste, name="paste"),
]
