from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import View, UpdateView, DetailView, DeleteView
from django.contrib.auth.views import LogoutView, LoginView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Messages, UserProfile, Task, Team, ChatMessages, Resource
from .models import MessagesCopy, Chart, ChartData, ChartSection, Schedule, Document,SubTask
from .forms import MessageForm, RecipientForm, RecipientDelete, SubmitTask, DenyCompletedTask
from .forms import ForwardMessages,ChatForm,AddTaskChart,LoginForm,SubTaskForm,FileFieldForm
from .forms import ProfilePictureForm

from django.utils import timezone
import time
from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import naturaltime

from django.utils.http import http_date
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseForbidden
from .utility import copy_message_data, days_of_the_week
from .protect import ProtectedCreate, ProtectedDelete, ProtectedUpdate, ProtectedView
from django import forms
from django.db.models import Q
import json
from .utility import get_stats_data, save_files, create_stats, save_stats, save_profile_picture
from django.utils.timezone import timedelta
from dateutil.relativedelta import relativedelta
from django.utils.encoding import smart_str
from collections import defaultdict
import mimetypes
from django.core.files.storage import default_storage

########## CONFIG ############
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie 
from django.core.cache import cache  
  
user_model = get_user_model()  
allowed_roles_forms = ['dev']  
allowed_roles_management = ['dev']


##############################
from django_registration.backends.one_step.views import RegistrationView

class CustomRegistration(RegistrationView):
    template_name = 'dashboard/django_registration/registration_form.html'
    success_url = reverse_lazy('dashboard:home')


class AccountView(LoginRequiredMixin, View):
    template_name = 'dashboard/users/account_view.html'
  
    def get(self, request, pk):
        form = ProfilePictureForm()
        try:
          picture = Document.objects.filter(object_id = self.request.user.userprofile.id).last()
        except:
            picture = False
        print(picture)

        employee = UserProfile.objects.get(id = pk, user = self.request.user)
        cache_key = f'individual_stats{employee.id}'
       
        if cache.has_key(cache_key):
            ctx = cache.get(cache_key)
        else:
            ctx = get_stats_data(employee)  
            cache.set(cache_key, ctx, (24 * 60 * 60))

        ctx['picture'] = picture
        ctx['form'] = form
        
        return render(request, self.template_name, ctx)
    
    
    def post(self, request, pk):
        form = FileFieldForm(request.POST, request.FILES)
        employee = UserProfile.objects.get(id = pk, user = self.request.user)
  
        if not form.is_valid():
            
            cache_key = f'individual_stats{employee.id}'
            picture = Document.objects.get(object_id = self.request.user.userprofile.id)
            if cache.has_key(cache_key):
                ctx = cache.get(cache_key)
            else:
                ctx = get_stats_data(employee)  
                cache.set(cache_key, ctx, (24 * 60 * 60))

            ctx['picture'] = picture
            ctx['form'] = form
            return render(request, self.template_name, ctx)
    
        file = self.request.FILES.get('file')
        
        save_profile_picture(self, file, employee)
        return redirect(reverse('dashboard:user_account', args=[pk]))



class AccountUpdate(LoginRequiredMixin, UpdateView):
    template_name = 'dashboard/users/account_update.html'
    model = user_model
 
    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if request.user.id == pk:

            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('This is not your account')
   
        

class PasswordChangeView(PasswordChangeView):
      template_name = 'dashboard/users/password_update.html'
      success_url = reverse_lazy('password_change_done')


########## Home #############
class CustomLoginView(LoginView):
    authentication_form = LoginForm
    template_name = 'dashboard/login.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

@method_decorator([cache_page(60 * 60), vary_on_cookie], name='dispatch')
class BillboardView(LoginRequiredMixin, View):
    template = 'dashboard/billboard_view.html'
    def get(self, request):
        ctx = {'is_home':True}

        return render(request, self.template, ctx)



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
           Q(title__icontains=search) | Q(user__username__icontains=search))
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
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = Document.objects.filter(object_id = self.object.id)
        context['documents'] = documents

        messages = Messages.objects.filter(recipient = self.request.user.userprofile)

 ### Previous and next function ###
        index_list = []
        for message in messages:
            index_list.append(message.id)
        index_list.sort()
        position = index_list.index(self.object.id)

        if len(index_list) - 1 > position:
            next_index = index_list[position + 1] 
        else:
            next_index = None

        if index_list[0] != position:
            previous_index = index_list[position - 1]
        else:
            previous_index = None

        context['next_index'] = next_index
        context['previous_index'] = previous_index

        
        return context
    


