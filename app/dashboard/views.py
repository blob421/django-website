from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import View, UpdateView, DetailView, DeleteView, ListView, CreateView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Messages, UserProfile, Task, Team
from .forms import MessageForm, RecipientForm, RecipientDelete, TaskCreate
from django.utils import timezone
from django.contrib.auth import get_user_model
user_model = get_user_model()
from django.http import HttpResponse
from .owner import OwnerUpdateView

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
        template_name = 'dashboard/homeview.html'
        user_id = self.request.user.id
        reports = Messages.objects.filter(recipient=user_id).order_by('-timestamp')[:9]
        context = {'user': self.request.user, 'reports': reports}
        response = render(request, template_name, context)
        return response

######## Messages #################################
class InboxView(LoginRequiredMixin, ListView):
    template_name = "dashboard/inbox.html"
    context_object_name = "messages"

    def get_queryset(self):
        return Messages.objects.filter(recipient = self.request.user)
    
class MessageDetail(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/message_detail.html'
    context_object_name = 'report'

    def get_object(self):
       report_id = self.kwargs['id']
    
       return Messages.objects.get(id=report_id, recipient=self.request.user)
    

# Create a message view dashboard, shows history too
class MessageView(LoginRequiredMixin, View):

    template = 'dashboard/messages.html'
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
    fields = ['recipient','title', 'content']
    success_url = reverse_lazy('dashboard:reports')

class MessageDelete(DeleteView, LoginRequiredMixin):
    model = Messages
    success_url = reverse_lazy('dashboard:home')
    
### RECIPIENTS ##############################

class AddRecipient(LoginRequiredMixin, View):
    template = 'dashboard/add_recipient.html'
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
        return redirect('dashboard:reports')  
    

class DeleteRecipient(LoginRequiredMixin, View):
    template_name = 'dashboard/recipient_delete.html'
    
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
class TaskManageCreate(LoginRequiredMixin, View):
    template_name = 'dashboard/task_create.html'

    def get(self,request):

        profile = UserProfile.objects.get(id=self.request.user.id)
        team = profile.team.name
        team_member = UserProfile.objects.filter(team__name=team)

        form = TaskCreate(team=team_member)
        
        context = {'form': form}
        return render(request, self.template_name, context)
    


class TasksList(LoginRequiredMixin, View):

    template_name = 'dashboard/tasks_list.html'

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
    template_name = 'dashboard/task_detail.html'
    context_object_name = 'task'
    
    def get_object(self):
        report_id = self.kwargs['pk']   
        return Task.objects.filter(id = report_id, users=self.request.user.userprofile)
    
class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = Task
    fields = ['name', 'description', 'urgent', 'due_date', 'users']
    success_url = reverse_lazy('dashboard/team')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        profile = UserProfile.objects.get(id=self.request.user.id)
        team = profile.team.name
        team_users = UserProfile.objects.filter(team__name=team)  
        form.fields['users'].queryset = team_users
        return form
    
    
class TaskDelete(LoginRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('dashboard:team')
        
######### Manage #################

class TeamView(LoginRequiredMixin, View):
    template_name='dashboard/team_view.html'
    def get(self, request):

        profile = UserProfile.objects.get(id=self.request.user.id)
        team = profile.team.name
        team_member = UserProfile.objects.filter(team__name=team)
        user = self.request.user
        context = {'user':user, 'team': team_member}
        return render(request, self.template_name, context)

class TeamUpdate(OwnerUpdateView):
     model = Team
     fields = ['pinned_msg']
     success_url = reverse_lazy('dashboard:team')
     
    
       

def stream_file(request, pk):
    pic = get_object_or_404(Messages, id=pk)
    response = HttpResponse()
    response['Content-Type'] = pic.content_type
    response['Content-Length'] = len(pic.picture)
    response.write(pic.picture)
    return response