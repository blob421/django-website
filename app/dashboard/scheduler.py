from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from .models import WeekRange, UserProfile, Schedule, LogginRecord, Stats
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django_apscheduler.models import DjangoJob, DjangoJobExecution
from django.conf import settings
from .utility import calculate_days_scheduled


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

    if now.weekday() == settings.SCHEDULE_DAY:

        users = UserProfile.objects.all()
        if WeekRange.objects.all().count() < 3:
            weeks_array = [7 , 14 , 21, 28]
            for d in weeks_array:
                
                week_range = WeekRange.objects.create(
                    starting_day = now + relativedelta(days= d - 7), 
                    end_day = now + relativedelta(days=d))
                   
                for user in users:
                        Schedule.objects.create(user=user, week_range=week_range)

                    
        
        if last_range.end_day.day != (now + relativedelta(days=28)).day:

            last_range  = WeekRange.objects.last()     
            week_range = WeekRange.objects.create(starting_day = now + relativedelta(days=21),
                                    end_day = now + relativedelta(days=28))  
                   
            target_week_range = WeekRange.objects.order_by('-starting_day')[3]


            for user in users:

                last_schedule = Schedule.objects.get(user=user, week_range=target_week_range)
                total_days = calculate_days_scheduled(user, last_schedule)         
                logs = LogginRecord.objects.filter(schedule = last_schedule)
                days_list = set()

                for log in logs:
                    day = log.timestamp.day
                    days_list.add(day)
                    
                days_missed = total_days - len(days_list)

                if days_missed > 0:
                        Stats.objects.create(object_id = user.id, days_missed=days_missed)

                Schedule.objects.create(user=user, week_range=week_range)
                    
            
       

   