# Create a message view dashboard, shows history too
class MessageView(LoginRequiredMixin, View):

    template = 'dashboard/messages/messages_send.html'
    def get(self, request):
        pk = self.request.user.id
        data = MessagesCopy.objects.filter(user_id=pk).order_by('-id')

        file_form = FileFieldForm()
        form = MessageForm(sender_id = self.request.user.id)
        form_add = RecipientForm(sender_id=self.request.user.id)
        form_del = RecipientDelete(sender_id=self.request.user.id)

        context = {'data': data, 'form': form, 'file_form': file_form, 'form_add':form_add, 
                   'form_del':form_del}
        return render(request, self.template, context)
       

    def post(self, request):
        user_profile = self.request.user.userprofile
        
        if 'send' in request.POST:

            file_form = FileFieldForm(request.POST, request.FILES)
            form = MessageForm(request.POST, request.FILES or None, sender_id=self.request.user.id)
            if not form.is_valid():
                pk = self.request.user.id
                data = MessagesCopy.objects.filter(user_id=pk)
                context = {'data': data, 'form': form, 'file_form': file_form, 'form_add':form_add, 'form_del':form_del}
                return render(request, self.template, context)
            
        
            report = form.save(commit=False)
        

            recipient = form.cleaned_data['recipient']
            report.user_id = request.user.id
            report.save()
            if request.FILES: 
                files = self.request.FILES.getlist('file_field')
                valid = save_files(self, files, report)

                if not valid:
                    pk = self.request.user.id
                    form_add = RecipientForm(sender_id=self.request.user.id)
                    form_del = RecipientDelete(sender_id=self.request.user.id)
                    data = MessagesCopy.objects.filter(user_id=pk).order_by('-id')
                    file_form.add_error('file_field',"Files must be below 2 MB")
                    ctx = {'data': data, 'form': form, 'form_add':form_add, 
                          'file_form': file_form, 'form_del':form_del}
                    return render(self.request, self.template, ctx)
                
            report.recipient.set(recipient.all())


            ##Making a copy for inbox
            copy_message_data(report , MessagesCopy)
            return redirect('dashboard:messages_create')  
    
        if 'add' in request.POST:
            form_add = RecipientForm(request.POST, sender_id=self.request.user.id, 
                                                         instance = user_profile) 
            if not form_add.is_valid():
                pk = self.request.user.id
                data = MessagesCopy.objects.filter(user_id=pk)
                context = {'data': data, 'form': form, 'form_add':form_add, 'form_del':form_del}
                return render(request, self.template, context)
            
            add = form_add.save(commit=False)
            previous_receivers = user_profile.recipients.all() 
            new_receivers = form_add.cleaned_data['recipients']
            combined_receivers = previous_receivers | new_receivers
            add.save()
            add.recipients.set(combined_receivers)
            return redirect('dashboard:messages_create')  
        
        if 'delete' in request.POST:
            form_del = RecipientDelete(request.POST, sender_id=self.request.user.id, 
                                                     instance = user_profile)
            if not form_del.is_valid():
                pk = self.request.user.id
                data = MessagesCopy.objects.filter(user_id=pk)
                context = {'data': data, 'form': form, 'form_add':form_add, 'form_del':form_del}
                return render(request, self.template, context)
            
            remove = form_del.save(commit=False)
            previous = user_profile.recipients.all()
            added = form_del.cleaned_data['recipients']
            new = previous.exclude(id__in=added.values_list('id', flat=True))
            remove.save()
            remove.recipients.set(new)
            return redirect('dashboard:messages_create')

    

