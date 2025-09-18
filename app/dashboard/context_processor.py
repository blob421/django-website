from .models import Messages, Options


def unread_messages_count(request):
    options=None
    if request.user.is_authenticated:
       if request.user.userprofile.team.team_lead == request.user.userprofile:
            options, _ = Options.objects.get_or_create(user=request.user.userprofile)

       new_msgs = Messages.objects.filter(
                                    recipient=request.user.userprofile.id, new = True).count()
        
       return {'new': new_msgs, 'options':options}
    return {}