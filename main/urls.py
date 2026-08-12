from django.urls import re_path
from django.contrib.sitemaps.views import sitemap

from . import views

app_name = "main"
urlpatterns = [
    re_path(r"^$", views.home, name="home"),
    re_path(r"^account/$", views.account, name="account"),
    re_path(r"^account/reset-key/$", views.reset_key, name="reset-key"),
    re_path(r"^account/delete-account/$", views.delete_account, name="delete-account"),
    re_path(r"^login/$", views.login, name="login"),
    re_path(r"^oembed/$", views.oembed, name="oembed"),
    re_path(r"^(?P<paste_id>[^/]+)/delete/$", views.delete_paste, name="delete-paste"),
    re_path(r"^(?P<paste_id>[^/]+)/report/$", views.report_paste, name="report-paste"),
    re_path(r"^(?P<paste_id>[^/]+)/embed/$", views.embed_paste, name="embed-paste"),
    re_path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"static": views.StaticViewSitemap}},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    re_path(r"^(?P<paste_id>[^/]+)/raw/$", views.raw_paste, name="raw-paste"),
    re_path(r"^(?P<paste_id>[^/]+)/dl/$", views.download_paste, name="download-paste"),
    re_path(r"^(?P<paste_id>[^/]+)/$", views.paste, name="paste"),
]
