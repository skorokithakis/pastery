from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Paste, User


@admin.register(Paste)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "created", "expiration", "views", "max_views", "has_expired"]
    search_fields = ["user__username", "title"]
    list_filter = ('created', "expiration")
    ordering = ["-created"]


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Various', {'fields': ('_style_name', "api_key")}),
    )
