from .models import UserProfile, Task, Team
from django.db.models import Q
from dateutil.relativedelta import relativedelta
import plotly.graph_objs as go
from plotly.offline import plot
from django.utils import timezone
##### UTILITY ###############

days_of_the_week = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
def copy_message_data(source, target_model):
    copy = target_model(
        id=source.id,
        user=source.user,
        title=source.title,
        content=source.content,
        timestamp=source.timestamp,
        task=source.task,
        picture=source.picture,
        content_type=source.content_type
    )
    copy.save()
    copy.recipient.set(source.recipient.all())
    return copy



def safe_divide(numerator, denominator):
            try:
                return (numerator / denominator) * 100
            except ZeroDivisionError:
                return 0
            
def get_graph_data(stats, ytick_var):
        x_ticks = []
        y_ticks = []
        y_ticks2 = []
        total_completed = 0 
        late_task_count = 0
        total_denied = 0
        total_urgent = 0
        total_submissions = 0
        for stat in stats:
       
            total_submissions += stat.submission  
            late_task_count += stat.late_tasks
            total_denied += stat.denied_tasks
            total_urgent += stat.urgent_tasks_success
            total_completed += stat.completed_tasks
    
            x_ticks.append(stat.timestamp)

            if ytick_var == "total_denied":
                y_ticks.append(total_denied)
                y_ticks2.append(total_submissions)
            if ytick_var == 'late_task_count':
                y_ticks.append(late_task_count)
            if ytick_var == 'total_urgent':
                 y_ticks.append(total_urgent)

        return {'x_ticks':x_ticks, 'y_ticks':y_ticks,
                    'total_completed':total_completed, 'late_task_count':late_task_count,
                    'total_denied':total_denied,'total_urgent':total_urgent,
                    'total_submissions':total_submissions, 'y_ticks2':y_ticks2}
        

graph_margin = dict(l=20, r=30, t=30, b=40)
graph_title = {
            'x': 0.5, 
            'y':0.98,
            'xanchor': 'center',  
            'yanchor': 'top'      
        }

graph_y_axis = dict(
            ticklabelposition="outside left", 
            automargin=True,
            ticksuffix="   ",
            tickfont=dict(size=15)
                    )

graph_x_axis = dict(
            ticklabelposition="outside bottom", 
            automargin=True,
            tickfont=dict(size=15),
            tickangle=0
                    )


