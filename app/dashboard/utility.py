from .models import UserProfile, Task, Team, Document, Stats, Milestone, Goal
from django.db.models import Q
from dateutil.relativedelta import relativedelta
import plotly.graph_objs as go
from plotly.offline import plot
from django.utils import timezone
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from twilio.rest import Client
from django.conf import settings
user_model = get_user_model()
##### UTILITY ###############
import os 
days_of_the_week = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

  
def send_sms(phone_number, content):
    user_phone = f'+1{phone_number}'
   
    account_sid = os.environ.get('TWILIO_ACCCOUNT_SID').strip("'\"")
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN').strip("'\"")
    client = Client(account_sid, auth_token)
    message = client.messages.create(
    messaging_service_sid=os.environ.get('TWILIO_MSG_SID').strip("'\""),
    body=content,
    to=user_phone
    )
    print(message.sid)


def save_stats(stats, late=False, urgent=False):
    stats.completed_tasks += 1
    stats.submission += 1
    if late:
        stats.late_tasks += 1
    if urgent:
        stats.urgent_tasks_success += 1
    stats.save()


def create_stats(instance):
    stats = Stats.objects.create(content_object = instance, object_id=instance.id)  
    return stats    

def save_profile_picture(self, file, user):
        if file.size > 2 * 1024 * 1024:
            return False
        image = Image.open(file)

        width, height = image.size
        min_dim = min(width, height)

        # Calculate crop box to center the square
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim

        # Crop the image to a centered square
        image = image.crop((left, top, right, bottom))

        # Optional: resize to a fixed square size (e.g., 300x300)
        image = image.resize((300, 300), Image.Resampling.LANCZOS)

        # Save to memory
        image_io = BytesIO()
        image_format = image.format if image.format else 'PNG'
        image.save(image_io, format=image_format)

        # Create Django file object
        square_file = ContentFile(image_io.getvalue(), name=file.name)
        file_name = square_file.name    
        file_path = f'{user.__class__.__name__}/{user.id}/{file_name}'

     
          
        if default_storage.exists(file_path):
            file = Document.objects.get(file__icontains=file_name, object_id = user.id)
            if file.owner == self.request.user.userprofile:
                default_storage.delete(file_path)
                
                file.delete()

        Document.objects.create(file = square_file, owner =self.request.user.userprofile,
                                                          content_object = user)
        return True



def save_files(self, files, task):
    
    for f in files:
        file_name = f.name

        if f.size > 2 * 1024 * 1024:
                return False
        
        if task:
        
            file_path = f'{task.__class__.__name__}/{task.id}/{file_name}'

    
            
            if default_storage.exists(file_path):
                file = Document.objects.get(file__icontains=file_name, object_id = task.id)
                if file.owner == self.request.user.userprofile:
                    default_storage.delete(file_path)
                    
                    file.delete()

            Document.objects.create(file = f, owner =self.request.user.userprofile,
                                                            content_object = task)
        else:
            continue
             
    return True
   

def copy_message_data(source, target_model):
    copy = target_model(
        id=source.id,
        user=source.user,
        title=source.title,
        content=source.content,
        timestamp=source.timestamp,
        task=source.task,
           
    )
    copy.save()
    copy.recipient.set(source.recipient.all())
    copy.documents.set(source.documents.all())
    return copy



def safe_divide(numerator, denominator):
            try:
                return (numerator / denominator) * 100
            except ZeroDivisionError:
                return 0


def get_user_data(stats):
    total_completed = 0 
    late_task_count = 0
    total_denied = 0
    total_urgent = 0
    total_submissions = 0
    days_missed = 0
    days_scheduled = 0
    stars = []
    for stat in stats:

        total_submissions += stat.submission  
        late_task_count += stat.late_tasks
        total_denied += stat.denied_tasks
        total_urgent += stat.urgent_tasks_success
        total_completed += stat.completed_tasks
        days_missed += stat.days_missed
        days_scheduled += stat.days_scheduled
        
        if stat.star_note:
            stars.append(stat)
           
    
    return {'total_completed':total_completed, 'late_task_count':late_task_count,
                    'total_denied':total_denied,'total_urgent':total_urgent,
                    'total_submissions':total_submissions, 'days_missed':days_missed,
                    'days_scheduled':days_scheduled, 'stars':stars}
        


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

