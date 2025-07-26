from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, CreateView

class OwnerCreateView(LoginRequiredMixin, CreateView):
    def get_queryset(self):
       qs = super(OwnerCreateView, self).get_queryset()
       if self.request.user.userprofile.role.name == 'dev':
           return qs
       return qs.none()
    
class OwnerUpdateView(LoginRequiredMixin, UpdateView):
 

    def get_queryset(self):
 
        qs = super(OwnerUpdateView, self).get_queryset()
        if self.request.user.userprofile.role.name == 'dev':
           return qs.filter(team_lead=self.request.user.userprofile)
        return qs.none()
