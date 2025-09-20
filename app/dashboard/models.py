from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
import os
from django.contrib.humanize.templatetags.humanize import naturaltime



def object_directory_path(instance, filename):
    model_name = instance.content_type.model
    object_id = instance.object_id
    return f'{model_name}/{object_id}/{filename}'

### USERS ###

class Users(AbstractUser):
    street_address = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=12, blank=True)
    assigned_on = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    username = models.CharField(max_length=21, unique=True)

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

    availability = models.CharField(null=True, blank=True)
    weekends = models.BooleanField(default=False)
    stats = GenericRelation('Stats')
    picture = GenericRelation('Document')
    active_task = models.ForeignKey('Task', on_delete=models.CASCADE, null=True, blank=True)
    status = models.TextField(max_length=80, null=True, blank=True, default='No status yet')
    
    push_token = models.CharField(null=True, blank=True)

   
    class Meta:

        verbose_name_plural = "Add a user" 
      
        indexes = [
            models.Index(fields=['team']),
            models.Index(fields=['id']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return self.user.username
    
    def save(self, *args, **kwargs):
        if self.status == '':
            self.status = 'No status yet' 
        super().save(*args, **kwargs)
        

class Stats(models.Model):
  
    timestamp = models.DateTimeField(auto_now_add=True) 
  
    completed_tasks = models.PositiveIntegerField(default=0)
    late_tasks = models.PositiveIntegerField(default=0)

    denied_tasks= models.PositiveIntegerField(default=0)
    urgent_tasks_success = models.PositiveIntegerField(default=0)

    days_missed = models.PositiveIntegerField(default=0)
    days_scheduled = models.PositiveIntegerField(default=0)
    logged = models.PositiveIntegerField(default=0)
    
    submission = models.PositiveIntegerField(default=0)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    late = models.BooleanField(null=True, blank = True)
    report_not_done = models.PositiveIntegerField(default=0)

    stars = models.PositiveIntegerField(default=0, null=True,blank=True)
    star_note = models.TextField(null=True, blank=True)
    team = models.ForeignKey('Team', on_delete=models.CASCADE, null=True, blank=True)
        
    class Meta:
        indexes = [
            models.Index(fields=['object_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['stars']),
        ]
    

class Team(models.Model):
    team_lead =models.ForeignKey(UserProfile, on_delete=models.CASCADE, 
                                 related_name='team_lead', null=True)
    pinned_msg = models.TextField(null=True , default='---')
    name = models.CharField(max_length=40, blank=True )
    description = models.TextField(null=True, blank=True)
    stats = GenericRelation('Stats')

    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(fields=['team_lead']),
            models.Index(fields=['id']),
            models.Index(fields=['name']),
        ]



##### Objects #####

class Messages(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sender', 
                                                       on_delete=models.CASCADE)
    recipient = models.ManyToManyField(UserProfile,
               related_name='receiver', 
               null=True, blank=True, default='')
    
    title = models.CharField(max_length=60)
    content = models.TextField(null=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    new = models.BooleanField(default=True)
    
    task = models.ForeignKey('Task', on_delete=models.CASCADE, null=True, blank=True)
    forwarded = models.BooleanField(default=False)
    forwarded_by = models.ForeignKey(UserProfile, null=True, on_delete=models.CASCADE)
    
    documents = GenericRelation('Document')
   
    
    def __str__(self):
        return self.title
    
    class Meta:
        indexes = [
        
            models.Index(fields=['user']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['id']),
        ]


class MessagesCopy(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sender_copy', 
                                                    on_delete=models.CASCADE)
    recipient = models.ManyToManyField(UserProfile,
            related_name='receiver_copy', 
            null=True, blank=True, default='')
    
    title = models.CharField(max_length=60)
    content = models.TextField(null=False)
    timestamp = models.DateTimeField()
    task = models.ForeignKey('Task', on_delete=models.CASCADE, null=True, blank=True)
    forwarded = models.BooleanField(default=False)
    forwarded_by = models.ForeignKey(UserProfile, null=True, on_delete=models.CASCADE)
    documents =  GenericRelation('Document')

    def __str__(self):
        return self.title
    class Meta:
        indexes = [
        
            models.Index(fields=['user']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['id']),
        ]



class ChatMessages(models.Model):
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
            indexes = [
                
                models.Index(fields=['created_at']),
            ]



class Task(models.Model):
        
        users = models.ManyToManyField(UserProfile, related_name='task_users')
        description = models.TextField()
        name = models.CharField(max_length=36, unique=True)
        creation_date = models.DateTimeField(auto_now_add=True)
        starting_date = models.DateTimeField(null=True, blank=True)
        completion_time = models.FloatField(null=True, blank=True)

        due_date = models.DateTimeField()
        completed = models.BooleanField(default=False)
        urgent = models.BooleanField(default=False)
        pending= models.BooleanField(default=False)
        documents = GenericRelation('Document')
        content_type = models.CharField(max_length=50, null=True, blank=True)
        completion_note = models.TextField(null=True , blank=True)
    
        ### MANAGEMENT ###
        submitted_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
        approved_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, 
                                 related_name='aproved_by', null=True, blank=True)
        submitted_at = models.DateTimeField(null=True, blank=True)
        task_approvals = models.ManyToManyField(UserProfile, related_name='approval_task')
        approvals= models.IntegerField(default=0)
        denied = models.BooleanField(default=False)
        deny_reason = models.TextField(null=True, blank=True)
   
        ### CHART ###
        section = models.ForeignKey(
            'ChartSection', on_delete=models.CASCADE, null=True, blank=True)
        chart = models.ForeignKey(
            'Chart', on_delete=models.CASCADE, null=True, blank=True)
        
 
        position = models.PositiveIntegerField(default=0)

        @property
        def week(self):
            if self.starting_date and self.due_date:
                delta = self.due_date - self.starting_date
                return int(round(delta.days / 7, 0))
            return 0
        
        def __str__(self):
           return self.name
        
        def delete(self, *args, **kwargs):
            self.users.clear()
            super().delete(*args, **kwargs)

        class Meta:
            indexes = [
                models.Index(fields=['completed']),
                models.Index(fields=['due_date']),
                models.Index(fields=['id']),
                models.Index(fields=['creation_date']),
            ]



class Report(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField()
    time = models.DateTimeField(auto_now_add=True)
    tasks = models.ManyToManyField(Task)
   



class DailyReport(models.Model):
    document = GenericRelation('Document')
    timestamp = models.DateTimeField(auto_now=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)


class SubTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    completed = models.BooleanField(default=False)
    description = models.TextField(null=True,blank=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)

class EventIcon(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='event_icons/')

class Event(models.Model):
    name = models.CharField(max_length=40)
    location = models.CharField(max_length=40)
    time = models.DateTimeField()
    users = models.ManyToManyField(UserProfile, related_name='event_users', null=True, blank=True)
    days = models.ManyToManyField('Day', null=True, blank=True, related_name='events')
    icon = models.ForeignKey(EventIcon, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.time.strftime('%D')
class Day(models.Model):
    date = models.DateField()
    content = models.CharField(null=True, blank=True)
    agenda = models.ForeignKey('Agenda', on_delete=models.CASCADE, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.date.strftime('%A')
    @property
    def day(self):
        return self.date.strftime('%d')

class Agenda(models.Model):
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True )
    days = models.ManyToManyField(Day, related_name='agenda_day')
    @property
    def name(self):
        return f'{self.days.first().date.strftime('%B%Y')}-{self.days.last().date.strftime('%B%Y')} '


class Document(models.Model):
  
    file = models.FileField(upload_to=object_directory_path)
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    content_object = GenericForeignKey('content_type', 'object_id')
    upload_time = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)

    @property
    def file_name(self):
        return os.path.basename(self.file.name)
    @property
    def time(self):
        return naturaltime(self.upload_time)
    
    indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['object_id']),
            models.Index(fields=['owner']),
            models.Index(fields=['upload_time']),
        ]



class ChartSection(models.Model):
    name = models.CharField(max_length=30, null=True)
    chart = models.ForeignKey('Chart', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class Chart(models.Model):
    title = models.CharField(max_length=25)
    
    start_date = models.DateField()
    end_date = models.DateField()
    teams = models.ManyToManyField(Team)

    @property
    def months(self):
        if self.start_date and self.end_date:
            months_array = []
            current = self.start_date.replace(day=1)
            while current <= self.end_date:
                months_array.append(current.strftime("%B"))
                current += relativedelta(months=1)
            return months_array

    def __str__(self):
        return self.title
    
    class Meta:
        indexes = [
            models.Index(fields=['id']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]


class ChartData(models.Model):
     chart = models.ForeignKey(Chart, on_delete=models.CASCADE)
     task_id = models.IntegerField()
     columns = ArrayField(models.IntegerField(), null=True)



class Schedule(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    week_range = models.ForeignKey('WeekRange', on_delete=models.CASCADE)
    monday = models.CharField(null=True, blank=True, help_text='9-17')
    tuesday = models.CharField(null=True, blank=True)
    wednesday = models.CharField(null=True, blank=True)
    thursday = models.CharField(null=True, blank=True)
    friday = models.CharField(null=True, blank=True)
    saturday = models.CharField(null=True, blank=True)
    sunday = models.CharField(null=True, blank=True)
    unscheduled = models.BooleanField(default=False)
    vacation = models.BooleanField(default=False)

    textmonday = models.CharField(null=True, blank=True)
    texttuesday = models.CharField(null=True, blank=True)
    textwednesday = models.CharField(null=True, blank=True)
    textthursday = models.CharField(null=True, blank=True)
    textfriday = models.CharField(null=True, blank=True)
    textsaturday = models.CharField(null=True, blank=True)
    textsunday = models.CharField(null=True, blank=True)



    
    
 
    message = models.TextField(null=True, blank=True)
    request_pending = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['week_range']),
        ]

    """ def save(self, *args, **kwargs):
            if not self.end_date and self.start_date:
                self.end_date = self.start_date + relativedelta(days=7)
            super().save(*args, **kwargs)"""

    
class LogginRecord(models.Model):
    schedule = models.ForeignKey('Schedule', on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

class WeekRange(models.Model):
    starting_day = models.DateTimeField()
    end_day = models.DateTimeField()
    @property
    def end_month(self):
        return self.end_day.strftime('%B')
    @property
    def start_month(self):
        return self.starting_day.strftime('%B')


class ResourceCategory(models.Model):
    name = models.CharField()
    def __str__(self):
        return self.name
    

class Options(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    login = models.BooleanField(default=True)
    late = models.BooleanField(default=True)
    help = models.BooleanField(default=True)
    active_task = models.BooleanField(default=True)
    task_approval_modal = models.BooleanField(default=False)
   


class Resource(models.Model):
    what = models.CharField()
    how = models.TextField()
    category = models.ForeignKey(ResourceCategory, on_delete=models.CASCADE)
    management = models.BooleanField(null=True)
    def __str__(self):
        return self.what

  
class Milestone(models.Model):
    name = models.CharField(max_length=25) 
    date = models.DateField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.name
    @property
    def timestamp(self):
        return self.date.strftime('%B %d')
    @property
    def month(self):
        return self.date.strftime('%B')
    
class Goal(models.Model):
    name = models.CharField(null=True, unique=True, max_length=24)
    accomplished = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)
    failed_at = models.DateTimeField(null=True, blank=True)
    type = models.ForeignKey('GoalType', on_delete=models.CASCADE, null=True, blank=True)
    
    value = models.PositiveIntegerField(null=True, blank=True)
    #time_limit = models.DateTimeField(null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)
  
    def __str__(self):
        return self.name

class GoalType(models.Model):
    name = models.CharField()
    description= models.CharField(null=True, blank=True)
    value_type = models.ForeignKey('ValueType', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name

class ValueType(models.Model):
    name= models.CharField()
    def __str__(self):
        return self.name