########## Main stats fetching function for both views ##########

def get_stats_data(user_profile, page=None):
    
    now = timezone.now()
    three_months_ago = now - relativedelta(days=90)
    start_date = f"{three_months_ago.day} {three_months_ago.strftime('%B')}" 
    end_date = f"{now.day} {now.strftime('%B')}" 
    date_string = start_date + ' '+  '-' + ' ' + end_date
    
    days_missed_ratio = 0
    task_mean_time = 0
    total_urgent_completed = 0
    tasks_time_total = 0

    ########## FOR USERS ###########
    if not page:
       
        all_user_stats = user_profile.stats.filter().all()
        stats = get_user_data(all_user_stats)
        tasks = Task.objects.filter(users__in=[user_profile])

        for task in tasks:
            if task.completion_time:
                tasks_time_total += task.completion_time 
        
       

        users = None
        plot_div1 = None
        plot_div2 = None
   
        total_urgent_completed = tasks.filter(urgent=True, 
                submitted_at__lte = now, submitted_at__gte=three_months_ago).count()

    ############ FOR TEAMS #############
    if page:

        tasks = Task.objects.filter(creation_date__lte = now,
                                        creation_date__gte=three_months_ago,
                                    ).order_by('creation_date')
       
        for task in tasks:
             if task.completion_time:
                 task_mean_time += task.completion_time
             if task.urgent:
                 total_urgent_completed  += 1
      
        team = Team.objects.get(id = user_profile.team.id)
        users = UserProfile.objects.filter(team=team)
    
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

    ##### PROCEEDS FOR BOTH ######
    if page:
     
        origin = data
    else:
        origin = stats
        days_missed_ratio = safe_divide(origin['days_missed'], origin['days_scheduled'])
        task_mean_time = safe_divide(tasks_time_total, tasks.count())

    denied_ratio = round(safe_divide(origin['total_denied'],  origin['total_submissions']), 1)
    late_ratio = round(safe_divide(origin['late_task_count'],  origin['total_completed']), 1)
    urgent_ratio = round(safe_divide(origin['total_urgent'], total_urgent_completed), 1)
   
    
         
    ranges = range(1, 5)

    return {'stats':stats, 'denied_ratio': denied_ratio, 
            'late_ratio':late_ratio, 'days_missed_ratio':days_missed_ratio, 
            'urgent_ratio':urgent_ratio,  'users':users, 'plot1':plot_div1, 
            'plot2':plot_div2, 'ranges':ranges, 'date_string':date_string,
            'task_mean_time': round(safe_divide(task_mean_time, tasks.count()),1)
           
              }


def calculate_days_scheduled(user,last_sched):
   
     total_days = 0

     if last_sched.unscheduled:
          return
     if last_sched.monday:
          total_days += 1
     if last_sched.tuesday:
          total_days += 1
     if last_sched.wednesday:
          total_days += 1
     if last_sched.thursday:
          total_days += 1
     if last_sched.friday:
          total_days += 1
     if last_sched.saturday:
          total_days += 1
     if last_sched.sunday:
          total_days += 1

      
     Stats.objects.create(content_object=user, days_scheduled=total_days)
     return total_days