def get_stats_data(user_profile, page=None):

    now = timezone.now()
    three_months_ago = now - relativedelta(days=90)
    start_date = f"{three_months_ago.day} {three_months_ago.strftime('%B')}" 
    end_date = f"{now.day} {now.strftime('%B')}" 
    date_string = start_date + ' '+  '-' + ' ' + end_date

    total_urgent_completed = 0
    tasks_time_total = 0
    if not page:
        stats = user_profile.stats.get()   
        tasks = Task.objects.filter(users__in=[user_profile])
        
        
        for task in tasks:
            if task.completion_time:
                tasks_time_total += task.completion_time 
                

        users = None
        plot_div1 = None
        plot_div2 = None
        task_mean_time = safe_divide(tasks_time_total, tasks.count())
        total_urgent_completed = tasks.filter(urgent=True, 
                submitted_at__lte = now, submitted_at__gte=three_months_ago).count()

    if page:

        tasks = Task.objects.filter(creation_date__lte = now,
                                        creation_date__gte=three_months_ago,
                                    ).order_by('creation_date')
        task_mean_time = 0
        for task in tasks:
             if task.completion_time:
                 task_mean_time += task.completion_time
             if task.urgent:
                 total_urgent_completed  += 1

        team = Team.objects.get(id = user_profile.team.id)
        users = UserProfile.objects.filter(team=team)
        days_missed = 0 
       
        total_days_scheduled = 0
        stats = team.stats.filter(timestamp__lte = now,
                                         timestamp__gte=three_months_ago,
                                       ).order_by('timestamp')   
        



        if page == 1:   
            data = get_graph_data(stats, 'late_task_count')
          
            fig1 = go.Figure(data=[go.Scatter(x=data['x_ticks'], y=data['y_ticks'], 
                                              line=dict(color='#EA7656', width=4),
                                              mode='lines+markers',)])
            graph_title['text'] = 'Late tasks over time'
            fig1.update_layout( margin=graph_margin,
                                title=graph_title,
                                xaxis=graph_x_axis,
                                yaxis=graph_y_axis,
                                plot_bgcolor="#FFECEC",
                                paper_bgcolor="lightgray",
                                )
        
            plot_div1 = plot(fig1, output_type='div')

            fig2 = go.Figure(data=[go.Bar(x=['Late','On time','Total'], 
                                        y=[data['late_task_count'],
                                            data['total_completed']-data['late_task_count'],
                                            data['total_completed']],
                                            marker_color=["#EA7656", "#B2E3BA","#93BDFC"])])
            graph_title['text'] = 'On time completion'
            fig2.update_layout( margin=graph_margin,
                                title=graph_title,
                                xaxis=graph_x_axis,
                                yaxis=graph_y_axis,
                                plot_bgcolor="#FFECEC",
                                paper_bgcolor="lightgray",
                                )
            
            plot_div2 = plot(fig2, output_type='div')


        if page == 2:

            data = get_graph_data(stats, 'total_denied')

            fig2 = go.Figure(data=[go.Bar(x=['Denied', 'Submissions'], 
                                          y=[data['total_denied'], data['total_submissions']],
                                          marker_color=["#EA7656","#93BDFC"])])
            
            graph_title['text'] = 'Denied and submissions'
            fig2.update_layout( margin=graph_margin,
                                title=graph_title,
                                xaxis=graph_x_axis,
                                yaxis=graph_y_axis,
                                plot_bgcolor="#FFECEC",
                                paper_bgcolor="lightgray",
                                )
        
            plot_div2 = plot(fig2, output_type='div')
        
            fig1 = go.Figure()

            fig1.add_trace(go.Scatter(x=data['x_ticks'], y=data['y_ticks'], 
                                              line=dict(color='#EA7656', width=4),
                                              name='Denied',
                                              mode='lines+markers'))
            fig1.add_trace(go.Scatter(x=data['x_ticks'], y=data['y_ticks2'], 
                                              line=dict(color='#93BDFC', width=4),
                                                 name='Submitted',
                                              mode='lines+markers'))
            
            graph_title['text'] = 'Denied vs submitted'
            fig1.update_layout(     legend=dict(
                                        x=0.1,          
                                        y=1,           
                                        xanchor="center",
                                        yanchor="top"    
                                    ),
                                margin=graph_margin,
                                title=graph_title,
                                xaxis=graph_x_axis,
                                yaxis=graph_y_axis,
                                plot_bgcolor="#FFECEC",
                                paper_bgcolor="lightgray",
                                )
            
            plot_div1 = plot(fig1, output_type='div')

        if page == 3:
            
            
            x_ticks = []
            y_ticks = []
            urgent_count = 0
            for task in tasks:
                    if task.urgent:
                        urgent_count += 1
                    x_ticks.append(task.creation_date)
                    y_ticks.append(urgent_count)
                        
            
            data = get_graph_data(stats, 'total_urgent')

            fig2 = go.Figure(data=[go.Bar(x=['Late', 'Succeeded'], 
                                        y=[urgent_count-data['total_urgent'],
                                            data['total_urgent']],
                                            marker_color=["#EA7656","#93BDFC"])])
            
            graph_title['text'] = 'Urgent tasks success'
            fig2.update_layout( margin=graph_margin,
                                title=graph_title,
                                xaxis=graph_x_axis,
                                yaxis=graph_y_axis,
                                plot_bgcolor="#FFECEC",
                                paper_bgcolor="lightgray",
                                )
        
            plot_div2 = plot(fig2, output_type='div')
        
            fig1 = go.Figure()

            fig1.add_trace(go.Scatter(x=x_ticks, y=y_ticks, 
                                            line=dict(color='#93BDFC', width=4),
                                        
                                            mode='lines+markers'))
            
            graph_title['text'] = 'Urgent tasks over time'
            fig1.update_layout(     legend=dict(
                                        x=0.1,          
                                        y=1,           
                                        xanchor="center",
                                        yanchor="top"    
                                    ),
                                margin=graph_margin,
                                title=graph_title,
                                xaxis=graph_x_axis,
                                yaxis=graph_y_axis,
                                plot_bgcolor="#FFECEC",
                                paper_bgcolor="lightgray",
                                )
            
            plot_div1 = plot(fig1, output_type='div')


    denied_ratio = round(safe_divide(data['total_denied'],  data['total_submissions']), 0)
    late_ratio = safe_divide(data['late_task_count'],  data['total_completed'])
    days_missed_ratio = safe_divide(days_missed, total_days_scheduled)
    urgent_ratio = safe_divide(data['total_urgent'], total_urgent_completed)
    ranges = range(1, 5)
    return {'stats':stats, 'denied_ratio': denied_ratio, 
            'late_ratio':late_ratio, 'days_missed_ratio':days_missed_ratio, 
            'urgent_ratio':urgent_ratio,  'users':users, 'plot1':plot_div1, 
            'plot2':plot_div2, 'ranges':ranges, 'date_string':date_string,
            'task_mean_time': round(task_mean_time/tasks.count(),1)
           
              }