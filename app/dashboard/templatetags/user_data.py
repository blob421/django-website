from django import template
from ..models import Schedule, WeekRange, Document
from django.db.models import Q
import mimetypes

register = template.Library()

@register.filter
def slicer(doc_id):
 document = Document.objects.get(id=doc_id)
 content_type=mimetypes.guess_type(document.file.name)[0]

 return content_type[:5]
    
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_schedules(user, manage = False):
            
    weeks = WeekRange.objects.filter().order_by('-starting_day')[:4][::-1]
  
    week1=weeks[0]
    week2=weeks[1]
    week3=weeks[2]
    week4=weeks[3]
    week_days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    
    starting_month = week1.starting_day.strftime("%B")
    ending_month = week4.end_day.strftime("%B")
    all_schedules = Schedule.objects.filter(user= user.userprofile)
    query = Q(week_range = week1) | Q(week_range = week2) |Q(week_range = week3) | Q(
        week_range = week4)
    

    if not manage:
        
        return {'schedules':all_schedules.filter(query).order_by('id'), 
                'start_month': starting_month,
                'end_month': ending_month,
                'week_days':week_days}
    
    else: 
        
        schedules = Schedule.objects.filter(user__team = user.userprofile.team)
        last_month_schedules  = schedules.filter(query).order_by('id')
  
        return {
            
                'week_objects': weeks,
                'schedules': last_month_schedules,
                'start_month': starting_month,
                'end_month': ending_month,
             
                }




       
