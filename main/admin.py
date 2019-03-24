from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from .models import Paste, Setting, User


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["key"]
    search_fields = ["key"]


@admin.register(Paste)
class PasteAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = ["id", "user", "title", "created", "expiration", "views", "max_views", "has_expired"]
    list_filter = ("created", "expiration")
    ordering = ["-created"]
    actions = ["purge_user"]

    def purge_user(self, request, queryset):
        for paste in queryset:
            user_counter = 0
            paste_counter = 0
            if paste.user:
                paste_counter += paste.user.paste_set.count()
                paste.user.delete()
                user_counter += 1
            else:
                paste.delete()
                paste_counter += 1
            self.message_user(request, "%s users and %s pastes deleted." % (user_counter, paste_counter))

    purge_user.short_description = "Delete selected pastes and their users"  # type: ignore


@admin.register(User)
class MyUserAdmin(DjangoQLSearchMixin, UserAdmin):
    fieldsets = (
        (_("Credentials"), {"fields": ("username", "email", "password")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Various"), {"fields": ("_style_name", "api_key")}),
    )
    list_display = ("username", "email", "is_staff")