def calculate_milestones():
        now = timezone.now().date()
        first_user = user_model.objects.get(id=1)
        first_date = first_user.assigned_on
        milestones = Milestone.objects.all()
 
        if (now - first_date).days <= 100:
            time_gap = relativedelta(days=7)
         
        elif (now - first_date).days <= 365:
            time_gap = relativedelta(month=1)
           

        months_set = []
        
        week = first_date 
        while week <= now:
                month_str = week.strftime('%B')       
                if not month_str in months_set:
                    months_set.append(month_str)
                week += time_gap

        dates_set = []
        empty_count_dict = {}
        milestones_dict = {}
        last_month = None
        iter = 0
        empty_count_total = 0
    
        for month in months_set:
           for m in milestones:       
                milestones_dict[month] = [m for m in milestones if m.month == month]
                dates_set.append(m.timestamp)

           if iter == 0:
               last_month = month
               iter += 1
               continue
           
           for n in milestones_dict[last_month]:
                empty_count_dict[month] = empty_count_dict.get(month , 0) + 1 

           empty_count_dict[month] += empty_count_total
           empty_count_total += empty_count_dict[month]
        
        for key, val in empty_count_dict.items():
               empty_count_dict[key] = range(val)

        return {'dates_set':dates_set, 'months_set':months_set, 'milestones':milestones,
                'empty_count_dict':empty_count_dict, 'milestones_dict':milestones_dict}


def check_milestones():

    now = timezone.now()
    goals = Goal.objects.filter(accomplished = False)
    stats = Stats.objects.all()
    
    goals_dict = {}
   

    for goal in goals:

        if goal.value_type == 'Days':
     
            time_range = now - relativedelta(days=goal.value)
            stats = stats.filter(timestamp__lte = now, timestamp__gte=time_range)

   
        has_key = goals_dict.get(goal.type.name)
        if not has_key:
        

            goals_dict[goal.type.name] = goal
         
            total_denied = 0
            total_completed = 0
            for stat in stats:
                total_denied += stat.denied_tasks
                total_completed += stat.completed_tasks
   
            if goal.type.name == 'No denied tasks':
                if total_denied > 0 :
                    continue
                else:
                    Milestone.objects.create(date=now.date(), 
                                name=f'{goal.type.name}{goal.value}{goal.value_type}')
            if goal.type.name == 'Tasks completed':
          
                if total_completed >= goal.value:
                        goal.accomplished = True
                        goal.save()
                        Milestone.objects.create(date=now.date(), 
                                name=f'{goal.type.name} ({goal.value})')
                else:
                     continue
            


def get_team_graph():
    
        teams = Team.objects.all()
        now = timezone.now()
        three_months_ago = now - relativedelta(days=90)
        team_list = []

        fig1 = go.Figure()
        color_list = ['lightblue','red', 'lightgreen']
        n = 0
        for team in teams:
            team_list.append(team.name)
            stats = Stats.objects.filter(timestamp__lte = now,
                                            timestamp__gte=three_months_ago,
                                        object_id=team.id).order_by('timestamp') 
            
            x_ticks = []
            y_ticks = []
            
            total_late = 0
            total_completed = 0
            for stat in stats:
                   total_completed += stat.completed_tasks
                   total_late += stat.late_tasks
                   y_ticks.append(round(safe_divide(total_late, total_completed),0))
                   x_ticks.append(stat.timestamp)
       

            #graph_dict[team.name] = {'x_ticks':x_ticks, 'y_ticks':y_ticks}
            
        
            

            fig1.add_trace(go.Scatter(x=x_ticks, y=y_ticks, 
                                              line=dict(color=color_list[n], width=4),
                                              name=f'{team.name}',
                                              mode='lines+markers'))
            n+=1
        
        graph_title['text'] = 'Teams effiency'
        graph_title['y'] = 0.95
        fig1.update_layout(legend=dict(
                            x=0.1,          
                            y=1,           
                            xanchor="center",
                            yanchor="top"    
                        ),
                         margin=dict(b=70, l=20, r=50,t=80),
                            title=graph_title,
                            xaxis=dict(
                                 
                                        ticks="outside",      
                                        ticklabelposition="outside",
                                              
                                    ),          
                            yaxis=dict(range=[0, 100], ticksuffix='%    ',
                                       ),
                            plot_bgcolor="#C8C8C8",
                            paper_bgcolor="#E3E3E3",
                         
                        )
 
        plot_div1 = plot(fig1, output_type='div')
        return {'graph':plot_div1}

