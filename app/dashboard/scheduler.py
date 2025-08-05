from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from .models import WeekRange, UserProfile, Schedule
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django_apscheduler.models import DjangoJob, DjangoJobExecution

def start():

    DjangoJobExecution.objects.all().delete()
    DjangoJob.objects.all().delete()
    CheckWeekRanges()
    if not BackgroundScheduler().get_jobs():
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        scheduler.add_job(CheckWeekRanges, 'interval', hours=12, name='my_job', 
                           replace_existing=True)
        register_events(scheduler)
        scheduler.start()



def CheckWeekRanges():
     
        now= timezone.now()
        week_day = now.weekday()
        if week_day == 1:
            if WeekRange.objects.all().count() < 3:
                weeks_array = [7 , 14 , 21, 28]
                for d in weeks_array:
                    
                    week_range = WeekRange.objects.create(starting_day = now + relativedelta(days= d - 7), 
                                            end_day = now + relativedelta(days=d))
                    
                    users = UserProfile.objects.all()
                    for user in users:
                          Schedule.objects.create(user=user, week_range=week_range)

                    
        if week_day == 1:
               last_range  = WeekRange.objects.last()
               if last_range.end_day.day != (now + relativedelta(days=28)).day:
                     print((now + relativedelta(days=28)).day)
                    
                     week_range = WeekRange.objects.create(starting_day = now + relativedelta(days=21),
                                              end_day = now + relativedelta(days=28) )
                     
                     users = UserProfile.objects.all()
                     for user in users:
                          Schedule.objects.create(user=user, week_range=week_range)
                          
            
       

   