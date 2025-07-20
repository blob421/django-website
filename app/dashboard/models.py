from django.db import models
from django.contrib.auth.models import User




### USERS ###
class Role(models.Model):
    name = models.CharField(max_length=50)
    redirect_url = models.CharField(max_length=255) 
    def __str__(self):
        return self.name

# More like a blueprint with the elements I want to pick.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT) 
# Limits to one use per row and imports from User directly | one user is linked to one user
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    # References Role by role id
    receivers = models.ManyToManyField(User, blank = True, related_name='many_relation')
    # Can have many users in this field | many users are linked to many users
    # Many users that appear one time will have many users that appears multiple times
    def __str__(self):
        return self.user.username
    # So I can look up one user , and know what are the many users in receivers
    # One user /for one role / for multiple users
    

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


