from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Paste, User


@admin.register(Paste)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "created", "expiration", "has_expired"]
    search_fields = ["user", "title"]
    list_filter = ('created', "expiration")


@admin.register(User)
class UserAdmin(UserAdmin):
    pass
