from django.forms import ModelForm
from .models import Messages, UserProfile, Task,SubTask, ChatMessages, ChartSection, Document
from .models import Goal, Stats, Chart, ChartSection, Report
from django.contrib.auth import get_user_model
user_model = get_user_model()
from django import forms

from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm
from	crispy_forms.layout	import Submit, Button
from	crispy_forms.helper	import FormHelper
from .models import Users
from django_registration.forms import RegistrationForm
from django.contrib.auth.forms import PasswordChangeForm




class ProfilePictureForm(ModelForm):
     class Meta:
          model = Document
          fields = ['file']

class ProfileUpdateForm(ModelForm):
     class Meta:
          model = Users
          fields = ['email', 'street_address', 'phone']
     def __init__(self, *args, **kwargs):
          super(ProfileUpdateForm, self).__init__(*args, **kwargs)
          self.helper = FormHelper()
          self.helper.add_input(Submit('submit', 'Update', css_class='btn btn-primary w-50 mt-4',))
          self.helper.add_input(Button('back', "Back", css_class='btn btn-secondary  w-25 mt-4', 
                                     onclick="window.history.back();"))

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Update', css_class='btn btn-primary w-50 mt-2',))
        self.helper.add_input(Button('back', "Back", css_class='btn btn-secondary  w-25 mt-2', 
                                     onclick="window.history.back();"))
        

class CustomRegistrationForm(RegistrationForm):
    class Meta:
        model = user_model
        fields = ['username', 'email', 'first_name', 'last_name', 'street_address', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Register'))





class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class FileFieldForm(forms.Form):
    file_field = MultipleFileField(required=False)




class LoginForm(AuthenticationForm):
     def __init__(self, *args, **kwargs):
          super(LoginForm, self).__init__(*args, **kwargs)
          self.helper = FormHelper()                               
          self.helper.add_input(Submit('submit','Submit'))           
          self.helper.form_class = 'login_form'
         
       

class SubTaskForm(ModelForm):
     class Meta:
          model = SubTask
          fields = ['name', 'description']
          widgets = {
            'name': forms.TextInput(attrs={'id': 'name_form'}),
            'description': forms.Textarea(attrs={'id': 'description_form'}),
        }



class MessageForm(ModelForm):

     class Meta:
          model = Messages
          fields = ['recipient', 'title', 'content']
          
     
     def __init__(self, *args, sender_id=None):
               
            super().__init__(*args)
            
            if sender_id:
          
               profile = UserProfile.objects.get(user=sender_id)

               combined_qs = UserProfile.objects.filter(
               Q(team=profile.team) | Q(user__in=profile.recipients.all())
               ).distinct()
      
               allowed = combined_qs.exclude(id=sender_id)
               self.fields['recipient'].queryset = allowed
            

class ForwardMessages(ModelForm):
     class Meta:
          model = Messages
          fields = ['recipient']

          
class RecipientForm(ModelForm):
     class Meta:
          model = UserProfile
          fields = ['recipients']
    
     def __init__(self, *args, **kwargs):
          sender_id= kwargs.pop('sender_id', None)
          super().__init__(*args, **kwargs)
        
        
          if sender_id:
               profile = UserProfile.objects.get(user=sender_id)

               existing_contacts = user_model.objects.exclude(many_relation=sender_id)
               logged_in_account = existing_contacts.exclude(pk=sender_id)
               team = logged_in_account.exclude(userprofile__team=profile.team)
      
               self.fields['recipients'].queryset = team
             

class RecipientDelete(ModelForm):
     class Meta:
          model = UserProfile
          fields = ['recipients']
    
     def __init__(self, *args, **kwargs):
          sender_id= kwargs.pop('sender_id', None)
          super().__init__(*args, **kwargs)
        
          if sender_id:
           
               choices = user_model.objects.filter(many_relation=sender_id)
               allowed = choices.exclude(pk=sender_id)
              
                    
               self.fields['recipients'].queryset = allowed
   

class TaskCreate(ModelForm):
     class Meta:
        model = Task
        fields = ['name','description','users','urgent']
        
     def __init__(self, *args, **kwargs):
          team = kwargs.pop('team', None)
          super().__init__(*args, **kwargs)

          if team:     
             self.fields['users'].queryset = team



class SubmitTask(forms.Form):
          completion_note = forms.CharField(widget=forms.Textarea)

class TransferTaskForm(ModelForm):
    class Meta:
          model = Task
          fields=['chart', 'section']
    def __init__(self, *args, **kwargs):
         userprofile = kwargs.pop('user', None)
         super().__init__(*args, **kwargs)

         self.fields['chart'].queryset = Chart.objects.filter(teams__in=[userprofile.team])
         self.fields['section'].queryset = ChartSection.objects.none()
   
    

class DenyCompletedTask(ModelForm):
     class Meta:
         model = Task
         fields = ['deny_reason']



class ChatForm(ModelForm):
     class Meta:
          model = ChatMessages
          fields = ['message']

class AddTaskChart(ModelForm):
     class Meta:
          model= Task
          fields= ['name', 'description', 'users', 'starting_date', 'due_date', 'section']

     def __init__(self, *args, **kwargs):
                  chart = kwargs.pop('chart', None)
                  super().__init__(*args, **kwargs)
                  self.fields['due_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})
                  self.fields['starting_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})
                  self.fields['section'].queryset = ChartSection.objects.filter(chart = chart)

class AddTask(ModelForm):
     class Meta:
          model= Task
          fields= ['name', 'description', 'users', 'due_date', 'urgent']

     def __init__(self, *args, **kwargs):

                  super().__init__(*args, **kwargs)
                  self.fields['due_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})
            
                   
class ReportForm(ModelForm):
      class Meta:
               
          model = Report
          fields = ['content', 'tasks']
          def __init__(self, *args, **kwargs):
               user = kwargs.pop('user')
               super().__init__(*args,**kwargs)
               tasks = Task.objects.filter(users__in= user)
               self.fields['tasks'].queryset = tasks

      
class UpdateTask(ModelForm):
     class Meta:
          model = Task
          fields = ['name', 'description', 'urgent', 'due_date', 'users', 'completed']
     
     def __init__(self, *args, **kwargs):
          profile = kwargs.pop('user')
          super().__init__(*args, **kwargs)

          team = profile.team.name
          team_users = UserProfile.objects.filter(team__name=team)  
          self.fields['users'].queryset = team_users
          self.fields['due_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})


class GoalForm(ModelForm):
     class Meta:
          model = Goal
          fields = ['name', 'type', 'value', 'value_type']

class StatsForm(ModelForm):
     class Meta:
          model = Stats
          fields = ['star_note']

class StatsForm2(ModelForm):
     class Meta:
          model = Stats
          fields = ['star_note']
          widgets = {
           
            'star_note': forms.Textarea(attrs={'id': 'note'}),
        }

class StatusForm(ModelForm):
     class Meta:
          model = UserProfile
          fields = ['status']