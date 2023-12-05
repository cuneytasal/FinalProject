from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

class AccountAdmin(UserAdmin):
    list_display = ('email', 'cafe_name', 'date_joined', 'last_login', 'is_admin', 'is_staff')
    search_fields = ('email', 'cafe_name')
    readonly_fields = ('id', 'date_joined', 'last_login')
    # remove the ordering attribute
    ordering = ['email']
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
admin.site.register(Account, AccountAdmin)
