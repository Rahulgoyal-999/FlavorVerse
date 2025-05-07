from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import RegisterUser


class RegisterUserAdmin(UserAdmin):
    model = RegisterUser
    list_display = ('email', 'name', 'is_staff', 'is_superuser', 'gender', 'address', 'phone')
    ordering = ('email',)


    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone', 'address', 'gender')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),


    )


    # Fields visible when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'phone', 'address', 'gender', 'password1', 'password2'),
        }),
    )


admin.site.register(RegisterUser, RegisterUserAdmin)