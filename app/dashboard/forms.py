from django.forms import ModelForm
from .models import Messages, UserProfile
from django.contrib.auth import get_user_model
user_model = get_user_model()



class MessageForm(ModelForm):
    class Meta:
        model = Messages
        fields = ['recipient', 'title', 'content']
        
    def __init__(self, *args, sender_id=None):
           
            super().__init__(*args)
            
            if sender_id:
                allowed_users = user_model.objects.filter(many_relation__id=sender_id)
                filtered = allowed_users.exclude(id = sender_id)
               # allowed = allowed_users.filter(userprofile__role__name = 'manager')
                self.fields['title'].widget.attrs.update({'autofocus': 'autofocus',
                'required': 'required', 'placeholder': 'Title'})

                self.fields['recipient'].queryset = filtered
                

class RecipientForm(ModelForm):
     class Meta:
          model = UserProfile
          fields = ['recipients']
    
     def __init__(self, *args, **kwargs):
          sender_id= kwargs.pop('sender_id', None)
          super().__init__(*args, **kwargs)
        
        
          if sender_id:
           
               choices = user_model.objects.exclude(many_relation=sender_id)
               allowed = choices.exclude(pk=sender_id)
             #  alloed= User.objects.filter(userprofile__role__name='manager') 
             #  allowed = choices.difference(alloed) # substracts managers
              
                    
               self.fields['recipients'].queryset = allowed
             

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
   

