from django.db import models
from django.contrib.auth.models import User


### USERS ###
class Role(models.Model):
    name = models.CharField(max_length=50)
    redirect_url = models.CharField(max_length=255, default='dashboard:home', help_text="* Path to dashboard, do not change")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT, 
                                help_text='* You can add a new user with the plus sign ') 

    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    receivers = models.ManyToManyField(User, blank = True, related_name='many_relation',
                                       help_text='Allowed contacts ; ')
    
 

    def __str__(self):
        return self.user.username

    

### FORMS ###
class Reports(models.Model):

    user = models.ForeignKey(User, related_name='sender', on_delete=models.PROTECT)
    recipient = models.ForeignKey(User,
               related_name='receiver', 
               on_delete=models.PROTECT,
               null=True, blank=True, default='')
    
    title = models.CharField(max_length=255, default='title')
    content = models.TextField(null=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


