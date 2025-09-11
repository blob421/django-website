from django.shortcuts import render
from rest_framework.response import	Response
from rest_framework	import	generics, viewsets
from  .serializers import (TeamMessageSerializer, MessagesSerializer, TaskSerialier, 
                           UserprofileSerializer, TeamSerializer)
from  dashboard.models import Team, Messages, Task, UserProfile, Document
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from dashboard.utility import save_profile_picture, get_stats_data
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from celery.result import AsyncResult
from django.core.cache import cache  


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


def user_response(data, request):
    return Response({
        'user': {
            'id': request.user.id,
            'username': request.user.username,

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
        return user_response(serializer.data, request)
    
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
        queryset = queryset.filter(users__in=[request.user.userprofile]).order_by('due_date')

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