class MessageUpdate(LoginRequiredMixin, UpdateView):
    model = MessagesCopy
    template_name = 'dashboard/messages/messages_update.html'
    
    fields = ['recipient','title', 'content']
    success_url = reverse_lazy('dashboard:messages_create')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file_form = FileFieldForm()
        context['file_form'] = file_form
        return context


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
        file_form = FileFieldForm(self.request.POST, self.request.FILES)
        response = super().form_valid(form)
        report = self.object

        if self.request.FILES:
         
            files = self.request.FILES.getlist('file_field')
            valid = save_files(self, files, report)

            if not valid:
                file_form.add_error('file_field',"Files must be below 2 MB")
                ctx = {'form': form, 'file_form': file_form}
                return render(self.request, self.template_name, ctx)
          
        # Create a copy of the updated instance
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
        
        message = MessagesCopy.objects.get(id = pk)
        documents = Document.objects.filter(object_id = message.id)

        forwarded_msg = Messages(user=message.user, title=message.title,
                  content=message.content, task= message.task, forwarded=True, 
                  forwarded_by=self.request.user.userprofile, timestamp=message.timestamp)
        forwarded_msg.save()
        

        forwarded_msg.documents.set(documents.all())
        forwarded_msg.recipient.set(recipients.all())
        return redirect(reverse('dashboard:messages_create'))
    


class ReplyView(LoginRequiredMixin, View):
    template_name = 'dashboard/messages/reply_view.html'

    def get(self, request, recipient_id):
        file_form = FileFieldForm()
        form = MessageForm(sender_id = self.request.user.id)
        recipient = UserProfile.objects.get(id = recipient_id)

        ctx = {'form':form, 'recipient':recipient, 'file_form':file_form}
        return render(request, self.template_name, ctx)
    

    def post(self, request, recipient_id):

        file_form = FileFieldForm(request.POST, request.FILES or None)
        form = MessageForm(request.POST, request.FILES or None, sender_id=self.request.user.id)
        recipient = UserProfile.objects.get(id = recipient_id)
        
        if not form.is_valid:

            ctx = {'form':form, 'recipient':recipient, 'file_form':file_form}
            return render(request, self.template_name, ctx)
        
      
        message = form.save(commit=False)
        message.user_id = request.user.id
        message.save()

        if request.FILES:
            files = request.FILES.getlist('file_field')
            valid = save_files(self, files, message)
            if not valid:
                file_form.add_error('file_field',"Files must be below 2 MB")
                ctx = {'form':form, 'recipient':recipient, 'file_form':file_form}
                return render(request, self.template_name, ctx)
            
        recipient = UserProfile.objects.filter(id = recipient_id)
        message.recipient.set(recipient.all())
        copy_message_data(message , MessagesCopy)
        return redirect('dashboard:messages')  


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
    
    def get_context_data(self, **kwargs):
        fileform = FileFieldForm()
        context = super().get_context_data(**kwargs)
        context['file_form'] = fileform
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        task = self.object
        file_form = FileFieldForm(self.request.POST, self.request.FILES)
        if file_form.is_valid():
   
            files = self.request.FILES.getlist('file_field')
            save_files(self, files, task)
            

        return response


class TasksList(LoginRequiredMixin, View):

    template_name = 'dashboard/tasks/tasks_list.html'

    def get(self, request):   
      
        tasks = Task.objects.filter(users=self.request.user.userprofile.id)
       
        time = timezone.now()
      
        context = {'tasks': tasks, 'time': time}
        return render(request, self.template_name, context)




