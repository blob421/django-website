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
    redirect_url = models.CharField(max_length=255, default='dashboard:home', 
                                    help_text="* Path to dashboard, do not change")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                help_text='* You can add a new user with the plus sign ')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    recipients = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         blank = True, related_name='many_relation', default='----' )
    team = models.ForeignKey('Team', on_delete=models.CASCADE, null=True)

    class Meta:

        verbose_name_plural = "Add a user" 

       

    def __str__(self):
        return self.user.username
    


### FORMS ###
class Messages(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sender', 
                                                       on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL,
               related_name='receiver', 
               on_delete=models.PROTECT,
               null=True, blank=True, default='')
    
    title = models.CharField(max_length=60)
    content = models.TextField(null=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey('Task', on_delete=models.CASCADE, null=True, blank=True)
    
    picture = models.BinaryField(null=True, blank=True, editable=True)
    content_type = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.title


class Task(models.Model):
       
       users = models.ManyToManyField(UserProfile, related_name='task_users')
       description = models.TextField()
       name = models.CharField(max_length=50)
       creation_date = models.DateField(auto_now_add=True)
       due_date = models.DateTimeField()
       completed = models.BooleanField(default=False)
       urgent = models.BooleanField(default=False)

       picture = models.BinaryField(null=True, blank=True, editable=True)
       content_type = models.CharField(max_length=50, null=True, blank=True)
       completion_note = models.TextField(null=True)
       submitted_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
       
       denied = models.BooleanField(default=False)
       deny_reason = models.TextField(null=True, blank=True)
       
       def __str__(self):
           return self.name
       

class CompletedTasks(models.Model):
    approved_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='aproved_by', 
                                   null=True)
    submitted_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null = True)
    users = models.ManyToManyField(UserProfile, related_name='task_completed_users')
    description = models.TextField()
    name = models.CharField(max_length=50)
    completed = models.BooleanField(default=True)
    urgent = models.BooleanField(default=False)
    due_date = models.DateTimeField()
    creation_date = models.DateField()
    content_type = models.CharField(max_length=50, null=True, blank=True)
    
    picture = models.BinaryField(null=True, blank=True, editable=True)
    completion_note = models.TextField(null=True)
 


class Team(models.Model):
    team_lead =models.ForeignKey(UserProfile, on_delete=models.CASCADE, 
                                 related_name='team_lead', null=True)
    pinned_msg = models.TextField(null=True , default='---')
    name = models.CharField(max_length=40, blank=True )
    description = models.TextField(null=True)
    def __str__(self):
        return self.name


class ChatMessages(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


