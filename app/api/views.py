from django.shortcuts import render
from rest_framework.response import	Response
from rest_framework	import	generics, viewsets
from  .serializers import (TeamMessageSerializer, MessagesSerializer, TaskSerialier, 
                           UserprofileSerializer, TeamSerializer, SubTaskSerializer)
from  dashboard.models import (Team, Messages, Task, UserProfile, Document, ChatMessages, 
                               MessagesCopy, SubTask)
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from dashboard.utility import (save_profile_picture, get_stats_data, copy_message_data, 
                               save_files, notify)
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from celery.result import AsyncResult
from django.core.cache import cache  
from django.contrib.humanize.templatetags.humanize import naturaltime


class ActivateTask(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        task = Task.objects.get(id=pk)
        user = request.user.userprofile
        if user.active_task and user.active_task == task:
            user.active_task = None
        else:
            user.active_task = task
        user.save()
        return JsonResponse({'message':'activated'})

class FileUploadView(APIView):
    parser_classes = [MultiPartParser]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        
    
        file = request.FILES.get('file')
        
        
        task = Task.objects.get(id=pk)
        save_files(self, [file], task)
       
        return JsonResponse({'message': 'saved'})


class ImageUploadView(APIView):
    parser_classes = [MultiPartParser]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        image = request.FILES.get('image')
        user = request.user.userprofile
        content_type = ContentType.objects.get_for_model(UserProfile).id
        Document.objects.create(file=image, content_type_id=content_type, 
                                            owner= user, object_id = user.id )
        
        relative_path = f'userprofile/{user.id}/{image.name}'

        file_path = default_storage.save(relative_path, image)
        celery_task = save_profile_picture.delay(file_path, user.id)
        
        return JsonResponse({'message': celery_task.id})


def contacts_response(data, request):
  
    user = request.user.userprofile
    combined_qs = UserProfile.objects.filter(
               Q(team=user.team) | Q(user__in=user.recipients.all())
               ).distinct()
      
    recipients = combined_qs.exclude(id=user.id)

    return Response({
        'user': {
            'id': request.user.id,
            'username': request.user.username,

        },
        'data': data,
        'contacts': [{'id':recipient.id, 'username':recipient.user.username} for recipient in recipients]

    })


def user_response(data, request):
    active_task = request.user.userprofile.active_task
    if active_task:
        active = active_task.id
    else :
        active = None
    return Response({
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'active_task' :  active

        },
        'data': data
    })

def stats_response(data, request, celery_id, stars, stats):
        stats2= None
        if stats:
            stats2 = stats['stats']
    
        return Response({
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'joined': request.user.date_joined.strftime("%Y-%m-%d %H:%M"),
            'team': request.user.userprofile.team.name,
            'last_login': request.user.last_login.strftime("%Y-%m-%d %H:%M"),
        },
        'data': data,
        'stars':stars,
        'stats':stats,
        'stats2':stats2,
       
        'celery':celery_id

    })


def SubtaskCompleted(request, pk):
    subtask = SubTask.objects.get(id = pk)
    if subtask.completed:
        subtask.completed= False
        
    else:
        subtask.completed = True
    subtask.save()
    return JsonResponse({'message': 'changed'})


