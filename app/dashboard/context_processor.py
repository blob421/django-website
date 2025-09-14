from .models import Messages, Alerts


def unread_messages_count(request):
 
    if request.user.is_authenticated:
      

        new_msgs = Messages.objects.filter(
                                    recipient=request.user.userprofile.id, new = True).count()
        
        return {'new': new_msgs}
    return {}