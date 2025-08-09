from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, CreateView, View, DeleteView
from django.http import HttpResponseForbidden


allowed_roles_forms = ['dev']
allowed_roles_management = ['dev']

################## Protected Views ######################

class ProtectedCreate(LoginRequiredMixin, CreateView):

    def dispatch(self, request, *args, **kwargs):
        user_role = request.user.userprofile.role.name
        if user_role not in allowed_roles_forms:
            return HttpResponseForbidden('Forbidden')
        return super().dispatch(request, *args, **kwargs)
    

class ProtectedUpdate(LoginRequiredMixin, UpdateView):
 
    def dispatch(self, request, *args, **kwargs):
        user_role = request.user.userprofile.role.name
        if user_role not in allowed_roles_forms:
            return HttpResponseForbidden('Forbidden')
        return super().dispatch(request, *args, **kwargs)
    

class ProtectedDelete(LoginRequiredMixin, DeleteView):

    def dispatch(self, request, *args, **kwargs):
        user_role = request.user.userprofile.role.name
        if user_role not in allowed_roles_forms:
            return HttpResponseForbidden('Forbidden')
        return super().dispatch(request, *args, **kwargs)

################## CHARTS ###########################


class ChartOwnerUpdateView(LoginRequiredMixin, UpdateView):
       
    def get_queryset(self):

        qs = super(ChartOwnerUpdateView, self).get_queryset()
        if self.request.user.userprofile.role.name in allowed_roles_forms:
            return qs.filter(teams__team_lead__in=[self.request.user.userprofile])
        return qs.none()
    
    
############# PROTECTED VIEWS #################


class ProtectedView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        user_role = request.user.userprofile.role.name
        if user_role not in allowed_roles_management:
            return HttpResponseForbidden('Forbidden')
        return super().dispatch(request, *args, **kwargs)


class ProtectedFormView(LoginRequiredMixin, View):
     
    def dispatch(self, request, *args, **kwargs):
        user_role = request.user.userprofile.role.name
        if user_role not in allowed_roles_forms:
            return HttpResponseForbidden('Forbidden')
        return super().dispatch(request, *args, **kwargs)
    