class TaskDetail(LoginRequiredMixin, View):
    template_name = 'dashboard/tasks/task_detail.html'
    time_threshold = timezone.now() - relativedelta(hours=24)
    context_object_name = 'task'
    
    def get(self, request, pk):
        form = FileFieldForm()
        subtask_form = SubTaskForm()

        task = Task.objects.get(id = pk, users=self.request.user.userprofile)
        subtasks = SubTask.objects.filter(task=task).order_by('-id')
        user_files = Document.objects.filter(owner = self.request.user.userprofile, object_id=task.id)
        files = Document.objects.filter(object_id = task.id)      
        old_files = files.filter(upload_time__lte=self.time_threshold)
        recent_files = files.filter(upload_time__gte = self.time_threshold).order_by('-upload_time')

        ctx = {'task': task, 'form':form, 'subtask_form':subtask_form, 'files': old_files, 
               'recent_files':recent_files, 'user_files':user_files, 'subtasks':subtasks}
        return render(request, self.template_name, ctx)
    
    def post(self, request, pk):
       
        task = Task.objects.get(id = pk, users=self.request.user.userprofile)
        subtask_form = SubTaskForm(request.POST)
        form = FileFieldForm(request.POST, request.FILES)
        print(request.POST)
        if request.FILES:
            if not form.is_valid():
                subtasks = SubTask.objects.filter(task=task).order_by('-id')
                user_files = Document.objects.filter(owner = self.request.user.userprofile, object_id=task.id)
                files = Document.objects.filter(object_id = task.id)
                time_threshold = timezone.now() - relativedelta(hours=24)
                old_files = files.filter(upload_time__lte=time_threshold)
                recent_files = files.filter(upload_time__gte = time_threshold).order_by('-upload_time')

                ctx = {'task': task, 'form':form, 'subtask_form':subtask_form, 'files': old_files, 
                'recent_files':recent_files, 'user_files':user_files, 'subtasks':subtasks}
                return render(request, self.template_name, ctx)
        
        
            files = self.request.FILES.getlist('file_field')
            save_files(self, files, task)
               
        else:
            subtask = subtask_form.save(commit=False)

            if request.POST.get('action'):
                  id = request.POST.get('action')[6:]
             
                  subtask = SubTask.objects.get(id = int(id))
                  subtask.delete()

            elif request.POST.get('subtask_id'):
                subtask_id = request.POST['subtask_id']
                existing_subtask = SubTask.objects.get(id = subtask_id)
                existing_subtask.name = subtask.name
                existing_subtask.description = subtask.description.strip()
                existing_subtask.save()

                
            else:
           
                subtask.task = task
                subtask.user = self.request.user.userprofile
                subtask.save()

        return redirect(reverse('dashboard:task_detail', args=[pk]))




def SubtaskCompleted(request, task, pk):
    subtask = SubTask.objects.get(id = pk)
    if subtask.completed:
        subtask.completed= False
        
    else:
        subtask.completed = True
    subtask.save()
    return redirect(reverse('dashboard:task_detail', args=[task]))



