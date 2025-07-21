from django.contrib import admin
from . import models
# Register your models here.


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ['user__username', 'role__name']  
    list_display = ['user', 'role'] 


@admin.register(models.Role)
class RoleeAdmin(admin.ModelAdmin):
    search_fields = ['name']  
    list_display = ['name'] 