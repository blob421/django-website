from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path, include
from	rest_framework.routers import	DefaultRouter


router = DefaultRouter()
from api.views import MessageViewSet, TaskViewSet,TeamViewSet, UserProfileViewSet
router.register("messages", MessageViewSet)
router.register('tasks', TaskViewSet)
router.register('team', TeamViewSet)


urlpatterns = [

     path("jwt/", TokenObtainPairView.as_view(), name="jwt_obtain_pair"),
     path("jwt/refresh/", TokenRefreshView.as_view(), name="jwt_refresh"),
     path('checkAuth/', views.checkAuth.as_view({'get': 'get'}), name='checkAuth'),
     path("home/", views.Homeview.as_view({'get': 'retrieve'}), name="home"),
     path('team/', views.TeamViewSet.as_view({'get':'list'}), name ='team'),
     path('activate/task/<int:pk>', views.ActivateTask.as_view(),name='activate'),
     path('subtasks/<int:pk>/', views.SubtaskViewSet.as_view({
                                     'post':'create', 'patch':'update'}), name="subtasks"),

     path('subtasks/completed/<int:pk>/', views.SubtaskCompleted, name="subtask_completed"),
     path('upload/', views.ImageUploadView.as_view(), name='upload'),
     path('upload/file/<int:pk>', views.FileUploadView.as_view(), name='uploadFiles'),
     path('chat/', views.ChatViewSet.as_view({'get':'get'}), name='chat'),
     path('chat/submit/', views.SaveMessage.as_view({'post':'post'}), name='savemsg'),
     path('loading/<str:celery_id>/<str:photo>/', views.Ready.as_view({'get': 'get'}), 
          name='ready'),
    # path('messages/unread', views.UnreadMessages.as_view(), name='unread_count'),
     path('profile/', views.UserProfileViewSet.as_view({'get':'retrieve'})),
     path('pushtoken/', views.RegisterPush.as_view(), name='registerpush'),
     path("",	include(router.urls)),

     #path('home')
]