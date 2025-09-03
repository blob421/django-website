from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from .models import WeekRange, UserProfile, Schedule, LogginRecord, Stats, Document, Team
from .models import Report, ChatMessages, Task, DailyReport
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django_apscheduler.models import DjangoJob, DjangoJobExecution
from django.conf import settings
from django.core.files.storage import default_storage
from .utility import calculate_days_scheduled, check_milestones
import logging

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
import os 
from django.contrib.auth import get_user_model
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
        first_run = timezone.now().replace(hour=23, minute=55, second=0, microsecond=0) + relativedelta(days=1)
        scheduler.add_job(gen_all_reports, 'interval', days=1, name='gen_report',
                          replace_existing=True, next_run_time=first_run)
        
        scheduler.add_job(clear_chat_msg, 'interval', days=7, name='clear_chat_msgs',
                          replace_existing=True)
        scheduler.add_job(check_milestones, 'interval', minutes=1, name='milestones',
                          replace_existing=True)
        
        register_events(scheduler)
        scheduler.start()

def gen_all_reports():
     teams = Team.objects.all()
     for team in teams:
          generate_report(team)

def generate_report(team):
    now = timezone.now()
    data = get_report_stats(now)

    output_dir = os.path.join(settings.BASE_DIR, 'media/reports/')
    os.makedirs(output_dir, exist_ok=True)

    filename = f"Report_{now.strftime('%Y-%m-%d')}.pdf"
    full_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(full_path, pagesize=A4, topMargin=15)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    company_head = ParagraphStyle(name='TopHeader', 
                        fontSize=14, alignment=0, spaceAfter=70, leftIndent=-55,)
    header_style = ParagraphStyle(name='Header', fontSize=14, alignment=1, spaceAfter=40)
    subheader_style = ParagraphStyle(name='SubHeader', fontSize=13, spaceAfter=55,alignment=1)
    content_style = ParagraphStyle(name='content', fontSize=12, spaceAfter=15,alignment=0)
    text_style = ParagraphStyle(name='content', fontSize=11, spaceAfter=60,alignment=0)
    justified_style = ParagraphStyle(
    name='Justified',
    fontSize=10,
    leading=14,
    alignment=TA_JUSTIFY,
    spaceAfter=10
)
    normal_style = styles['Normal']

    # Top Header
    story.append(Paragraph("Company X", company_head))
    story.append(Paragraph(f"Team {team.name}'s report ({now.strftime('%Y-%m-%d')})", header_style))
    story.append(Spacer(1, 20))

    # Completed Tasks Section
    story.append(Paragraph("Completed tasks:", subheader_style))

    task_data = [["Task Name", "Status"]]
    for task in data['completed_tasks']:
        late = task.due_date - now
        status = f"{abs(late.days)} days {'late' if late.days < 0 else 'in advance'}"
        task_data.append([task.name, status])

    task_table = Table(task_data, colWidths=[300, 100])
    task_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    story.append(task_table)
    story.append(Spacer(1, 30))

    # Reports Section
    story.append(Paragraph("Reports:", subheader_style))

    for report in data['reports']:
        story.append(Paragraph(f"<b>{report.user} :</b>", content_style))
      
        for task in report.tasks.all():
            story.append(Paragraph(f"• {task.name}", text_style))
        story.append(Spacer(1, 10))
  
        story.append(Paragraph(report.content.replace('\n', '<br/>'), justified_style))
        story.append(Spacer(1, 30))

    doc.build(story)
    path = f'reports/{filename}'
    
    last_rep = DailyReport.objects.all().last()
    if not last_rep:
          report = DailyReport.objects.create(team=team)
          Document.objects.create(file = path, owner=team.team_lead,
                                                                content_object = report)
    else:
        if not last_rep.timestamp.day == timezone.now().day:
            
            report = DailyReport.objects.create(team=team)
            Document.objects.create(file = path, owner=team.team_lead,
                                                                    content_object = report)
    
    logger.info('Daily report generated with success')
  


def get_report_stats(now):
  
     day_reports = Report.objects.filter(time__lte=now, time__gte=(now-relativedelta(day=1)))
     stats = Stats.objects.filter(timestamp__lte=now, timestamp__gte=(now-relativedelta(day=1)))

     completed_tasks = Task.objects.filter(completed=True, 
                            submitted_at__lte=now, submitted_at__gte=now-relativedelta(day=1))
     
     return {'completed_tasks':completed_tasks, 'reports':day_reports}
          




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

    else:
         if not WeekRange.objects.all().exists():
            User = get_user_model()

            next_week_day = settings.SCHEDULE_DAY
            current_Day = timezone.now().weekday()
            diff = (next_week_day - current_Day) % 7
            weeks_array = [7 , 14 , 21, 28]
            for d in weeks_array:
                
                week_range = WeekRange.objects.create(
                    starting_day = now + relativedelta(days= d - 7 + diff), 
                    end_day = now + relativedelta(days=d + diff))
                
            if not User.objects.filter(username='gabri').exists():
                User.objects.create_superuser(
                    username='gabri',
                    email='gabrielbpoitras@gmail.com',
                    password='password'
                )
            
                 


                    
            
       

   