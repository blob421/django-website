from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from .models import WeekRange, UserProfile, Schedule, LogginRecord, Stats, Document, ChatMessages
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django_apscheduler.models import DjangoJob, DjangoJobExecution
from django.conf import settings
from django.core.files.storage import default_storage
from .utility import calculate_days_scheduled, check_milestones
import logging

logger = logging.getLogger(__name__)

def start():
 
    DjangoJobExecution.objects.all().delete()
    DjangoJob.objects.all().delete()
    CheckWeekRanges()

    if not BackgroundScheduler().get_jobs():
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(CheckWeekRanges, 'interval', hours=12, name='my_job', 
                           replace_existing=True)
        scheduler.add_job(clear_pictures, 'interval', days=7, name='clear_pics',
                          replace_existing=True)
        
        scheduler.add_job(clear_files, 'interval', days=7, name='clear_files',
                          replace_existing=True)
        
        scheduler.add_job(clear_chat_msg, 'interval', days=7, name='clear_chat_msgs',
                          replace_existing=True)
        scheduler.add_job(check_milestones, 'interval', minutes=1, name='milestones',
                          replace_existing=True)
        
        register_events(scheduler)
        scheduler.start()
        


def clear_pictures():
     users = UserProfile.objects.all()
     for user in users:
          pictures = Document.objects.filter(object_id = user.id)
          last_picture = pictures.last()
          pictures.exclude(last_picture)
          
          for picture in pictures:
               file_path = picture.file.path
               if default_storage.exists(file_path):
                    default_storage.delete(file_path)

               picture.delete()


def clear_files():
     try:
         files = Document.objects.filter(
          upload_time__lte = timezone.now()-relativedelta(days=settings.FILE_RETENTION_DAYS))
         
         logger.INFO(f'{files.count()} files deleted')
         files.delete()
     except:
          raise('No files to delete')
          

def clear_chat_msg():
    try:
        msgs = ChatMessages.objects.filter(
          created_at__lte = timezone.now() - relativedelta(days=settings.CHAT_RETENTION_DAYS))
        msgs.delete()
    except:
        raise('No chat messages to delete')
     

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
                    
            
       

   