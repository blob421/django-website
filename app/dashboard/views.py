from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import View, UpdateView, DetailView, DeleteView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Messages, UserProfile, Task, Team, ChatMessages
from .models import MessagesCopy, Chart, ChartData, ChartSection, Schedule
from .forms import MessageForm, RecipientForm, RecipientDelete, SubmitTask, DenyCompletedTask
from .forms import ForwardMessages, ChatForm, AddTaskChart
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import naturaltime

from django.http import HttpResponse, JsonResponse
from .utility import copy_message_data, days_of_the_week
from .protect import ProtectedCreate, ProtectedDelete, ProtectedUpdate, ProtectedView
from django import forms
from django.db.models import Q
import json

from django.utils.timezone import timedelta



########## CONFIG ############

user_model = get_user_model()
allowed_roles_forms = ['dev']
allowed_roles_management = ['dev']


########## Home #############


class BillboardView(LoginRequiredMixin, View):
    template = 'dashboard/billboard_view.html'
    def get(self, request):

        return render(request, self.template)



######## Messages #################################

class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        template_name = 'dashboard/messages/messages_view.html'
        user_id = self.request.user.userprofile
        reports = Messages.objects.filter(recipient=user_id).order_by('-timestamp')[:9]
     
    
        context = {'user': self.request.user, 'reports': reports}
        response = render(request, template_name, context)
        return response
    

class InboxView(LoginRequiredMixin, View):
    template_name = "dashboard/messages/inbox.html"
    def get(self, request):
       
       search = request.GET.get('search', None)
       if search :
           query = Q(recipient=self.request.user.userprofile) & (
           Q(title__contains=search) | Q(user__username__contains=search))
           msg = Messages.objects.filter(query)
           
       else:
            msg = Messages.objects.filter(recipient = self.request.user.userprofile).order_by('-timestamp')
       
       ctx = {"messages": msg}
       return render(request, self.template_name, ctx)



    def post(self, request):
        tick_list = request.POST.getlist('selected_boxes')

        for id in tick_list:
            msg = Messages.objects.filter(recipient = self.request.user.userprofile, id = int(id))
            msg.delete()

        return redirect(reverse('dashboard:inbox'))



