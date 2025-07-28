from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from .models import Paste
from .models import Setting
from .models import User


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["key"]
    search_fields = ["key"]


@admin.register(Paste)
class PasteAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "title",
        "created",
        "expiration",
        "user_address",
        "views",
        "max_views",
        "has_expired",
    ]
    list_filter = ("created", "expiration")
    ordering = ["-created"]
    actions = ["purge_user", "purge_user_and_pastes", "purge_by_ip"]

    def purge_user(self, request, queryset):
        user_counter = 0

        for paste in queryset:
            if paste.user:
                # Shadowban the user instead of deleting
                if not paste.user.shadowbanned:
                    paste.user.shadowbanned = True
                    paste.user.save()
                    user_counter += 1

        self.message_user(
            request,
            "%s users shadowbanned." % user_counter,
        )

    purge_user.short_description = "Shadowban users of selected pastes"  # type: ignore

    def purge_user_and_pastes(self, request, queryset):
        user_counter = 0
        paste_counter = 0

        # Collect unique users from selected pastes
        users = set()

        for paste in queryset:
            users.add(paste.user)

        # Process each unique user once
        for user in users:
            # Shadowban the user if not already shadowbanned
            if not user.shadowbanned:
                user.shadowbanned = True
                user.save()
                user_counter += 1

            # Delete all their pastes
            paste_counter += user.paste_set.count()
            user.paste_set.all().delete()

        self.message_user(
            request,
            "%s users shadowbanned and %s pastes deleted."
            % (user_counter, paste_counter),
        )

    purge_user_and_pastes.short_description = (
        "Shadowban users and delete all their pastes"  # type: ignore
    )

    def purge_by_ip(self, request, queryset):
        ips = set()
        for paste in queryset:
            ips.add(paste.user_address)

        paste_counter = 0
        for ip in ips:
            for paste in Paste.objects.filter(user_address=ip):
                paste.delete()
                paste_counter += 1

        self.message_user(
            request, "Deleted %s pastes from %s IPs.." % (paste_counter, len(ips))
        )

    purge_by_ip.short_description = "Delete all pastes from the selected pastes' IPs"  # type: ignore


@admin.register(User)
class MyUserAdmin(DjangoQLSearchMixin, UserAdmin):
    fieldsets = (
        (_("Credentials"), {"fields": ("username", "email", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Various"), {"fields": ("_style_name", "api_key", "shadowbanned")}),
    )
    list_display = ("username", "email", "is_staff", "shadowbanned")
    list_filter = ("is_staff", "is_superuser", "is_active", "shadowbanned")
