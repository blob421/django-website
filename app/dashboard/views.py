from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import View, UpdateView, DetailView, DeleteView, ListView, CreateView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Messages, UserProfile, Task, Team, CompletedTasks, ChatMessages
from .forms import MessageForm, RecipientForm, RecipientDelete, SubmitTask, DenyCompletedTask, ChatForm
from django.utils import timezone
from django.contrib.auth import get_user_model
user_model = get_user_model()
from django.http import HttpResponse, JsonResponse
from .owner import OwnerUpdateView, OwnerCreateView
from django.contrib.humanize.templatetags.humanize import naturaltime
import datetime
from django import forms

# Dispatches by role after login

def role_dispatch(request):
    user_profile = request.user.userprofile
    if user_profile and user_profile.role:
        return redirect(user_profile.role.redirect_url)
    
    return redirect('dashboard:home')

# Home view dashboard
class BillboardView(LoginRequiredMixin, View):
    template = 'dashboard/billboard_view.html'
    def get(self, request):
        user = UserProfile.objects.get(id=self.request.user.id)
        context = {'users':user}
        return render(request, self.template, context)

class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        template_name = 'dashboard/messages/messages_view.html'
        user_id = self.request.user.id
        reports = Messages.objects.filter(recipient=user_id).order_by('-timestamp')[:9]
        context = {'user': self.request.user, 'reports': reports}
        response = render(request, template_name, context)
        return response

######## Messages #################################
class InboxView(LoginRequiredMixin, ListView):
    template_name = "dashboard//messages/inbox.html"
    context_object_name = "messages"

    def get_queryset(self):
        return Messages.objects.filter(recipient = self.request.user).order_by('-timestamp')
    
class MessageDetail(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/messages/message_detail.html'
    context_object_name = 'report'

    def get_object(self):
       report_id = self.kwargs['id']
    
       return Messages.objects.get(id=report_id, recipient=self.request.user)
    

# Create a message view dashboard, shows history too
class MessageView(LoginRequiredMixin, View):

    template = 'dashboard/messages/messages.html'
    def get(self, request):
        pk = self.request.user.id
        data = Messages.objects.filter(user_id=pk)
        form = MessageForm(sender_id = self.request.user.id)
        context = {'data': data, 'form': form}
        return render(request, self.template, context)
       

    def post(self, request):
        form = MessageForm(request.POST, request.FILES or None, sender_id=self.request.user.id)
        if not form.is_valid():
            context = {'form': form}
            return render(request, self.template, context)
        report = form.save(commit=False)
        report.user_id = request.user.id
        report.save()
        return redirect('dashboard:reports')  
    

class MessageUpdate(LoginRequiredMixin, UpdateView):
    model = Messages
    template_name = 'dashboard/messages/messages_update.html'

    fields = ['recipient','title', 'content']
    success_url = reverse_lazy('dashboard:reports')

class MessageDelete(DeleteView, LoginRequiredMixin):
    template_name = 'dashboard/messages/messages_confirm_delete.html'
    model = Messages
    success_url = reverse_lazy('dashboard:home')
    
### RECIPIENTS ##############################

class AddRecipient(LoginRequiredMixin, View):
    template = 'dashboard/messages/recipient_add.html'
    def get(self, request):

        form = RecipientForm(sender_id=self.request.user.id)
        
        context = {'form': form}
        return render(request, self.template, context)
    
    def post(self, request):
        user_profile = UserProfile.objects.get(user=self.request.user)
        form = RecipientForm(request.POST, sender_id=self.request.user.id, instance = user_profile)
        if not form.is_valid():
          
            context = {'form': form}
            return render(request, self.template, context)
    

        add = form.save(commit=False)
        previous_receivers = user_profile.recipients.all() 
        new_receivers = form.cleaned_data['recipients']
        combined_receivers = previous_receivers | new_receivers
        add.save()
        add.recipients.set(combined_receivers)
        return redirect('dashboard:messages')  
    

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
        return redirect('dashboard:reports')


class Logout(LogoutView):
    template_name = 'dashboard/logout.html'


################### TASKS #######################
class TaskManageCreate(OwnerCreateView):
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
      
        tasks = Task.objects.filter(users=self.request.user.userprofile)
        time = timezone.now()
      
        context = {'tasks': tasks, 'time': time}
        return render(request, self.template_name, context)

class TaskForm(LoginRequiredMixin, CreateView):
     model = Task
     fields = ['name', 'description', 'urgent', 'due_date', 'users']
     success_url = reverse_lazy('dashboard:tasks_list')


class TaskDetail(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/tasks/task_detail.html'
    context_object_name = 'task'
    
    def get_object(self):
        report_id = self.kwargs['pk']   
        return Task.objects.filter(id = report_id, users=self.request.user.userprofile)
    
class TaskUpdate(LoginRequiredMixin, UpdateView):
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
    
    
class TaskDelete(LoginRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('dashboard:team')

class TaskSubmit(LoginRequiredMixin, View):
    template = 'dashboard/tasks/task_submit.html'
    success_url = reverse_lazy('dashboard:tasks_list')

    def get(self, request, pk):
       
        form = SubmitTask()
        context= {'form': form}
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
            
            task.picture = picture_file.read()  
            task.content_type = picture_file.content_type

        task.completion_note = note
        task.completed = True
        task.submitted_by = user_profile
        task.save()
        
       
       
        return redirect(self.success_url)

######### Management #################

class TeamView(LoginRequiredMixin, View):
    template_name='dashboard/Management/team_view.html'
    def get(self, request):

        profile = UserProfile.objects.get(id=self.request.user.id)
        team = profile.team.name
        team_member = UserProfile.objects.filter(team__name=team)
        team = Team.objects.get(team_lead = self.request.user.userprofile)
        team_name = team.name
        team_tasks = Task.objects.filter(completed=True, submitted_by__team__name = team_name).count()    
        user = self.request.user
        context = {'user':user, 'team': team_member , 'count':team_tasks}
        return render(request, self.template_name, context)

class TeamUpdate(OwnerUpdateView):
     template_name = 'dashboard/management/team_update.html'
     model = Team
     fields = ['pinned_msg']
     success_url = reverse_lazy('dashboard:team')
     
    
class TeamCompletedTask(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'dashboard/management/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        team = Team.objects.get(team_lead = self.request.user.userprofile)
        team_name = team.name
        team_tasks = Task.objects.filter(completed=True, submitted_by__team__name = team_name)      
        return team_tasks
    
class TaskCompletedDetail(LoginRequiredMixin, View):
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
        
      
        task = Task.objects.get(id = pk)
        task.completed = False
        task.denied = True
        task.deny_reason = form.cleaned_data['deny_reason']
        task.save()
        return redirect(self.success_url)
        


class TeamCompletedApprove(LoginRequiredMixin, View):

    def get(self, request, pk):

        user_profile = self.request.user.userprofile

        if user_profile == user_profile.team.team_lead:
            task = Task.objects.get(id=pk)
            
            completed_task = CompletedTasks(id = task.id, 
                                            submitted_by = task.submitted_by,
                                            description = task.description,
                                            name = task.name,
                                            completed = True,
                                            urgent = task.urgent,
                                            due_date = task.due_date,
                                            creation_date = task.creation_date,
                                            content_type = task.content_type,
                                            picture = task.picture,
                                            approved_by = user_profile,
                                            completion_note = task.completion_note)
            completed_task.save()
            completed_task.users.set(task.users.all())
            task.delete()
            return redirect(reverse('dashboard:team'))



############# CHAT #################

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
