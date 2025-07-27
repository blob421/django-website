from django.forms import ModelForm
from .models import Messages, UserProfile, Task, Team, CompletedTasks
from django.contrib.auth import get_user_model
user_model = get_user_model()
from itertools import chain
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q


class MessageForm(ModelForm):
     max_size_limit = 2 * 1024 * 1024
     picture = forms.FileField(required=False, label="File to upload <= 2MB")
     upload_field_name = 'picture'

     class Meta:
          model = Messages
          fields = ['recipient', 'title', 'content','picture']
          
          
     def __init__(self, *args, sender_id=None):
               
            super().__init__(*args)
            
            if sender_id:
                

               profile = UserProfile.objects.get(user=sender_id)


               combined_qs = UserProfile.objects.filter(
               Q(team=profile.team) | Q(user__in=profile.recipients.all())
               ).distinct()
               #Since recipients are users and not userprofiles
               #Give me all user profiles where there is a user in recipients
               #allowed_users = user_model.objects.filter(many_relation__id=sender_id)
               allowed = combined_qs.exclude(id=sender_id)
                
               # allowed = allowed_users.filter(userprofile__role__name = 'manager')
               self.fields['recipient'].queryset = allowed
            

     def clean(self):
          cleaned_data = super().clean()
          pic = cleaned_data.get('picture')
          if pic is None: return
          if len(pic) > self.max_size_limit:
               self.add_error('picture','Pictures must be less than 2 megabytes')


     def save(self, commit=True):
          instance = super().save(commit=False)
          f = self.cleaned_data.get('picture')

          if isinstance(f, InMemoryUploadedFile):
               bytearr = f.read()
               instance.content_type = f.content_type
               instance.picture = bytearr  # Store raw bytes

          if commit:
               instance.save()

          return instance



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

             #  alloed= User.objects.filter(userprofile__role__name='manager') 
             #  allowed = choices.difference(alloed) # substracts managers
              
                    
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
          picture = forms.FileField(required=False, label="File to upload <= 2MB")
          completion_note = forms.CharField(widget=forms.Textarea)

        

class DenyCompletedTask(ModelForm):
     class Meta:
         model = Task
         fields = ['deny_reason']



   

