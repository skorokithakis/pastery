from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from .models import Paste
from .models import Setting
from .models import User


class ShadowbannedUserFilter(admin.SimpleListFilter):
    title = _("user shadowban status")
    parameter_name = "user_shadowbanned"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("From shadowbanned users")),
            ("no", _("From non-shadowbanned users")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(user__shadowbanned=True)
        if self.value() == "no":
            return queryset.filter(user__shadowbanned=False)
        return queryset


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
    list_filter = ("created", "expiration", ShadowbannedUserFilter)
    ordering = ["-created"]
    actions = ["shadowban_user", "shadowban_user_and_pastes", "purge_by_ip"]

    def shadowban_user(self, request, queryset):
        users = {paste.user for paste in queryset}
        total_pastes = 0

        for user in users:
            total_pastes += user.paste_set.count()
            if not user.shadowbanned:
                user.shadowbanned = True
                user.save()

        self.message_user(
            request,
            "%s users shadowbanned (%s total pastes)." % (len(users), total_pastes),
        )

    shadowban_user.short_description = "Shadowban users of selected pastes"  # type: ignore

    def shadowban_user_and_pastes(self, request, queryset):
        user_counter = 0
        paste_counter = 0

        # Collect unique users from selected pastes
        users = set()

        for paste in queryset:
            users.add(paste.user)

        # Process each unique user once
        for user in users:
            # Count pastes before deletion
            user_paste_count = user.paste_set.count()
            paste_counter += user_paste_count

            # Shadowban the user if not already shadowbanned
            if not user.shadowbanned:
                user.shadowbanned = True
                user.save()
                user_counter += 1

            # Delete all their pastes
            user.paste_set.all().delete()

        self.message_user(
            request,
            "%s users shadowbanned and %s pastes deleted."
            % (user_counter, paste_counter),
        )

    shadowban_user_and_pastes.short_description = (
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
