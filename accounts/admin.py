from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
@admin.register(User)
class FarmConnectUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("FarmConnect", {"fields":("role", "phone", "district")}),)
    list_display = ("username", "email", "role", "is_staff", "is_active")
