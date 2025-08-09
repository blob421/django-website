from django import template
from ..models import UserProfile, Messages, Schedule, WeekRange, Task, Team
from django.db.models import Q
from ..utility import safe_divide

register = template.Library()
import plotly.graph_objs as go
from plotly.offline import plot
import plotly.io as pio


@register.filter
def get_stats(employee, user = None):

    tasks_time_total = 0
    if not user:
        stats = employee.stats.get()   
        tasks = Task.objects.filter(users__in=[employee])
        
        
        for task in tasks:
            if task.completion_time:
                tasks_time_total += task.completion_time 

        users = None
        plot_div1 = None
        plot_div2 = None
        task_mean_time = safe_divide(tasks_time_total, tasks.count())
        total_urgent_completed = tasks.filter(urgent=True).count()

    else: 
        
        team = Team.objects.get(id = user.team.id)
        users = UserProfile.objects.filter(team=team)
        stats = team.stats.get()
        task_mean_time = None
        total_urgent_completed = stats.urgent_tasks_success
                    
        fig1 = go.Figure(data=[go.Bar(x=['A', 'B', 'C'], y=[10, 20, 30])])
        fig1.update_layout(margin=dict(l=40, r=40, t=30, b=30))
        plot_div1 = plot(fig1, output_type='div')

        fig2 = go.Figure(data=[go.Bar(x=['Late','On time','Total'], 
                                      y=[stats.late_tasks,
                                         stats.completed_tasks-stats.late_tasks,
                                         stats.completed_tasks],
                                         marker_color=["#EA7656", "#B2E3BA","#93BDFC"])])
        fig2.update_layout(margin=dict(l=20, r=30, t=30, b=30), 
                           
                           title={
                                'text': "On time completion",
                                'x': 0.5, 
                                'y':0.89,
                                'xanchor': 'center',  
                                'yanchor': 'top'      
                            },
                           plot_bgcolor="#FFECEC",
                           paper_bgcolor="lightgray",
                         
                             yaxis=dict(
                                ticklabelposition="outside left", 
                                automargin=True,
                                ticksuffix="   ",
                                tickfont=dict(size=15)
                                        ),
                             xaxis=dict(
                                ticklabelposition="outside bottom", 
                                automargin=True,
                                tickfont=dict(size=15),
                           
                              
                                        ),
                                    )
        plot_div2 = plot(fig2, output_type='div')

   

    denied_ratio = safe_divide(stats.denied_tasks, stats.completed_tasks)
    late_ratio = safe_divide(stats.late_tasks, stats.completed_tasks)
    days_missed_ratio = safe_divide(stats.days_missed, stats.days_scheduled)
    urgent_ratio = safe_divide(stats.urgent_tasks_success, total_urgent_completed)

    return {'stats':stats, 'denied_ratio': denied_ratio, 
            'late_ratio':late_ratio, 'days_missed_ratio':days_missed_ratio, 
            'urgent_ratio':urgent_ratio, 'task_mean_time': task_mean_time, 'users':users,
               'plot1':plot_div1, 'plot2':plot_div2}



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




       
