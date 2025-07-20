from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, View, CreateView, DetailView
from django.contrib.auth.views import LogoutView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from .models import Reports, UserProfile
from .forms import MakeForm, AddRec

# Create your views here.

def role_dispatch(request):
    user_profile = request.user.userprofile
    if user_profile and user_profile.role:
        return redirect(user_profile.role.redirect_url)
    
    return redirect('dashboard:home')


class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        template_name = 'dashboard/home.html'
        user_id = self.request.user.id
        reports = Reports.objects.filter(user_id=user_id)[:1]
        context = {'user': self.request.user, 'reports': reports}
        response = render(request, template_name, context)
        return response

class ReportsView(LoginRequiredMixin, View):

    template = 'dashboard/reports.html'
    def get(self, request):
        pk = self.request.user.id
        data = Reports.objects.filter(user_id=pk)
        form = MakeForm(sender_id = self.request.user.id)
        context = {'data': data, 'form': form}
        return render(request, self.template, context)
       

    def post(self, request):
        form = MakeForm(request.POST, sender_id=self.request.user.id)
        if not form.is_valid():
            context = {'form': form}
            return render(request, self.template, context)
        report = form.save(commit=False)
        report.user_id = request.user.id
        report.save()
        return redirect('dashboard:reports')  


class Report(LoginRequiredMixin, DetailView):
    template_name = 'dashboard/look_a_report.html'
    context_object_name = 'report'

    def get_object(self):
       report_id = self.kwargs['id']
    
       return Reports.objects.get(id=report_id, user_id=self.request.user.id)

class AddRecipient(LoginRequiredMixin, View):
    template = 'dashboard/add_recipient.html'
    def get(self, request):

        form = AddRec(sender_id=self.request.user.id)
        context = {'form': form}
        return render(request, self.template, context)
    
    def post(self, request):
        user_profile = UserProfile.objects.get(user=self.request.user)
        form = AddRec(request.POST, sender_id=self.request.user.id, instance = user_profile)
        if not form.is_valid():
          
            context = {'form': form}
            return render(request, self.template, context)
        
        ##Takes the newly selected ones and add them to the previous queryset
        add = form.save(commit=False)
        previous_receivers = user_profile.receivers.all() #Users queryset
        new_receivers = form.cleaned_data['receivers']
        combined_receivers = previous_receivers | new_receivers

        add.save()
        add.receivers.set(combined_receivers)
        
     
        return redirect('dashboard:reports')  



class Confirmation(LoginRequiredMixin, View):
    def get(self, request):
      template_name= 'dashboard/confirmation.html'
      return render(request, template_name)


class Logout(LogoutView):
    template_name = 'dashboard/logout.html'