class TaskUpdate(ProtectedUpdate):
    model = Task
    template_name = 'dashboard/management/task_update.html'
    fields = ['name', 'description', 'urgent', 'due_date', 'users', 'completed']
    
    
    def get_success_url(self):
        task_id = self.object.id
        success_url = reverse('dashboard:task_manage_update', args=[task_id])
        return success_url
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file_form = FileFieldForm()
        subtasks = SubTask.objects.filter(task = self.object)
        files = Document.objects.filter(object_id = self.object.id)
        user_files = files.filter(owner= self.request.user.userprofile)
        context['subtasks'] = subtasks
        context['file_form'] = file_form
        context['files'] = files
        context['user_files'] = user_files
        context['task'] = self.object
      
        return context
    

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        profile = UserProfile.objects.get(id=self.request.user.id)
        team = profile.team.name
        team_users = UserProfile.objects.filter(team__name=team)  
        form.fields['due_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})
        form.fields['users'].queryset = team_users
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        task = self.object
        file_form = FileFieldForm(self.request.POST, self.request.FILES)
        if file_form.is_valid():
            if self.request.POST.get('delete'):
        
                Task.objects.get(id = task.id).delete()
                return redirect('dashboard:team')
            
   
            files = self.request.FILES.getlist('file_field')
      
            save_files(self, files, task)

        return response
        
    
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
        task = Task.objects.get(id = pk)
        if not form.is_valid():
            ctx = {'form': form, 'task':task}
            return render(request, self.template, ctx)
        
        
        user_profile = self.request.user.userprofile
        note = form.cleaned_data['completion_note']

        task.completion_note = note
        task.completed = True
        task.submitted_by = user_profile
        task.submitted_at = timezone.now()
        task.completion_time = round(((((timezone.now()-task.creation_date).total_seconds())/60)/60), 2)
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
    template_name = 'dashboard/projects/chart_task_create.html'

    
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

        ctx = {'charts': charts, 'allowed_roles':allowed_roles_management}
    
        return render(request, self.template_name, ctx)
    


class ChartDetail(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/projects/projects_view.html'
    def get(self,request, pk):

        team = self.request.user.userprofile.team
        chart = Chart.objects.get(id = pk)
        day = chart.start_date.day
        time_delta = chart.end_date - chart.start_date
        number_of_weeks = time_delta.days / 7

        if day <= 7:
            grey =  1
        elif day <= 14:
            grey= 2
        elif day <= 21:
            grey= 3
        else:
            grey= 4

      
        total_week_col = range(int(number_of_weeks) + grey)
        week_int = int(number_of_weeks + grey)

        grey_col_list = []
        for number in range(1, week_int + 1):
            if ((number - 1) //4) % 2 == 0:
                grey_col_list.append(number)

        if week_int > 32:
            month_list = []
            for n in chart.months:
                month_list.append(n[:3])
        else :
            month_list = None
      
        sections = ChartSection.objects.filter(chart=chart)
        tasks = Task.objects.filter(chart=chart)
     
        tasks_by_section = defaultdict(list)
        for task in tasks:
             tasks_by_section[task.section_id].append(task)

   
        charts = Chart.objects.filter(teams = team ).order_by('id')
        ctx = {'charts': charts, 'chart':chart, 'weeks':total_week_col, 
               'grey':grey , 'sections':sections, 'week_int':week_int, 
               'grey_col_list':grey_col_list,'months_list':month_list, 
               'tasks_by_section':tasks_by_section, 'allowed_roles':allowed_roles_management}
       
   

        return render(request, self.template_name, ctx)
    


    def post(self,request, pk):

        json_data = json.loads(request.body)

        all_data = json_data['data']
        chart = Chart.objects.get(id=pk)
        
        for key, value in all_data.items():            
            chart_data = ChartData(id = key, task_id=key, columns = value, chart=chart)
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
    fields =['monday','tuesday','wednesday','thursday','friday','saturday','sunday', 
             'unscheduled', 'vacation']

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
        time = timezone.now()
      
        team = Team.objects.get(team_lead = self.request.user.userprofile)
        team_member = UserProfile.objects.filter(team__name=team)
        team_name = team.name
        tasks = Task.objects.filter(
            users__team = team, completed=False).order_by('due_date').distinct()
        
        query = Q(completed=True, submitted_by__team__name = team_name) & Q(approved_by__isnull=True)
        completed_task_count = Task.objects.filter(query).count()    

    
        context = {'team': team_member , 'count':completed_task_count,'tasks':tasks,
                   'time':time}
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
            user_stats = create_stats(user)
                
            user_stats.denied_tasks += 1
            user_stats.submission += 1
            user_stats.save()

    
        team_stats = create_stats(team)
        team_stats.denied_tasks += 1
        team_stats.submission += 1
        team_stats.save()

        return redirect(self.success_url)
        
        


    

class TeamCompletedApprove(ProtectedView):

    def get(self, request, pk):
        task = Task.objects.get(id=pk)
        users = task.users.all()
        team = Team.objects.get(id = self.request.user.userprofile.team.id)
   
        if task.submitted_at > task.due_date:
            for user in users:
              
                user_stats = create_stats(user)
                save_stats(user_stats, late=True)

            team_stats = create_stats(team)
            save_stats(team_stats, late=True)
         
        else:
            if task.urgent:
                for user in users:

                    user_stats = create_stats(user)
                    save_stats(user_stats, urgent=True)
       
                team_stats = create_stats(team)
                save_stats(team_stats, urgent=True)
              
              
            else:
                for user in users:           
                    user_stats = create_stats(user)
                    save_stats(user_stats)
 
                team_stats = create_stats(team)
                save_stats(team_stats)
        

        task.approved_by = self.request.user.userprofile   
        task.submitted_at = timezone.now()
                           
        task.save()
        return redirect(reverse('dashboard:team'))

class RessourcesView(View):
    template_name = "dashboard/management/ressources.html"
    def get(self,request):

        if self.request.user.userprofile.role.name in allowed_roles_management:
            resources = Resource.objects.all()
        else:
            resources = Resource.objects.filter(management=False)

        ctx = {'resources':resources}
        return render(request, self.template_name, ctx)
    
    
############## TEAM STATS #####################################
@method_decorator([cache_page(60 * 60 * 24), vary_on_cookie], name='dispatch')
class PerformanceDetail(ProtectedView):
    template_name = 'dashboard/management/perf_detail.html'
    def get(self, request, pk):

        employee = UserProfile.objects.get(id = pk)
        cache_key = f'individual_stats{employee.id}'

        if cache.has_key(cache_key):
            ctx = cache.get(cache_key)
        else:
            ctx = get_stats_data(employee)  
            cache.set(cache_key, ctx, (24 * 60 * 60))
        
        return render(request, self.template_name, ctx)


@method_decorator([cache_page(60 * 60 * 24), vary_on_cookie], name='dispatch')
class PerformanceView(ProtectedView):
    template_name = 'dashboard/management/perf_view.html'

    def get(self, request, pk, page=1):
     
        user_profile = UserProfile.objects.get(user = self.request.user)
        cache_key = f'team_stats{user_profile.team.id}_page{page}'

        if cache.has_key(cache_key):
            ctx = cache.get(cache_key)
        else:
            ctx = get_stats_data(user_profile, page)
            cache.set(cache_key, ctx, (24 * 60 * 60))
        
        return render(request, self.template_name, ctx)



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

def FetchSubtask(request, pk):
    if request.method =='GET':
        subtask = SubTask.objects.get(id=pk)
        data = {'name':subtask.name, 'description': subtask.description, 
                'user':subtask.user.user.username}
  
        return JsonResponse(data)

 
def ChatUpdate(request):

    data = []
    profile = UserProfile.objects.get(id=request.user.id)

    team = profile.team
    messages = ChatMessages.objects.filter(team= team).order_by('-created_at')[:50]
    for message in messages:
        text = message.message
        user = message.user.user.username
        try:
            pic = Document.objects.filter(object_id = message.user.id).last()   
            pic_id = pic.id
        except:
            pic_id = 1
   
        time = naturaltime(message.created_at)
        timed_message = {'user':user, 'text':text,'time': time, 'pic_id':pic_id}
        data.append(timed_message)
    return JsonResponse(data, safe=False)



def stream_file(request, pk):
    file = Document.objects.get(id = pk)
    content_type=mimetypes.guess_type(file.file.name)[0]
    file_path = file.file.path
    if content_type not in ['image/png', 'image/jpeg', 'image/jpg']:
    
  
        response = FileResponse(open(file_path, 'rb') , as_attachment=True, filename=file.file.name)
  
    else:
        
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Cache-Control'] = 'public, max-age=86400'  # Cache for 1 day
            response['Expires'] = http_date(time.time() + 86400)
  
    return response



def stream_completed_task_img(request, pk):
    pic = get_object_or_404(Task, id=pk)
    response = HttpResponse()
    response['Content-Type'] = pic.content_type
    response['Content-Length'] = len(pic.picture)
    response.write(pic.picture)
    return response

def GetFile(request, pk):
    file = get_object_or_404(Document, id=pk)
    file_path = file.file.path
    file_name = file.file.name

    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=mimetypes.guess_type(file_name)[0] or 'application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{smart_str(file_name)}"'
        return response

def DelFile(request, pk, manage=0):
   
    file = Document.objects.get(id = pk)
    file_path = file.file.path
    task_id = file.content_object.id
 
    if default_storage.exists(file_path):
        default_storage.delete(file_path)
    file.delete()

    if manage == 1:
        success_url = redirect(reverse('dashboard:task_manage_update', args=[task_id]))
    else:
        success_url = redirect(reverse('dashboard:task_detail', args=[task_id]))
    return success_url

class Logout(LogoutView):
    template_name = 'dashboard/logout.html'
