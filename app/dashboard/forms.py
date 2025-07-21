from django.forms import ModelForm
from dashboard.models import Reports, Role, UserProfile
from django.contrib.auth.models import User

class MakeForm(ModelForm):
    class Meta:
        model = Reports
        fields = ['recipient', 'title', 'content']
        
    def __init__(self, *args, sender_id=None):
           
            super().__init__(*args)
            
            if sender_id:
                allowed_users = User.objects.filter(many_relation__id=sender_id)
                allowed = allowed_users.filter(userprofile__role__name = 'manager')
                # get me the user rows that has its id is in the relation
                #Filters the users by the relation it has with this id 
                                             #filter by(relation.user.id)
                                             # the id of the user of the relation = id
             
                self.fields['recipient'].queryset = allowed


class AddRec(ModelForm):
     class Meta:
          model = UserProfile
          fields = ['receivers']
    
     def __init__(self, *args, **kwargs):
          sender_id= kwargs.pop('sender_id', None)
          super().__init__(*args, **kwargs)
        
          if sender_id:
           
               choices = User.objects.exclude(many_relation=sender_id)
               allowed = choices.exclude(pk=sender_id)
             #  alloed= User.objects.filter(userprofile__role__name='manager') 
             #  allowed = choices.difference(alloed) # substracts managers
              
                    
               self.fields['receivers'].queryset = allowed
             

   

