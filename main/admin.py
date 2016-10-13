from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from .models import Paste, User


@admin.register(Paste)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "title", "created", "expiration", "views", "max_views", "has_expired"]
    search_fields = ["user__username", "title"]
    list_filter = ('created', "expiration")
    ordering = ["-created"]


@admin.register(User)
class MyUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        ('Various', {'fields': ('_style_name', "api_key")}),
    )
    list_display = ('username', 'email', 'is_staff')
    search_fields = ('username', 'email')
