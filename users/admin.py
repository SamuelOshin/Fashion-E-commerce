from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from unfold.admin import ModelAdmin

# Unregister the default User and Group admin classes
admin.site.unregister(User)
admin.site.unregister(Group)

# Register the User model with the custom UserAdmin class
@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    pass

# Register the Group model with the custom GroupAdmin class
@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass