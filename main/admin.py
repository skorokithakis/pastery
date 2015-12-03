from django.contrib import admin
from .models import Paste


@admin.register(Paste)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "expiration"]
    search_fields = ["user", "title"]
