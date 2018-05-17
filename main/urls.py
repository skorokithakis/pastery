from django.conf.urls import url

from .main import views

app_name = "main"
urlpatterns = [
    url(r'^$', views.home, name="home"),
    url(r'^account/$', views.account, name="account"),
    url(r'^account/reset-key/$', views.reset_key, name="reset-key"),
    url(r'^login/$', views.login, name="login"),
    url(r'^oembed/$', views.oembed, name="oembed"),
    url(r'^(?P<paste_id>[^/]+)/delete/$', views.delete_paste, name="delete-paste"),
    url(r'^(?P<paste_id>[^/]+)/report/$', views.report_paste, name="report-paste"),
    url(r'^(?P<paste_id>[^/]+)/embed/$', views.embed_paste, name="embed-paste"),
    url(r'^(?P<paste_id>[^/]+)/raw/$', views.raw_paste, name="raw-paste"),
    url(r'^(?P<paste_id>[^/]+)/dl/$', views.download_paste, name="download-paste"),
    url(r'^(?P<paste_id>[^/]+)/$', views.paste, name="paste"),
]
