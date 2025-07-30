from django.contrib import admin
from . import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin

admin.site.register(models.ChatMessages)
admin.site.register(models.Chart)
user_model = get_user_model()
admin.site.register(models.ChartSection)
admin.site.register(models.Task)

admin.site.register(models.Team)

    
class UserProfileInline(admin.StackedInline):  
    model = models.UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Details'
    verbose_name = 'User profile'
    fields = ['role', 'team']

@admin.register(models.Role)
class RoleeAdmin(admin.ModelAdmin):
    search_fields = ['name']  
    list_display = ['name']
    



@admin.register(user_model)
class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    add_form_template = "admin/add_form.html"
    fieldsets = (
        ('Basic Info', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'street_address', 'phone','password', 'is_staff'),
        }),
     
        ('Login Data', {
            'fields': ('last_login', 'date_joined', 'groups'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
               
                'username',
                'email',
                'first_name',
                'last_name',
                'street_address',
                'phone',
                'password1',
                'password2',
                'is_staff',
                'notes',
            ),
        }),
    )

    list_display = ('email', 'first_name', 'last_name','username', 'is_staff')

 
    search_fields = ('username', 'email', 'first_name', 'last_name')
