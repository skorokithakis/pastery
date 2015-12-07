from django.conf.urls import url

from main import views


urlpatterns = [
    url(r'^$', views.home, name="home"),
    url(r'^account/$', views.account, name="account"),
    url(r'^logout/$', views.logout, name="logout"),
    url(r'^(?P<paste_id>[^/]{3,})/delete/$', views.delete_paste, name="delete-paste"),
    url(r'^(?P<paste_id>[^/]{3,})/raw/$', views.raw_paste, name="raw-paste"),
    url(r'^(?P<paste_id>[^/]{3,})/$', views.paste, name="paste"),
]