class checkAuth(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return JsonResponse({'status': 'ok'})
      


class Homeview(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request):
        user = request.user.userprofile
        queryset = Team.objects.get(id=user.team.id)
    
        serializer = TeamMessageSerializer(queryset)
        return user_response(serializer.data, request)
    

class TeamViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = UserProfile.objects.all()
    serializer_class = TeamSerializer
     
    
    def list(self , request):
        queryset = self.get_queryset()
        queryset =queryset.filter(team=request.user.userprofile.team).order_by('role')

        serializer = self.get_serializer(queryset, many=True)
        return user_response(serializer.data, request)


    
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Messages.objects.all()
    serializer_class = MessagesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        message = self.get_object()  
        serializer = self.get_serializer(message)
        return contacts_response(serializer.data, request)
    
    def create(self, request, *args, **kwargs):
        data = request.data
        if data.get('forwarded') == 'false':
            recipient = UserProfile.objects.get(id=data.get('recipient'))
            new_message = Messages(
                content=data.get('content'),
                title=data.get('title'),
                user=request.user
            )
            new_message.save()
            new_message.recipient.set([recipient])
            copy_message_data(new_message, MessagesCopy)
            notify(new_message)

        else:
            recipient_id = data.get('recipient')
            recipient = UserProfile.objects.get(id=recipient_id)
            message_id = data.get('message_id')
            message = MessagesCopy.objects.get(id=message_id)
            documents = Document.objects.filter(object_id = message.id)

            forwarded_msg = Messages(user=message.user, title=message.title,
                    content=message.content, task= message.task, forwarded=True, 
                    forwarded_by=request.user.userprofile, timestamp=message.timestamp)
            forwarded_msg.save()
            

            forwarded_msg.documents.set(documents.all())
            forwarded_msg.recipient.set([recipient])
            

        return Response({'status': 'Message created'}, 200)
 


    def list(self , request):
        term = request.GET.get('term')
        queryset = self.get_queryset()
        queryset = queryset.filter(recipient=request.user.userprofile)

        if term:
            queryset = queryset.filter(title__icontains=term)

        serializer = self.get_serializer(queryset, many=True)
        return user_response(serializer.data, request)
    
    def get_queryset(self):
       return Messages.objects.filter(recipient=self.request.user.userprofile).order_by('-timestamp')
    
    def get_object(self):
       return get_object_or_404(
        Messages,
        pk=self.kwargs["pk"],
        recipient=self.request.user.userprofile
    )

"""class UnreadMessages(viewsets.ViewSet):
    def get(self,request):
        count  = Messages.objects.filter(recipient=request.user.userprofile, new=True).count()
        return JsonResponse({'count': count})"""

class SubtaskViewSet(viewsets.ModelViewSet):
    permission_classes  = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = SubTaskSerializer
    queryset = SubTask.objects.all()

    def create(self , request, pk):
        data = request.data
        task = Task.objects.get(id=pk)

        SubTask.objects.create(task=task, description=data.get('description'), name= data.get('title'),
                               user=request.user.userprofile)

        return JsonResponse({'message': 'created'})
    
    def update(self, request, pk):
        data = request.data
        subtask = SubTask.objects.get(id=pk)
        subtask.description = data.get('description')
        subtask.name = data.get('name')
        subtask.save()
        return JsonResponse({'message':'updated'})


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes  = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = TaskSerialier
    queryset = Task.objects.all()

    
    def retrieve(self, request, pk=None):
        task = self.get_object()  
        serializer = self.get_serializer(task)
        return user_response(serializer.data, request)
    
    def list(self , request):
        queryset = self.get_queryset()
        queryset = queryset.filter(
            users__in=[request.user.userprofile], completed=False).order_by('due_date')

        serializer = self.get_serializer(queryset, many=True)
        return user_response(serializer.data, request)


class UserProfileViewSet(viewsets.ViewSet):
    permission_classes  = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserprofileSerializer
    queryset = UserProfile.objects.all()

    def retrieve(self, request, *args, **kwargs):
        
        user_profile = request.user.userprofile
        cache_key = f'individual_stats{user_profile.id}'
        stars = []
        all_user_stats = user_profile.stats.all()
        for stat in all_user_stats:
               if stat.star_note:
                    stars.append({'star_note':stat.star_note, 'id':stat.id})

        if cache.has_key(cache_key):
            celery_result= None
            stats = cache.get(cache_key)
        else:
         
            celery_result = get_stats_data.delay(user_profile.id).id 
            stats = None

        serializer = UserprofileSerializer(instance=user_profile)
        return stats_response(serializer.data, request, celery_result,stars, stats)
    

class Ready(viewsets.ViewSet):
    permission_classes  = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request, celery_id, photo):
        data = AsyncResult(celery_id) 
        if data.ready():
            if photo== 'false':
                user = request.user.userprofile
                cache_key = f'individual_stats{user.id}'
                cache.set(cache_key, data.result, 60 * 60 * 24)
    
        return JsonResponse({'ready': data.ready()})
    

class SaveMessage(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        message = request.data['message']
      
        user = request.user.userprofile
        ChatMessages.objects.create(user=user, message=message, team=user.team)
        return JsonResponse({'message':'received'})



class ChatViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
     
        content_type = ContentType.objects.get_for_model(UserProfile)
        team = request.user.userprofile.team
        cache_key = f'chat_team_{team.id}'
        data = cache.get(cache_key)
    
        if data:
            new_msg_list=[]

            last_seen = data[0]['id']
            messages = ChatMessages.objects.filter(id__gt = last_seen).order_by('-created_at')
            for message in messages:
                text  = message.message
                user = message.user.user.username
                id = message.id
                try:
                    pic = Document.objects.filter(object_id = message.user.id, 
                                                    content_type_id=content_type.id).last()   
                    pic_path = pic.file.name
                except:
                    pic_path = 'userprofile/0/avatar.png'
                
                time = message.created_at
               
                timed_message = {'id':id, 'user':user, 'text':text,'time': time, 'pic_path':pic_path}
                new_msg_list.append(timed_message)

            new_msg_list.extend(data)

            cache.set(cache_key, new_msg_list[:50], 60 * 60)
            return JsonResponse(new_msg_list[:50], safe=False)
            
        else:
            data = []
            messages = ChatMessages.objects.filter(team= team).order_by('-created_at')[:50]
            for message in messages:
                text = message.message
                user = message.user.user.username
                id = message.id
                try:
                    pic = Document.objects.filter(object_id = message.user.id, 
                                                content_type_id=content_type.id).last()   
                    pic_path = pic.file.name
                except:
                    pic_path = 'userprofile/0/avatar.png'
            
                time = message.created_at
                
                timed_message = {'id':id,'user':user, 'text':text,'time': time, 'pic_path':pic_path}
                data.append(timed_message)

            cache.set(cache_key, data, 30)
            
            return JsonResponse(data, safe=False)
        
class RegisterPush(APIView):
    def post(self, request):
        token = request.data.get('expoPushToken')
        if not userprofile.push_token:
            userprofile = request.user.userprofile
            userprofile.push_token = token
            userprofile.save()
            return JsonResponse({'message': 'token saved'})

        
