from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import View, UpdateView, DetailView, DeleteView, ListView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Messages, UserProfile, Task
from .forms import MessageForm, RecipientForm, RecipientDelete
from django.utils import timezone

# Dispatches by role after login

def role_dispatch(request):
    user_profile = request.user.userprofile
    if user_profile and user_profile.role:
        return redirect(user_profile.role.redirect_url)
    
    return redirect('dashboard:home')

# Home view dashboard
class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        template_name = 'dashboard/homeview.html'
        user_id = self.request.user.id
        reports = Messages.objects.filter(recipient=user_id).order_by('-timestamp')[:9]
        context = {'user': self.request.user, 'reports': reports}
        response = render(request, template_name, context)
        return response

######## Messages #################################

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
        form = MessageForm(request.POST, sender_id=self.request.user.id)
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
class TasksList(LoginRequiredMixin, View):
    template_name = 'dashboard/tasks_list.html'

    def get(self, request):   
    
        tasks = Task.objects.filter(users=self.request.user.userprofile)
        time = timezone.now()
        print(str(tasks))
        context = {'tasks': tasks, 'time': time}
        return render(request, self.template_name, context)


class TaskDetail(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/task_detail.html'
    context_object_name = 'task'
    
    def get_object(self):
        report_id = self.kwargs['pk']   
        return Task.objects.filter(id = report_id, users=self.request.user.userprofile)
    
    
class TaskDelete(LoginRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('dashboard/tasks')
        
