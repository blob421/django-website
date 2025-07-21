from django.db import models

from django.conf import settings
from django.contrib.auth.models import AbstractUser
### USERS ###

class Users(AbstractUser):
    street_address = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=12, blank=True)
    assigned_on = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.username   
    
    
class Role(models.Model):
    name = models.CharField(max_length=50)
    redirect_url = models.CharField(max_length=255, default='dashboard:home', help_text="* Path to dashboard, do not change")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                help_text='* You can add a new user with the plus sign ')
    class Meta:
       
        verbose_name_plural = "Add a user" 

    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         blank = True, related_name='many_relation' )
    
 

    def __str__(self):
        return self.user.username

    

### FORMS ###
class Reports(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sender', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL,
               related_name='receiver', 
               on_delete=models.PROTECT,
               null=True, blank=True, default='')
    
    title = models.CharField(max_length=255, default='title')
    content = models.TextField(null=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


