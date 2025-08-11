from django import template
from ..models import Schedule, WeekRange
from django.db.models import Q


register = template.Library()



@register.filter
def get_schedules(user, manage = False):
            
    weeks = WeekRange.objects.all()[:4]
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
        week_array = []

        for week in weeks:
            start_day = week.starting_day
            end_day = week.end_day
    
            week_range = f'{start_day.day} {starting_month[:3]}- {end_day.day} {
                ending_month[:3]}' 
            
            week_array.append(week_range)

      
        return {
                'weeks': week_array,
                'week_objects': weeks,
                'schedules': last_month_schedules,
                'start_month': starting_month,
                'end_month': ending_month,
             
                }




       