class MessageDetail(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/messages/message_detail.html'
    context_object_name = 'report'

    def get_object(self):
       report_id = self.kwargs['id']
    
       msg = Messages.objects.get(id=report_id, recipient=self.request.user.userprofile)
       msg.new = False
       msg.save()
       return msg
    


# Create a message view dashboard, shows history too
class MessageView(LoginRequiredMixin, View):

    template = 'dashboard/messages/messages_send.html'
    def get(self, request):
        pk = self.request.user.id
        data = MessagesCopy.objects.filter(user_id=pk)
        form = MessageForm(sender_id = self.request.user.id)
        context = {'data': data, 'form': form}
        return render(request, self.template, context)
       

    def post(self, request):
        form = MessageForm(request.POST, request.FILES or None, sender_id=self.request.user.id)
 
        if not form.is_valid():
            pk = self.request.user.id
            data = MessagesCopy.objects.filter(user_id=pk)
            context = {'data':data, 'form': form}
            return render(request, self.template, context)
        report = form.save(commit=False)

        recipient = form.cleaned_data['recipient']
        report.user_id = request.user.id
        report.save()
        report.recipient.set(recipient.all())

        ##Making a copy for inbox
        copy_message_data(report , MessagesCopy)
        return redirect('dashboard:messages_create')  
    

    

class MessageUpdate(LoginRequiredMixin, UpdateView):
    model = MessagesCopy
    template_name = 'dashboard/messages/messages_update.html'
    
    fields = ['recipient','title', 'content']
    success_url = reverse_lazy('dashboard:messages_create')
    
    def get_form(self, form_class=None):
               
            form = super().get_form(form_class)
            sender_id = self.request.user.id
            profile = UserProfile.objects.get(user=sender_id)
            combined_qs = UserProfile.objects.filter(
            Q(team=profile.team) | Q(user__in=profile.recipients.all())
            ).distinct()
            allowed = combined_qs.exclude(id=sender_id)
            form.fields['recipient'].queryset = allowed
            return form


    def form_valid(self, form):
      
        response = super().form_valid(form)

        # Create a copy of the updated instance
        report = self.object
        copy_message_data(report, Messages)
        return response



class MessageDelete(DeleteView, LoginRequiredMixin):
    template_name = 'dashboard/messages/messages_confirm_delete.html'
    model = Messages
    success_url = reverse_lazy('dashboard:home')
    


class MessageForward(LoginRequiredMixin, View):
    template_name = 'dashboard/messages/message_forward.html'
    def get(self, request, pk):
        form = ForwardMessages()
        ctx = {'form': form}
        return render(request, self.template_name, ctx)
    
    def post(self, request, pk):
        form = ForwardMessages(request.POST)
        if not form.is_valid():
             ctx = {'form': form}
             return render(request, self.template_name, ctx)
        
        recipients = form.cleaned_data['recipient']
        message = Messages.objects.get(id = pk)
        forwarded_msg = Messages(user=message.user, title=message.title,
                  content=message.content, task= message.task, forwarded=True, 
                  forwarded_by=self.request.user.userprofile,
                  picture=message.picture, content_type=message.content_type)
        forwarded_msg.save()
        forwarded_msg.recipient.set(recipients.all())
        return redirect(reverse('dashboard:messages_create'))
    


class AddRecipient(LoginRequiredMixin, View):
    template = 'dashboard/messages/recipient_add.html'
    def get(self, request):

        form = RecipientForm(sender_id=self.request.user.id)
        
        context = {'form': form}
        return render(request, self.template, context)
    
    def post(self, request):
        user_profile = UserProfile.objects.get(user=self.request.user)
        form = RecipientForm(request.POST, sender_id=self.request.user.id, 
                             instance = user_profile)
        if not form.is_valid():
          
            context = {'form': form}
            return render(request, self.template, context)
    

        add = form.save(commit=False)
        previous_receivers = user_profile.recipients.all() 
        new_receivers = form.cleaned_data['recipients']
        combined_receivers = previous_receivers | new_receivers
        add.save()
        add.recipients.set(combined_receivers)
        return redirect('dashboard:messages_create')  
    


class DeleteRecipient(LoginRequiredMixin, View):
    template_name = 'dashboard/messages/recipient_delete.html'
    
    def get(self, request):
        form = RecipientDelete(sender_id=self.request.user.id)

        context = {'form': form}
        return render(request, self.template_name, context)
    
    def post(self, request):
        user_profile = UserProfile.objects.get(user = self.request.user)
        form = RecipientDelete(request.POST, sender_id = self.request.user.id, 
                         instance = user_profile)
        if not form.is_valid():
            context = {'form': form}
            return render(self.request, self.template_name, context)
        
        remove = form.save(commit=False)
        previous = user_profile.recipients.all()
        added = form.cleaned_data['recipients']
        new = previous.exclude(id__in=added.values_list('id', flat=True))
        remove.save()
        remove.recipients.set(new)
        return redirect('dashboard:messages_create')





################### TASKS #######################

class TaskManageCreate(ProtectedCreate):
    
    template_name = 'dashboard/management/task_create.html'
    success_url = reverse_lazy('dashboard:team')
    model = Task
    fields = ['name','description','due_date','users','urgent']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['due_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})
        return form
    
        

class TasksList(LoginRequiredMixin, View):

    template_name = 'dashboard/tasks/tasks_list.html'

    def get(self, request):   
      
        tasks = Task.objects.filter(users=self.request.user.userprofile.id)
       
        time = timezone.now()
      
        context = {'tasks': tasks, 'time': time}
        return render(request, self.template_name, context)



class TaskCreate(ProtectedCreate):
     
     model = Task
     fields = ['name', 'description', 'urgent', 'due_date', 'users']
     success_url = reverse_lazy('dashboard:tasks_list')



class TaskDetail(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/tasks/task_detail.html'
    context_object_name = 'task'
    
    def get_object(self):
        report_id = self.kwargs['pk']   
        return Task.objects.filter(id = report_id, users=self.request.user.userprofile)
    

class TaskUpdate(ProtectedUpdate):
    model = Task
    template_name = 'dashboard/management/task_update.html'

    fields = ['name', 'description', 'urgent', 'due_date', 'users', 'completed']
    success_url = reverse_lazy('dashboard:team')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        profile = UserProfile.objects.get(id=self.request.user.id)
        team = profile.team.name
        team_users = UserProfile.objects.filter(team__name=team)  
        form.fields['due_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})
        form.fields['users'].queryset = team_users
        return form
    
    
class TaskDelete(ProtectedDelete):
    model = Task
    template_name ='dashboard/management/task_confirm_delete.html'
    success_url = reverse_lazy('dashboard:team')

    def get(self, request, pk):
        return render(request, self.template_name)

    def post(self,request, pk):
        task = Task.objects.get(id = pk)
        chart = ChartData.objects.get(id=pk)
        task.delete()
        chart.delete()
        return redirect(reverse('dashboard:team'))
        
    
class TaskSubmit(LoginRequiredMixin, View):
    template = 'dashboard/tasks/task_submit.html'
    success_url = reverse_lazy('dashboard:tasks_list')
        
    def get(self, request, pk):
        task = get_object_or_404(
        Task,
        Q(id=pk) & Q(users__in=[self.request.user.userprofile])
)
        form = SubmitTask()
        context= {'form': form, 'task':task}
        return render(request, self.template, context)
    

    def post(self, request, pk):
        form = SubmitTask(request.POST, request.FILES or None)
        
        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template, ctx)
        
        task = Task.objects.get(id = pk)
        user_profile = self.request.user.userprofile
        note = form.cleaned_data['completion_note']
        picture_file = form.cleaned_data['picture']

        if picture_file:
            if len(picture_file) > 2 * 1024 *1024:
                form.add_error('picture','Pictures must be less than 2 megabytes')

        if form.errors:
            task = get_object_or_404(Task, Q(id=pk) & Q(users__in=[self.request.user.userprofile]))
            return render(request, self.template, {'form': form, 'task':task})
        
        if picture_file:
            
            task.picture = picture_file.read()  
            task.content_type = picture_file.content_type

        task.completion_note = note
        task.completed = True
        task.submitted_by = user_profile
        task.save() 
       
        return redirect(self.success_url)
    


######## PROJECTS ####################################################

class ChartCreate(ProtectedCreate):
    template_name = 'dashboard/projects/chart_create.html'
    model = Chart
    fields = ['title', 'start_date', 'end_date', 'teams']
    success_url = reverse_lazy('dashboard:projects')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['start_date'].widget = forms.DateInput(attrs={'type': 'date'})
        form.fields['end_date'].widget = forms.DateInput(attrs={'type': 'date'})
        #form.fields['sections'] = ChartSection.objects.filter(chart = self.object)
        return form
    
    def form_valid(self, form):
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        max_duration = timedelta(days=396)  # 13 months ≈ 13 * 30.42 days

        if end_date - start_date > max_duration:
            form.add_error('end_date', 'End date must be within 13 months of the start date.')
            return self.form_invalid(form)

        return super().form_valid(form)



class ChartTaskCreate(ProtectedCreate):
    template_name = 'dashboard/projects/chart_task_create.html'
    def get(self, request, pk):
        chart = Chart.objects.get(id = pk)
        form = AddTaskChart(chart=chart)
        ctx = {'form':form}
        return render(request, self.template_name, ctx)

    
    
    def post(self, request, pk):
        chart = Chart.objects.get(id=pk)
        form = AddTaskChart(request.POST, chart=chart)

        if not form.is_valid():
            print('notvalid')
            ctx = {'form':form}
            return render(request, self.template_name, ctx)
    
        chart = Chart.objects.get(id = pk)
        saved_form = form.save(commit=False)
        saved_form.chart = chart
        saved_form.save()
        users = form.cleaned_data['users']
        saved_form.users.set(users.all()) 
        return redirect(reverse('dashboard:chart_detail', args=[pk]))
        
    

class ChartTaskUpdate(ProtectedUpdate):
    model= Task
    fields= ['name', 'description', 'users', 'starting_date', 'due_date', 'section']
    template_name = 'dashboard/projects/task_form.html'

    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['due_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})
        form.fields['starting_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})  
        form.fields['section'].queryset = ChartSection.objects.filter(chart = self.object.chart) 
        return form
    
    def get_success_url(self):
        chart_id = self.object.chart.id
        return reverse('dashboard:chart_detail', kwargs={'pk': chart_id})



class ProjectsView(LoginRequiredMixin, View):
    template_name = 'dashboard/projects/projects_view.html'
    def get(self,request):
        
        team = self.request.user.userprofile.team
        charts = Chart.objects.filter(teams = team ).order_by('id')

        ctx = {'charts': charts}
    
        return render(request, self.template_name, ctx)
    


class ChartDetail(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/projects/projects_view.html'
    def get(self,request, pk):
        chart = Chart.objects.get(id = pk)
        day = chart.start_date.day
        end = chart.end_date.day
        if day <= 7:
            grey =  1
        elif day <= 14:
            grey= 2
        elif day <= 21:
            grey= 3
        else:
            grey= 4

        time_delta = chart.end_date - chart.start_date
        number_of_weeks = time_delta.days / 7
     
        if end >= 30:
             total_week_col = range(int(round(number_of_weeks + grey /4)))
             week_int = int(round(number_of_weeks + grey) /4)
        elif end <= 10:
             total_week_col = range(int(number_of_weeks) + grey + 1)
             week_int = int(number_of_weeks + grey + 1)
        else : 
             total_week_col = range(int(number_of_weeks) + grey)
             week_int = int(number_of_weeks + grey)

        if week_int > 32:
            month_list = []
            for n in chart.months:
                month_list.append(n[:3])
        else :
            month_list = None
      
        sections = ChartSection.objects.filter(chart=chart)
        team = self.request.user.userprofile.team
        charts = Chart.objects.filter(teams = team ).order_by('id')
        ctx = {'charts': charts, 'chart':chart, 'weeks':total_week_col, 
               'grey':grey , 'sections':sections, 'week_int':week_int, 'months_list':month_list}
       
   

        return render(request, self.template_name, ctx)
    


    def post(self,request, pk):

        json_data = json.loads(request.body)
        print(json_data['data'])
        all_data = json_data['data']
        chart = Chart.objects.get(id=pk)
        
        for key, value in all_data.items():
            
            chart_data = ChartData(id = key, task_id=key, columns = value, chart=chart)
            print(chart_data)
            chart_data.save()
        return redirect(reverse('dashboard:projects'))
    


class ChartUpdate(ProtectedUpdate):
    model = Chart
    template_name = 'dashboard/projects/chart_form.html'
    fields= ['title', 'start_date', 'end_date', 'teams']
  
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chart = self.get_object()
        context['sections'] = ChartSection.objects.filter(chart=chart)
        return context
    
    def get_success_url(self):
        chart_id = self.object.id
        return reverse('dashboard:chart_detail', kwargs={'pk': chart_id})
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['start_date'].widget = forms.DateInput(attrs={'type': 'date'})
        form.fields['end_date'].widget = forms.DateInput(attrs={'type': 'date'})
       # form.fields['sections'].queryset = ChartSection.objects.filter(chart = self.object)
        return form

    def form_valid(self, form):
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        max_duration = timedelta(days=396)  # 13 months ≈ 13 * 30.42 days

        if end_date - start_date > max_duration:
            form.add_error('end_date', 'End date must be within 13 months of the start date.')
            return self.form_invalid(form)

        return super().form_valid(form)



class ChartDelete(ProtectedDelete):
    template_name = 'dashboard/projects/chart_confirm_delete.html'
    model = Chart
    success_url= reverse_lazy('dashboard:projects')



class AddSection(ProtectedCreate):
    model = ChartSection
    template_name = 'dashboard/projects/chartsection_form.html'
    fields = ['name']
    

    def form_valid(self, form):
        
        response = super().form_valid(form)
        pk = self.kwargs.get('pk')  
        chart = Chart.objects.get(id = pk)
        form.instance.chart = chart  
        form.save()
        return response
    
    def get_success_url(self):
         chart_id = self.kwargs.get('pk')  
         return reverse('dashboard:chart_detail', kwargs={'pk':chart_id})


######### TEAM SCHEDULES ###########################################

class ScheduleView(LoginRequiredMixin, View):
    template_name = 'dashboard/schedules/schedule_view.html'
    def get(self, request):
        
        return render(request, self.template_name)



class ScheduleDetail(LoginRequiredMixin, View):
    template_name = 'dashboard/schedules/schedule_view.html'
    def get(self, request, pk):
        schedule = Schedule.objects.get(id = pk)

        week_days = days_of_the_week
        hours = [schedule.monday, schedule.tuesday, schedule.wednesday, schedule.thursday,
                                      schedule.friday, schedule.saturday, schedule.sunday]
        
        days_hours = zip(week_days, hours)

        ctx = {'schedule':schedule, 'days_hours':days_hours}
        return render(request, self.template_name, ctx)



class ScheduleManage(ProtectedView):
    template_name = 'dashboard/management/schedule_manage.html'

    def get(self, request):
     
        team_users = UserProfile.objects.filter(team = self.request.user.userprofile.team)
          
        ctx= {'users':team_users}
        
        return render(request, self.template_name, ctx)



class ScheduleUpdate(ProtectedUpdate):
    template_name = 'dashboard/management/schedule_update.html'
    model = Schedule
    success_url = reverse_lazy('dashboard:schedule_manage')
    fields = days_of_the_week

    def form_valid(self, form):
        form.instance.message = None
        form.instance.request_pending = False
        return super().form_valid(form)


class AvailabilityForm(ProtectedUpdate):
    template_name = 'dashboard/management/availability.html'
    model = UserProfile
    fields = ['availability', 'weekends']
    success_url = reverse_lazy('dashboard:schedule_manage')


class ScheduleChangeRequest(LoginRequiredMixin, UpdateView):
    template_name = 'dashboard/schedules/schedule_change.html'
    model = Schedule
    fields = ['message']
    success_url = reverse_lazy('dashboard:schedule_view')
    def form_valid(self, form):
        form.instance.request_pending = True
        return super().form_valid(form)


######### TEAM ############################################

class TeamView(ProtectedView):
    template_name='dashboard/Management/team_view.html'
    def get(self, request):

        profile = UserProfile.objects.get(id=self.request.user.id)
        team = profile.team.name
        team_member = UserProfile.objects.filter(team__name=team)
        team = Team.objects.get(team_lead = self.request.user.userprofile)
        team_name = team.name
        query = Q(completed=True, submitted_by__team__name = team_name) & Q(approved_by__isnull=True)
        team_tasks = Task.objects.filter(query).count()    
        user = self.request.user
        context = {'user':user, 'team': team_member , 'count':team_tasks}
        return render(request, self.template_name, context)



class TeamUpdate(ProtectedUpdate):
     template_name = 'dashboard/management/team_update.html'
     model = Team
     fields = ['pinned_msg']
     success_url = reverse_lazy('dashboard:team')
     


class TeamCompletedTask(ProtectedView):
    model = Task
    template_name = 'dashboard/management/task_list.html'
  
 
    def get(self, request):
        time = timezone.now()
        team = Team.objects.get(team_lead = self.request.user.userprofile)
        team_name = team.name
        team_tasks = Task.objects.filter(completed=True, submitted_by__team__name = team_name).order_by('due_date') 
        ctx = {'tasks':team_tasks, 'time':time}     
        return render(request, self.template_name, ctx)



class TaskCompletedDetail(ProtectedView):
    template_name = 'dashboard/management/task_detail.html'
    context_object_name = 'task'
    success_url =  'dashboard:team'
    
    def get(self, request, pk):
      
        form = DenyCompletedTask()
        task = Task.objects.get(id = pk)
        ctx = {'form': form, 'task': task}   
        return render(request, self.template_name, ctx)
     
    
    def post(self, request, pk):

        form = DenyCompletedTask(request.POST)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)
        
        team = Team.objects.get(id = self.request.user.userprofile.team.id)
        task = Task.objects.get(id = pk)
        task.completed = False
        task.denied = True
        task.deny_reason = form.cleaned_data['deny_reason']
        task.save()

        users = task.users.all()
        for user in users:
            user_stats = user.stats.get()
            user_stats.denied_tasks += 1
            user_stats.save()

        team_stats = team.stats.get()
        team_stats.denied_tasks += 1
        team_stats.save()

        return redirect(self.success_url)
        


class TeamCompletedApprove(ProtectedView):

    def get(self, request, pk):
        task = Task.objects.get(id=pk)
        users = task.users.all()
        team = Team.objects.get(id = self.request.user.userprofile.team.id)
   
        if timezone.now() > task.due_date:
            for user in users:
                user_stats = user.stats.get()
                user_stats.completed_tasks += 1
                user_stats.late_tasks += 1
                user_stats.save()

            team_stats = team.stats.get()
            team_stats.completed_tasks += 1
            team_stats.late_tasks += 1
            team_stats.save()

        else:
            if task.urgent:
                for user in users:
                    user_stats = user.stats.get()
                    user_stats.completed_tasks += 1
                    user_stats.urgent_tasks_success += 1
                    user_stats.save()

                team_stats = team.stats.get()
                team_stats.completed_tasks += 1
                team_stats.urgent_tasks_success += 1
                team_stats.save()

            else:
                for user in users:
                    user_stats = user.stats.get()
                    user_stats.completed_tasks += 1
                    user_stats.save()

                team_stats = team.stats.get()
                team_stats.completed_tasks += 1
                team_stats.save()

        task.approved_by = self.request.user.userprofile   
        task.completion_time = round(((((task.creation_date - timezone.now()).seconds)/60)/60), 2)                           
        task.save()
        return redirect(reverse('dashboard:team'))


############## TEAM STATS #####################################

class PerformanceDetail(ProtectedView):
    template_name = 'dashboard/management/perf_detail.html'
    def get(self, request, pk):
        employee = UserProfile.objects.get(id = pk)
      
        ctx = {'user': employee}  
        return render(request, self.template_name, ctx)


class PerformanceView(ProtectedView):
    template_name = 'dashboard/management/perf_view.html'

    def get(self, request, pk):

        return render(request, self.template_name)



############# CHAT ####################################################

class ChatView(LoginRequiredMixin, View):
    template = 'dashboard/chat_view.html'
    def get(self, request):
        form = ChatForm()
        ctx = {'form': form}
        return render(request, self.template, ctx)
    
    def post(self, request):
        form = ChatForm(request.POST)
        if not form.is_valid():
             ctx = {'form': form}
             return render(request, self.template, ctx)
        submit = form.save(commit=False)
        profile = UserProfile.objects.get(id=request.user.id)
        team = profile.team
        submit.team = team
        submit.user = profile
        submit.save()
        return redirect(reverse('dashboard:chat_view'))






############ FUNCTION VIEWS ################################

def role_dispatch(request):
    user_profile = request.user.userprofile
    if user_profile and user_profile.role:
        return redirect(user_profile.role.redirect_url)
    
    return redirect('dashboard:home')



def SectionDelete(request, pk):
    section = ChartSection.objects.get(id=pk)
    chart = section.chart.id
    section.delete()
    return redirect(reverse('dashboard:chart_update', args=[chart]))
    
    

def ChartReset(request, pk):
    chart = ChartData.objects.filter(chart_id=pk).all()
    chart.delete()
    return redirect(reverse('dashboard:chart_detail', args=[pk]))
    


def LoadChart(request, pk):
    if request.method == 'GET':
        chart_data = ChartData.objects.filter(chart_id = pk)
        data = {}
        for row in chart_data:   
            data[row.task_id] = row.columns
        
        json_data = json.dumps(data)
        return JsonResponse(json_data, safe=False)



def ChatUpdate(request):

    data = []
    profile = UserProfile.objects.get(id=request.user.id)

    team = profile.team
    messages = ChatMessages.objects.filter(team= team).order_by('-created_at')[:10]
    for message in messages:
        text = message.message
        user = message.user.user.username
        time = naturaltime(message.created_at)
        timed_message = {'user':user, 'text':text,'time': time}
        data.append(timed_message)
    return JsonResponse(data, safe=False)



def stream_file(request, pk):
    pic = get_object_or_404(Messages, id=pk)
    response = HttpResponse()
    response['Content-Type'] = pic.content_type
    response['Content-Length'] = len(pic.picture)
    response.write(pic.picture)
    return response



def stream_completed_task_img(request, pk):
    pic = get_object_or_404(Task, id=pk)
    response = HttpResponse()
    response['Content-Type'] = pic.content_type
    response['Content-Length'] = len(pic.picture)
    response.write(pic.picture)
    return response


class Logout(LogoutView):
    template_name = 'dashboard/logout.html'
