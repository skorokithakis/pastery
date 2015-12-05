from django.contrib import admin
from .models import Paste


@admin.register(Paste)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "created", "expiration", "has_expired"]
    search_fields = ["user", "title"]
    list_filter = ('created', "expiration")
